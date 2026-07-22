import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

# Use an in-memory SQLite database for unit tests
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables in test database
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override app database dependency
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_signup():
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": "tester@fitvision.ai", "password": "securepassword", "full_name": "Test Runner"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "tester@fitvision.ai"
    assert data["full_name"] == "Test Runner"
    assert "id" in data

def test_signup_duplicate_email():
    # Setup duplicate signup
    client.post(
        "/api/v1/auth/signup",
        json={"email": "duplicate@fitvision.ai", "password": "securepassword", "full_name": "User 1"}
    )
    # Trigger second signup
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": "duplicate@fitvision.ai", "password": "anotherpass", "full_name": "User 2"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "A user with this email address already exists in the system."

def test_login():
    # Setup User
    client.post(
        "/api/v1/auth/signup",
        json={"email": "login_test@fitvision.ai", "password": "mypassword", "full_name": "Login Tester"}
    )
    
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login_test@fitvision.ai", "password": "mypassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_incorrect_password():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login_test@fitvision.ai", "password": "wrong_password"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect email or password"

def test_read_me():
    # Signup & Login
    client.post(
        "/api/v1/auth/signup",
        json={"email": "me_test@fitvision.ai", "password": "securepassword", "full_name": "Me Tester"}
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "me_test@fitvision.ai", "password": "securepassword"}
    )
    token = login_res.json()["access_token"]

    # Request /me
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me_test@fitvision.ai"
    assert data["full_name"] == "Me Tester"
