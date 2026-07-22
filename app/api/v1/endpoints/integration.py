from fastapi import APIRouter, Body, Depends

from app.api.deps import optional_user
from app.services.sync_service import SyncRoadmapService
from app.infrastructure.providers import get_calendar_provider

router = APIRouter()


@router.post("/sync-notion")
async def sync_roadmap_to_notion(
    roadmap_data: dict = Body(...),
    _user=Depends(optional_user),
):
    notion_provider = get_calendar_provider()
    service = SyncRoadmapService(calendar=notion_provider)
    return service.sync_to_calendar(roadmap_data)
