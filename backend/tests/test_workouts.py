import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

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

def get_auth_headers(email: str, name: str) -> dict:
    client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "securepass", "full_name": name}
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "securepass"}
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_create_workout():
    headers = get_auth_headers("workout_runner@fitvision.ai", "Workout Runner")
    
    workout_payload = {
        "duration_seconds": 120,
        "calories_burned": 45.5,
        "score": 96,
        "difficulty": "Medium",
        "notes": "Test workout details",
        "exercises": [
            {
                "exercise_name": "Pushups",
                "variation": "Standard",
                "total_reps": 20,
                "valid_reps": 18,
                "invalid_reps": 2,
                "average_speed_seconds": 2.4,
                "best_streak": 12
            }
        ]
    }
    
    response = client.post(
        "/api/v1/workouts/",
        json=workout_payload,
        headers=headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["duration_seconds"] == 120
    assert data["calories_burned"] == 45.5
    assert len(data["exercises"]) == 1
    assert data["exercises"][0]["exercise_name"] == "Pushups"
    assert data["exercises"][0]["valid_reps"] == 18

def test_dashboard_stats():
    headers = get_auth_headers("stats_tester@fitvision.ai", "Stats Tester")
    
    # Post a workout first
    client.post(
        "/api/v1/workouts/",
        json={
            "duration_seconds": 300,
            "calories_burned": 150.0,
            "score": 90,
            "difficulty": "Easy",
            "exercises": [
                {
                    "exercise_name": "Squats",
                    "variation": "Standard",
                    "total_reps": 30,
                    "valid_reps": 30,
                    "invalid_reps": 0,
                    "average_speed_seconds": 3.0,
                    "best_streak": 30
                }
            ]
        },
        headers=headers
    )
    
    response = client.get("/api/v1/workouts/stats", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_workouts"] == 1
    assert data["total_calories_burned"] == 150.0
    assert data["streak_count"] == 1
    assert len(data["exercise_distribution"]) == 1
    assert data["exercise_distribution"][0]["exercise_name"] == "Squats"
    assert data["exercise_distribution"][0]["valid_reps"] == 30

def test_leaderboard():
    headers = get_auth_headers("leaderboard_tester@fitvision.ai", "LB Tester")
    
    # Just query standard leaderboard
    response = client.get("/api/v1/workouts/leaderboard", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # Should contain at least current user or seeded testers
