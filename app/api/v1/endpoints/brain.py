from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import optional_user
from app.domain.models import BiasMirrorRequest
from app.services.bias_mirror_service import BiasMirrorService
from app.services.notes_service import NotesService
from app.infrastructure.database.supabase_notes_repo import notes_repository
from app.infrastructure.database.supabase_repo import SupabaseVectorRepo
from app.infrastructure.providers import get_embedding_provider, get_llm_provider
from app.core.config import get_settings

router = APIRouter()


@router.post("/bias-mirror")
async def bias_mirror(payload: BiasMirrorRequest, _user=Depends(optional_user)):
    title = payload.title
    body = payload.body
    note_id = payload.note_id

    if note_id:
        note = NotesService(repo=notes_repository).get_note(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Nota no encontrada")
        title = title or note.get("title")
        body = body or note.get("body")

    if not title or not body:
        raise HTTPException(
            status_code=400,
            detail="Se requiere note_id o (title + body) para el espejo de sesgo",
        )

    try:
        repo = SupabaseVectorRepo()
    except Exception:
        # Sin Supabase o credenciales: espejo degradado con MockVectorRepo
        from app.infrastructure.mock_providers import MockVectorRepo
        repo = MockVectorRepo()

    embedder = get_embedding_provider()
    llm = None if get_settings().use_mock_ai else get_llm_provider()
    service = BiasMirrorService(embedder=embedder, repo=repo, llm=llm)
    result = service.mirror(
        title=title,
        body=body,
        note_id=note_id,
        include_live=bool(payload.include_live),
    )
    return result.model_dump()
