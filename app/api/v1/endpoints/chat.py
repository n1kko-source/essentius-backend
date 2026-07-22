from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.api.deps import optional_user
from app.services.chat_service import ChatService
from app.infrastructure.database.supabase_repo import SupabaseVectorRepo
from app.infrastructure.database.documents_repo import get_documents_repository
from app.infrastructure.providers import get_embedding_provider, get_llm_provider
from app.core.config import get_settings

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    # Frontend envía el título activo (activeDocument) o un UUID de documents.id
    document_id: Optional[str] = None


def _resolve_doc_filter(document_ref: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """Devuelve (filter_source, filter_document_id) a partir del ref del frontend."""
    if not document_ref:
        return None, None
    ref = document_ref.strip()
    if not ref:
        return None, None

    # UUID-like → document_id; si no, tratar como título/source
    looks_like_id = len(ref) >= 32 and "-" in ref and " " not in ref and "." not in ref
    if looks_like_id:
        try:
            doc = get_documents_repository().get_by_id(ref)
            if doc:
                return doc.get("title"), doc.get("id")
        except Exception:
            pass
        return None, ref

    return ref, None


@router.post("/ask")
async def ask_essentius(request: ChatRequest, _user=Depends(optional_user)):
    try:
        repo = SupabaseVectorRepo()
    except Exception:
        from app.infrastructure.mock_providers import MockVectorRepo

        repo = MockVectorRepo()

    embedder = get_embedding_provider()
    llm = get_llm_provider()

    service = ChatService(embedder=embedder, repo=repo, llm=llm)
    filter_source, filter_document_id = _resolve_doc_filter(request.document_id)

    try:
        response = service.ask_question(
            request.question,
            filter_source=filter_source,
            filter_document_id=filter_document_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Falló el chat / LLM: {exc}",
        ) from exc
    response["mode"] = "mock" if get_settings().use_mock_ai else "gemini"
    response["document_id"] = request.document_id
    response["filter_source"] = filter_source
    return response
