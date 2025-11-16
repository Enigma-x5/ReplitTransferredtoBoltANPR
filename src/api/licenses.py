from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database import get_db
from src.models.license import License, UsageReport
from src.schemas.license import ActivateLicenseRequest, ActivateLicenseResponse, UsageReportRequest
from src.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/licenses", tags=["Licensing"])


@router.post("/activate", response_model=ActivateLicenseResponse)
async def activate_license(
    request: ActivateLicenseRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(License).where(License.license_key == request.license_key)
    )
    license = result.scalar_one_or_none()

    if not license:
        raise HTTPException(status_code=404, detail="Invalid license key")

    if license.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="License expired")

    if license.node_id and license.node_id != request.node_id:
        raise HTTPException(status_code=400, detail="License already activated on another node")

    if not license.node_id:
        license.node_id = request.node_id
        license.activated_at = datetime.utcnow()
        await db.commit()

    logger.info("License activated", license_key=request.license_key, node_id=request.node_id)

    return ActivateLicenseResponse(
        activated=True,
        expires_at=license.expires_at,
        features=license.features,
    )


@router.post("/usage")
async def report_usage(
    request: UsageReportRequest,
    db: AsyncSession = Depends(get_db),
):
    usage = UsageReport(
        node_id=request.node_id,
        camera_count=request.camera_count,
        reported_at=request.timestamp or datetime.utcnow(),
    )
    db.add(usage)
    await db.commit()

    logger.info("Usage reported", node_id=request.node_id, camera_count=request.camera_count)

    return {"status": "acknowledged"}
