from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import optional_user
from app.domain.models import HumanNoteCreate, HumanNoteUpdate
from app.services.notes_service import NotesService
from app.infrastructure.database.supabase_notes_repo import notes_repository

router = APIRouter()


def _service() -> NotesService:
    return NotesService(repo=notes_repository)


@router.post("")
async def create_note(payload: HumanNoteCreate, _user=Depends(optional_user)):
    return _service().create_note(payload)


@router.get("")
async def list_notes(
    user_id: Optional[str] = Query(None),
    _user=Depends(optional_user),
):
    return _service().list_notes(user_id=user_id)


@router.get("/{note_id}")
async def get_note(note_id: str, _user=Depends(optional_user)):
    note = _service().get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    return note


@router.patch("/{note_id}")
async def update_note(
    note_id: str,
    payload: HumanNoteUpdate,
    _user=Depends(optional_user),
):
    note = _service().update_note(note_id, payload)
    if not note:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    return note


@router.delete("/{note_id}")
async def delete_note(note_id: str, _user=Depends(optional_user)):
    ok = _service().delete_note(note_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    return {"status": "deleted", "id": note_id}
