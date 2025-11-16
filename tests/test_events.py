import pytest
from httpx import AsyncClient
from src.models.event import Event, ReviewState
from src.models.camera import Camera
from src.models.upload import Upload, UploadStatus


@pytest.mark.asyncio
async def test_search_events(client: AsyncClient, admin_token, db_session, admin_user):
    camera = Camera(name="Test Cam", lat=40.0, lon=-74.0)
    db_session.add(camera)

    upload = Upload(
        job_id="test-job",
        camera_id=camera.id,
        uploaded_by=admin_user.id,
        filename="test.mp4",
        storage_path="uploads/test.mp4",
        file_size=1000,
        status=UploadStatus.DONE
    )
    db_session.add(upload)

    event = Event(
        upload_id=upload.id,
        camera_id=camera.id,
        plate="ABC123",
        normalized_plate="ABC123",
        confidence=0.95,
        bbox={"x1": 100, "y1": 100, "x2": 200, "y2": 150},
        frame_no=10,
        captured_at="2024-01-01T12:00:00",
        crop_path="crops/test.jpg",
        review_state=ReviewState.UNREVIEWED
    )
    db_session.add(event)
    await db_session.commit()

    response = await client.get(
        "/api/events?plate=ABC",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert "ABC" in data["items"][0]["plate"]
