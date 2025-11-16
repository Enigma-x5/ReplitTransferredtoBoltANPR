import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_camera_as_admin(client: AsyncClient, admin_token):
    response = await client.post(
        "/api/cameras",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Test Camera",
            "description": "A test camera",
            "lat": 40.7128,
            "lon": -74.0060,
            "heading": 90.0,
            "active": True
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Camera"
    assert data["lat"] == 40.7128
    assert "id" in data


@pytest.mark.asyncio
async def test_create_camera_as_clerk_forbidden(client: AsyncClient, clerk_token):
    response = await client.post(
        "/api/cameras",
        headers={"Authorization": f"Bearer {clerk_token}"},
        json={
            "name": "Test Camera",
            "lat": 40.7128,
            "lon": -74.0060
        }
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_cameras(client: AsyncClient, admin_token):
    await client.post(
        "/api/cameras",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Camera 1", "lat": 40.0, "lon": -74.0}
    )

    response = await client.get(
        "/api/cameras",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Camera 1"
