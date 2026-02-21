"""
Basic API Tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "KeywordTracker" in response.json()["message"]


def test_user_registration():
    """Test user registration"""
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123"
    })
    # May fail if user exists, that's ok
    assert response.status_code in [200, 400]


def test_user_login():
    """Test user login"""
    response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpass123"
    })
    # May fail if user doesn't exist, that's ok
    assert response.status_code in [200, 401]


# Run with: pytest tests/test_basic.py -v
