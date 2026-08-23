from fastapi.testclient import TestClient
from sqlalchemy import delete 
from app.app import app
from app.db import Application, async_session_maker
import pytest

client = TestClient(app)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def clean_database(anyio_backend):
    async with async_session_maker() as session:
        await session.execute(delete(Application))
        await session.commit()

    yield

    async with async_session_maker() as session:
        await session.execute(delete(Application))
        await session.commit()

def test_get_applications():
    response = client.get("/applications")

    assert response.status_code == 200
    assert response.json() == []

def test_get_nonexistent_application():
    response = client.get("/applications/999")

    assert response.status_code == 404

def test_create_application():
    response = client.post("/applications", json={
        "company": "Test Company",
        "position": "Test Position",
        "status": "applied"
    })

    data = response.json()

    assert response.status_code == 200
    assert data["company"] == "Test Company"
    assert data["position"] == "Test Position"
    assert data["status"] == "applied"

def test_create_application_with_missing_fields():
    response = client.post("/applications", json={
        "company": "Test Company"
    })

    assert response.status_code == 422

def test_create_application_with_invalid_status():
    response = client.post("/applications", json={
        "company": "Test Company",
        "position": "Test Position",
        "status": "invalid_status"
    })

    assert response.status_code == 422

def test_delete_application():
    app_creation = client.post("/applications", json={
        "company": "Test Company",
        "position": "Test Position",
        "status": "applied"
    })
    app_id = app_creation.json()["id"]
    response = client.delete(f"/applications/{app_id}")
    deleted_response = client.get(f"/applications/{app_id}")

    assert response.status_code == 200
    assert deleted_response.status_code == 404

def test_delete_nonexistent_application():
    response = client.delete("/applications/999")

    assert response.status_code == 404

def test_update_application():
    app_creation = client.post("/applications", json={
        "company": "Test Company",
        "position": "Test Position",
        "status": "applied"
    })

    app_id = app_creation.json()["id"]
    data = {
        "company": "Toching",
        "position": "Student/Teacher",
        "status": "accepted"
    }
    response = client.put(f"/applications/{app_id}", json=data)
    updated_data = response.json()

    check_response = client.get(f"/applications/{app_id}")
    saved_data = check_response.json()

    assert response.status_code == 200
    assert check_response.status_code == 200
    assert data["company"] == updated_data["company"] == saved_data["company"]
    assert data["position"] == updated_data["position"] == saved_data["position"]
    assert data["status"] == updated_data["status"] == saved_data["status"]


def test_update_application_status():
    app_creation = client.post("/applications", json={
            "company": "Test Company",
            "position": "Test Position",
            "status": "applied"
        })
    
    app_id = app_creation.json()["id"]
    data = {
            "status": "accepted"
        }
    response = client.patch(f"/applications/{app_id}", json=data)
    updated_data = response.json()
    
    check_response = client.get(f"/applications/{app_id}")
    saved_data = check_response.json()
    
    assert response.status_code == 200
    assert check_response.status_code == 200
    assert data["status"] == updated_data["status"] == saved_data["status"]
    assert saved_data["company"] == "Test Company"
    assert saved_data["position"] == "Test Position"