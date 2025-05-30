# FilePath: api/tests/test_user_routes.py
# import pytest # No longer need pytest.mark.asyncio
from fastapi.testclient import TestClient # For type hinting
from http import HTTPStatus

# Test user data
student_data = {
    "username": "teststudent@example.com",
    "display_name": "Test Student",
    "role": "student",
    "password": "password123"
}
teacher_data = {
    "username": "testteacher@example.com",
    "display_name": "Test Teacher",
    "role": "teacher",
    "password": "password123"
}

def test_root_redirect(client: TestClient):
    response = client.get("/", follow_redirects=False) # *** ENSURE THIS IS PRESENT ***
    assert response.status_code == HTTPStatus.PERMANENT_REDIRECT # This is 308
    assert "/docs" in response.headers["location"]

def test_signup_user_success(client: TestClient): # db_cleanup is autouse
    response = client.post("/api/v1/users/signup", json=student_data)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == student_data["username"]
    assert data["role"] == student_data["role"]
    assert "id" in data
    assert "password_hash" not in data

def test_signup_user_duplicate_username(client: TestClient):
    client.post("/api/v1/users/signup", json=student_data) # First signup
    response = client.post("/api/v1/users/signup", json=student_data) # Attempt duplicate
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_login_success(client: TestClient):
    client.post("/api/v1/users/signup", json=student_data)
    login_payload = {"username": student_data["username"], "password": student_data["password"]}
    response = client.post("/api/v1/users/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == student_data["username"]
    assert "session" in client.cookies # TestClient manages cookies

def test_login_incorrect_password(client: TestClient):
    client.post("/api/v1/users/signup", json=student_data)
    login_payload = {"username": student_data["username"], "password": "wrongpassword"}
    response = client.post("/api/v1/users/login", json=login_payload)
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_login_user_not_found(client: TestClient):
    login_payload = {"username": "nouser@example.com", "password": "password123"}
    response = client.post("/api/v1/users/login", json=login_payload)
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_get_me_success(authenticated_student_data_and_client: tuple[TestClient, dict]): # Already updated this one
    client, student_details = authenticated_student_data_and_client
    response = client.get("/api/v1/users/me")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["username"] == student_details["username"]
    assert data["role"] == student_details["role"]
    assert data["id"] == student_details["id"]

def test_get_me_unauthenticated(client: TestClient):
    response = client.get("/api/v1/users/me")
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert "Not authenticated" in response.json()["detail"]

def test_logout_success(authenticated_student_data_and_client: tuple[TestClient, dict]): # MODIFIED: Use new fixture name
    client, _ = authenticated_student_data_and_client # Unpack, we only need client here
    
    me_response = client.get("/api/v1/users/me")
    assert me_response.status_code == HTTPStatus.OK

    response = client.post("/api/v1/users/logout")
    assert response.status_code == HTTPStatus.OK # Logout returns 200
    assert response.json()["message"] == "Successfully logged out"
    
    me_response_after_logout = client.get("/api/v1/users/me")
    assert me_response_after_logout.status_code == HTTPStatus.UNAUTHORIZED
