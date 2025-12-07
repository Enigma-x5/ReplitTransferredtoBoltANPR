from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.auth import get_current_user
from src.config import settings
from src.models.user import User

router = APIRouter(prefix="/maps", tags=["Maps"])


class MapConfig(BaseModel):
    api_key: str
    style_url: str


@router.get("/config", response_model=MapConfig)
async def get_map_config(current_user: User = Depends(get_current_user)):
    return MapConfig(
        api_key=settings.OLA_MAPS_API_KEY,
        style_url="https://api.olamaps.io/tiles/vector/v1/styles/default-light-standard/style.json"
    )
