# FilePath: api/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from typing import Generator
import asyncio
import uuid

from app.main import app
from app.core.db import MONGO_DB, close_mongo_connection, get_user_collection, get_course_collection, get_question_collection, get_qca_collection
from app.core.settings import DATABASE_NAME, MONGO_DATABASE_URL

@pytest.fixture(scope="session", autouse=True)
def database_warning_and_final_cleanup():
    # This fixture primarily issues a warning and attempts a final cleanup.
    # The main DB connection/disconnection should be handled by TestClient's app lifespan.
    if "test" not in MONGO_DATABASE_URL.lower() and "test" not in DATABASE_NAME.lower():
        print(f"\nCRITICAL WARNING: Running tests against a non-test database ({DATABASE_NAME} at {MONGO_DATABASE_URL}).")
    
    yield # Test session runs

    # Attempt a final graceful shutdown of the MongoDB client if it exists and has a loop
    # print("--- database_warning_and_final_cleanup: Attempting final MongoDB client close ---")
    if MONGO_DB.client and hasattr(MONGO_DB.client, '_loop') and MONGO_DB.client._loop:
        client_loop = MONGO_DB.client._loop
        if not client_loop.is_closed():
            # print(f"--- Running close_mongo_connection on loop {id(client_loop)} ---")
            future = asyncio.run_coroutine_threadsafe(close_mongo_connection(), client_loop)
            try:
                future.result(timeout=5) # Wait for close_mongo_connection to finish
                # print("--- close_mongo_connection completed ---")
            except Exception as e:
                print(f"--- Error during final close_mongo_connection: {e} ---")
            
            # Do not close the loop here if it's managed by anyio/TestClient for the app
            # If this loop was created *only* for this fixture, then close it.
            # This part is tricky. Relying on TestClient to manage the app's loop is best.
    # print("--- database_warning_and_final_cleanup: Finished ---")


@pytest.fixture(scope="session")
def client(database_warning_and_final_cleanup) -> Generator[TestClient, None, None]:
    # print("--- client fixture: Creating TestClient ---")
    with TestClient(app) as c: # TestClient manages app lifespan (DB connect/disconnect)
        if MONGO_DB.db is None or MONGO_DB.client is None:
            pytest.fail("DB or DB Client not initialized by TestClient app lifespan.")
        if not hasattr(MONGO_DB.client, '_loop') or MONGO_DB.client._loop is None:
            pytest.fail("MONGO_DB.client not bound to an event loop after TestClient app lifespan.")
        # print(f"--- client fixture: TestClient active, MONGO_DB.client loop: {id(MONGO_DB.client._loop)} ---")
        yield c
    # print("--- client fixture: TestClient context exited (app lifespan shutdown called) ---")



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
    assert login_response.status_code == 200, f"Student login failed within fixture: {login_response.text}"
    # Add an explicit check for the cookie here too
    assert "session" in client.cookies, "Session cookie not found in client after login within student fixture"
        
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

    assert login_response.status_code == 200, f"Teacher login failed within fixture: {login_response.text}"
    # Add an explicit check for the cookie here too
    assert "session" in client.cookies, "Session cookie not found in client after login within teacher fixture"
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
            
            if user_coll is not None: await user_coll.delete_many({})
            if course_coll is not None: await course_coll.delete_many({})
            if question_coll is not None: await question_coll.delete_many({})
            if qca_coll is not None: await qca_coll.delete_many({})
        
        # ... (rest of the loop running logic)
        if db_client_loop.is_running():
            future = asyncio.run_coroutine_threadsafe(clean_collections_async(), db_client_loop)
            try:
                future.result(timeout=10)
            except Exception as e:
                print(f"Error during db_cleanup: {e}") 
        else:
            try:
               asyncio.set_event_loop(db_client_loop)
               db_client_loop.run_until_complete(clean_collections_async())
            except Exception as e:
               print(f"Error during db_cleanup (loop not running case): {e}")
    elif MONGO_DB.db is None:
        print("Warning: auto_db_cleanup: MONGO_DB.db is None. App may not have started correctly. Skipping cleanup.")
    yield
