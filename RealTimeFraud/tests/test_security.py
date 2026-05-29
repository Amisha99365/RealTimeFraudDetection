from fastapi.testclient import TestClient

from config.settings import settings
from src.api.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["secure"] is True


def test_score_requires_api_key() -> None:
    response = client.post(
        "/api/v1/transactions/score",
        json={
            "user_id": "user_test",
            "amount": 1000,
            "currency": "INR",
            "channel": "upi",
        },
    )
    assert response.status_code == 401


def test_score_with_valid_api_key() -> None:
    response = client.post(
        "/api/v1/transactions/score",
        json={
            "user_id": "user_test",
            "amount": 1000,
            "currency": "INR",
            "channel": "upi",
            "device_id": "dev1",
            "country_code": "IN",
        },
        headers={"X-API-Key": settings.effective_api_key},
    )
    assert response.status_code == 200
    assert response.json()["decision"] in {"allow", "review", "block"}


def test_public_check_endpoint() -> None:
    response = client.post(
        "/api/v1/transactions/check",
        json={
            "user_id": "user_public",
            "amount": 500,
            "currency": "INR",
            "channel": "upi",
            "device_id": "dev2",
            "country_code": "IN",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["decision"] == "allow"


def test_invalid_user_id_rejected() -> None:
    response = client.post(
        "/api/v1/transactions/check",
        json={
            "user_id": "bad user!",
            "amount": 500,
            "currency": "INR",
            "channel": "upi",
        },
    )
    assert response.status_code == 422


def test_dashboard_stats() -> None:
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_scored" in data
