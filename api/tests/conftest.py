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
    get_survey_attempt_collection, # ADD THIS
    get_student_answer_collection  # ADD THIS
)
from app.core.settings import DATABASE_NAME, MONGO_DATABASE_URL

@pytest.fixture(scope="session", autouse=True)
def database_warning_and_final_cleanup():
    if "test" not in MONGO_DATABASE_URL.lower() and "test" not in DATABASE_NAME.lower():
        print(f"\nCRITICAL WARNING: Running tests against a non-test database ({DATABASE_NAME} at {MONGO_DATABASE_URL}).")
    yield
    if MONGO_DB.client and hasattr(MONGO_DB.client, '_loop') and MONGO_DB.client._loop:
        client_loop = MONGO_DB.client._loop
        if not client_loop.is_closed():
            future = asyncio.run_coroutine_threadsafe(close_mongo_connection(), client_loop)
            try:
                future.result(timeout=5)
            except Exception as e:
                print(f"--- Error during final close_mongo_connection: {e} ---")

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
def auto_db_cleanup(client: TestClient): 
    if MONGO_DB.db is not None and MONGO_DB.client is not None and hasattr(MONGO_DB.client, '_loop'):
        db_client_loop = MONGO_DB.client._loop
        if db_client_loop is None or db_client_loop.is_closed():
            print("Warning: auto_db_cleanup: MONGO_DB.client's event loop is None or closed. Skipping cleanup.")
            yield
            return

        async def clean_collections_async():
            user_coll = get_user_collection()
            course_coll = get_course_collection()
            question_coll = get_question_collection()
            qca_coll = get_qca_collection()
            survey_coll = get_survey_collection() 
            attempt_coll = get_survey_attempt_collection() # ADD THIS
            answer_coll = get_student_answer_collection() # ADD THIS
            
            if user_coll is not None: await user_coll.delete_many({})
            if course_coll is not None: await course_coll.delete_many({})
            if question_coll is not None: await question_coll.delete_many({})
            if qca_coll is not None: await qca_coll.delete_many({})
            if survey_coll is not None: await survey_coll.delete_many({})
            if attempt_coll is not None: await attempt_coll.delete_many({}) # ADD THIS
            if answer_coll is not None: await answer_coll.delete_many({}) # ADD THIS
        
        if db_client_loop.is_running():
            future = asyncio.run_coroutine_threadsafe(clean_collections_async(), db_client_loop)
            try:
                future.result(timeout=10)
            except Exception as e:
                print(f"Error during db_cleanup (threadsafe): {e}") 
        else:
            try:
                asyncio.set_event_loop(db_client_loop) 
                db_client_loop.run_until_complete(clean_collections_async())
            except RuntimeError as e: 
                print(f"Error setting/running event loop in db_cleanup (loop not running case - RuntimeError): {e}")
            except Exception as e:
               print(f"General error during db_cleanup (loop not running case): {e}")
    elif MONGO_DB.db is None:
        print("Warning: auto_db_cleanup: MONGO_DB.db is None. App may not have started correctly. Skipping cleanup.")
    yield
