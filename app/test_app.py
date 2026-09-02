from fastapi.testclient import TestClient
from sqlalchemy import delete
from app.app import app
from app.db import Application, User, async_session_maker
import pytest

client = TestClient(app)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def clean_database(anyio_backend):
    async with async_session_maker() as session:
        await session.execute(delete(Application))
        await session.execute(delete(User))
        await session.commit()

    yield

    async with async_session_maker() as session:
        await session.execute(delete(Application))
        await session.execute(delete(User))
        await session.commit()


@pytest.fixture
def auth_headers():

    client.post("/users", json={
        "email": "duck@sisyphos.com",
        "password": "duck test"
    })

    login_response = client.post("/user", data={
        "username": "duck@sisyphos.com",
        "password": "duck test"
    })

    token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }

@pytest.fixture
def auth_headers2():
    client.post("/users", json={
        "email": "anotherduck@sisyphos.com",
        "password": "another duck test"
    })

    login_response = client.post("/user", data={
        "username": "anotherduck@sisyphos.com",
        "password": "another duck test"
    })

    token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


def test_get_applications(auth_headers):
    response = client.get("/applications", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_get_nonexistent_application(auth_headers):
    response = client.get(
        "/applications/999",
        headers=auth_headers
    )

    assert response.status_code == 404


def test_create_application(auth_headers):
    response = client.post(
        "/applications",
        json={
            "company": "Test Company",
            "position": "Test Position",
            "status": "applied"
        },
        headers=auth_headers
    )

    data = response.json()

    assert response.status_code == 200
    assert data["company"] == "Test Company"
    assert data["position"] == "Test Position"
    assert data["status"] == "applied"


def test_create_application_with_missing_fields(auth_headers):
    response = client.post(
        "/applications",
        json={
            "company": "Test Company"
        },
        headers=auth_headers
    )

    assert response.status_code == 422


def test_create_application_with_invalid_status(auth_headers):
    response = client.post(
        "/applications",
        json={
            "company": "Test Company",
            "position": "Test Position",
            "status": "invalid_status"
        },
        headers=auth_headers
    )

    assert response.status_code == 422


def test_delete_application(auth_headers):
    app_creation = client.post(
        "/applications",
        json={
            "company": "Test Company",
            "position": "Test Position",
            "status": "applied"
        },
        headers=auth_headers
    )

    app_id = app_creation.json()["id"]

    response = client.delete(
        f"/applications/{app_id}",
        headers=auth_headers
    )

    deleted_response = client.get(
        f"/applications/{app_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    assert deleted_response.status_code == 404


def test_delete_nonexistent_application(auth_headers):
    response = client.delete(
        "/applications/999",
        headers=auth_headers
    )

    assert response.status_code == 404


def test_update_application(auth_headers):
    app_creation = client.post(
        "/applications",
        json={
            "company": "Test Company",
            "position": "Test Position",
            "status": "applied"
        },
        headers=auth_headers
    )

    app_id = app_creation.json()["id"]

    data = {
        "company": "Toching",
        "position": "Student/Teacher",
        "status": "accepted"
    }

    response = client.put(
        f"/applications/{app_id}",
        json=data,
        headers=auth_headers
    )

    updated_data = response.json()

    check_response = client.get(
        f"/applications/{app_id}",
        headers=auth_headers
    )

    saved_data = check_response.json()

    assert response.status_code == 200
    assert check_response.status_code == 200
    assert data["company"] == updated_data["company"] == saved_data["company"]
    assert data["position"] == updated_data["position"] == saved_data["position"]
    assert data["status"] == updated_data["status"] == saved_data["status"]


def test_update_application_status(auth_headers):
    app_creation = client.post(
        "/applications",
        json={
            "company": "Test Company",
            "position": "Test Position",
            "status": "applied"
        },
        headers=auth_headers
    )

    app_id = app_creation.json()["id"]

    data = {
        "status": "accepted"
    }

    response = client.patch(
        f"/applications/{app_id}",
        json=data,
        headers=auth_headers
    )

    updated_data = response.json()

    check_response = client.get(
        f"/applications/{app_id}",
        headers=auth_headers
    )

    saved_data = check_response.json()

    assert response.status_code == 200
    assert check_response.status_code == 200
    assert data["status"] == updated_data["status"] == saved_data["status"]
    assert saved_data["company"] == "Test Company"
    assert saved_data["position"] == "Test Position"


def test_user_cannot_get_another_user_application(auth_headers, auth_headers2):
    app_creation = client.post(
        "/applications",
        json = {
            "company": "another duck's company",
            "position": "whatever",
            "status": "seeking to apply"
        },
        headers=auth_headers
    )
    app_id = app_creation.json()["id"]

    check_response = client.get(
        f"/applications/{app_id}",
        headers=auth_headers2
        )

    assert check_response.status_code == 404
