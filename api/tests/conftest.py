import pytest
from fastapi.testclient import TestClient
from typing import Generator
import asyncio
import uuid

from app.main import app
from app.core.db import (
    MONGO_DB, close_mongo_connection, 
    get_user_collection, get_course_collection, 
    get_question_collection, get_qca_collection,
    get_survey_collection, 
    get_survey_attempt_collection,
    get_student_answer_collection
)
from app.core.settings import DATABASE_NAME, MONGO_DATABASE_URL

@pytest.fixture(scope="session", autouse=True)
def database_warning_and_final_cleanup():
    if "test" not in MONGO_DATABASE_URL.lower() and "test" not in DATABASE_NAME.lower():
        print(f"\nCRITICAL WARNING: Running tests against a non-test database ({DATABASE_NAME} at {MONGO_DATABASE_URL}).")
    yield
    # Ensure MONGO_DB.client and its loop exist and the loop is not closed before trying to close connection
    if MONGO_DB.client and hasattr(MONGO_DB.client, '_loop') and MONGO_DB.client._loop and not MONGO_DB.client._loop.is_closed():
        client_loop = MONGO_DB.client._loop
        # Check if the loop is running, as run_coroutine_threadsafe needs a running loop
        if client_loop.is_running():
            future = asyncio.run_coroutine_threadsafe(close_mongo_connection(), client_loop)
            try:
                future.result(timeout=5)
            except Exception as e:
                print(f"--- Error during final close_mongo_connection: {e} ---")
        else:
            # If the loop is not running, try running close_mongo_connection directly (less ideal but a fallback)
            try:
                client_loop.run_until_complete(close_mongo_connection())
            except Exception as e:
                 print(f"--- Error during final close_mongo_connection (loop not running): {e} ---")
    elif MONGO_DB.client:
        print("--- Warning: MONGO_DB.client exists but its event loop is not available or closed. Cannot run async close_mongo_connection. ---")


@pytest.fixture(scope="session")
def client(database_warning_and_final_cleanup) -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        if MONGO_DB.db is None or MONGO_DB.client is None:
            pytest.fail("DB or DB Client not initialized by TestClient app lifespan.")
        if not hasattr(MONGO_DB.client, '_loop') or MONGO_DB.client._loop is None:
            pytest.fail("MONGO_DB.client not bound to an event loop after TestClient app lifespan.")
        yield c

@pytest.fixture(scope="function")
def authenticated_student_data_and_client(client: TestClient) -> tuple[TestClient, dict]:
    unique_suffix = uuid.uuid4().hex[:8]
    user_data = {
        "username": f"student_{unique_suffix}@example.com",
        "display_name": f"Test Student {unique_suffix}",
        "role": "student",
        "password": "testpassword"
    }
    signup_response = client.post("/api/v1/users/signup", json=user_data)
    assert signup_response.status_code == 201, f"Student signup failed: {signup_response.text}"
    created_user_details = signup_response.json()
    login_data = {"username": user_data["username"], "password": user_data["password"]}
    login_response = client.post("/api/v1/users/login", json=login_data)
    assert login_response.status_code == 200, f"Student login failed: {login_response.text}"
    assert "session" in client.cookies, "Session cookie not found after student login in fixture"
    return client, created_user_details

@pytest.fixture(scope="function")
def authenticated_teacher_data_and_client(client: TestClient) -> tuple[TestClient, dict]:
    unique_suffix = uuid.uuid4().hex[:8]
    user_data = {
        "username": f"teacher_{unique_suffix}@example.com",
        "display_name": f"Test Teacher {unique_suffix}",
        "role": "teacher",
        "password": "testpassword"
    }
    signup_response = client.post("/api/v1/users/signup", json=user_data)
    assert signup_response.status_code == 201, f"Teacher signup failed: {signup_response.text}"
    created_user_details = signup_response.json()
    login_data = {"username": user_data["username"], "password": user_data["password"]}
    login_response = client.post("/api/v1/users/login", json=login_data)
    assert login_response.status_code == 200, f"Teacher login failed: {login_response.text}"
    assert "session" in client.cookies, "Session cookie not found after teacher login in fixture"
    return client, created_user_details

@pytest.fixture(scope="function", autouse=True)
def auto_db_cleanup(client: TestClient): # client fixture implicitly handles app lifespan and db connection
    # This fixture will run after each test function due to autouse=True
    # It relies on MONGO_DB.db being set up by the TestClient's app lifespan
    
    # Yield to let the test run
    yield

    # Cleanup after the test
    if MONGO_DB.db is not None and MONGO_DB.client is not None and hasattr(MONGO_DB.client, '_loop'):
        db_client_loop = MONGO_DB.client._loop
        if db_client_loop is None or db_client_loop.is_closed():
            # print("Warning: auto_db_cleanup: MONGO_DB.client's event loop is None or closed post-test. Skipping cleanup.")
            return

        async def clean_collections_async():
            # print(f"--- conftest (auto_db_cleanup): Cleaning collections for test ---")
            collections_to_clean_funcs = [
                get_user_collection, get_course_collection,
                get_question_collection, get_qca_collection,
                get_survey_collection, get_survey_attempt_collection,
                get_student_answer_collection
            ]
            for coll_func in collections_to_clean_funcs:
                try:
                    coll = coll_func()
                    if coll is not None:
                        await coll.delete_many({})
                except Exception as e:
                    print(f"--- conftest: Error cleaning collection via {coll_func.__name__} in auto_db_cleanup: {e} ---")
            # print(f"--- conftest (auto_db_cleanup): Collections cleaned ---")
        
        if db_client_loop.is_running():
            future = asyncio.run_coroutine_threadsafe(clean_collections_async(), db_client_loop)
            try:
                future.result(timeout=10)
            except Exception as e:
                print(f"Error during auto_db_cleanup (threadsafe): {e}") 
        else:
            # This case might be problematic if the loop from TestClient isn't easily reused.
            # However, for cleanup, a new temporary loop might be acceptable if the main one is truly gone.
            # print("Warning: auto_db_cleanup: MONGO_DB.client's event loop is not running. Attempting cleanup with new loop.")
            try:
                asyncio.run(clean_collections_async()) # Fallback to asyncio.run
            except Exception as e:
               print(f"General error during auto_db_cleanup (loop not running case, using asyncio.run): {e}")
    elif MONGO_DB.db is None:
        print("Warning: auto_db_cleanup: MONGO_DB.db is None post-test. App may not have initialized DB correctly. Skipping cleanup.")
