from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import extract_user_id, optional_user
from app.domain.gamification import XP_REWARDS
from app.services.progress_service import get_progress_service

router = APIRouter()

EventType = Literal[
    "note_create",
    "note_link",
    "pdf_upload",
    "chat_message",
    "bias_mirror",
    "world_search",
]


class AwardRequest(BaseModel):
    event_type: EventType = Field(..., description="Learning action that grants XP")


def _require_uid(user) -> str:
    uid = extract_user_id(user)
    if not uid:
        raise HTTPException(
            status_code=401,
            detail="Se requiere sesión para el progreso (Bearer JWT)",
        )
    return uid


@router.get("/me")
async def progress_me(user=Depends(optional_user)):
    uid = _require_uid(user)
    return get_progress_service().get_me(uid)


@router.post("/award")
async def progress_award(payload: AwardRequest, user=Depends(optional_user)):
    if payload.event_type not in XP_REWARDS:
        raise HTTPException(status_code=400, detail="event_type inválido")
    uid = _require_uid(user)
    return get_progress_service().award(uid, payload.event_type)


@router.post("/prestige")
async def progress_prestige(user=Depends(optional_user)):
    uid = _require_uid(user)
    return get_progress_service().prestige(uid)
