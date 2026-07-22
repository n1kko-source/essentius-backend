import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Depends, Query, HTTPException

from app.api.deps import extract_user_id, optional_user
from app.domain.models import LibraryDocumentUpdate
from app.services.ingestion_service import IngestionService
from app.infrastructure.processors.pdf_processor import PDFProcessor
from app.infrastructure.database.supabase_repo import SupabaseVectorRepo
from app.infrastructure.database.documents_repo import get_documents_repository
from app.infrastructure.providers import get_embedding_provider
from app.core.config import get_settings

router = APIRouter()


def _owned_or_404(doc: Optional[dict], uid: Optional[str]) -> dict:
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    owner = doc.get("user_id")
    if owner and uid and owner != uid:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return doc


@router.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    user=Depends(optional_user),
):
    from app.services.ingestion_service import TooManyChunksError

    safe_name = Path(file.filename or "upload.pdf").name
    fd, temp_path = tempfile.mkstemp(suffix=f"_{safe_name}")
    os.close(fd)

    docs_repo = get_documents_repository()
    uid = extract_user_id(user)
    document = None

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Crear documento primero para ligar embeddings a document_id
        try:
            document = docs_repo.create(title=safe_name, user_id=uid, chunk_count=0)
        except Exception:
            document = {
                "id": None,
                "title": safe_name,
                "user_id": uid,
                "chunk_count": 0,
            }

        processor = PDFProcessor()
        repo = SupabaseVectorRepo()
        embedder = get_embedding_provider()
        service = IngestionService(processor=processor, repo=repo, embedder=embedder)

        try:
            result = service.process_and_store(
                file_path=temp_path,
                source_metadata={
                    "title": safe_name,
                    "document_id": document.get("id") if document else None,
                },
            )
        except TooManyChunksError as exc:
            if document and document.get("id"):
                try:
                    docs_repo.delete(document["id"])
                except Exception:
                    pass
            raise HTTPException(status_code=413, detail=str(exc)) from exc
        except Exception as exc:
            if document and document.get("id"):
                try:
                    docs_repo.delete(document["id"])
                except Exception:
                    pass
            raise HTTPException(
                status_code=502,
                detail=f"Falló el procesamiento / embedding: {exc}",
            ) from exc

        chunk_count = int(result.get("chunks_processed") or 0)
        if document and document.get("id"):
            try:
                updated = docs_repo.set_chunk_count(document["id"], chunk_count)
                if updated:
                    document = updated
                else:
                    document = {**document, "chunk_count": chunk_count}
            except Exception:
                document = {**document, "chunk_count": chunk_count}
        else:
            document = {
                "id": None,
                "title": safe_name,
                "user_id": uid,
                "chunk_count": chunk_count,
            }

        mode = "mock" if get_settings().use_mock_ai else "gemini"
        return {
            "message": f"Archivo procesado (modo {mode})",
            "details": result,
            "document": document,
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/documents")
async def list_documents(
    user_id: Optional[str] = Query(None),
    user=Depends(optional_user),
):
    """Lista documentos de la biblioteca del usuario autenticado (o user_id query)."""
    uid = extract_user_id(user) or user_id
    try:
        return get_documents_repository().list_for_user(uid)
    except Exception:
        return []


@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    user=Depends(optional_user),
):
    uid = extract_user_id(user)
    try:
        doc = get_documents_repository().get_by_id(document_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return _owned_or_404(doc, uid)


@router.patch("/documents/{document_id}")
async def update_document(
    document_id: str,
    payload: LibraryDocumentUpdate,
    user=Depends(optional_user),
):
    uid = extract_user_id(user)
    repo = get_documents_repository()
    try:
        existing = repo.get_by_id(document_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    _owned_or_404(existing, uid)

    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="El título no puede estar vacío")

    try:
        updated = repo.update_title(document_id, title)
    except Exception:
        raise HTTPException(status_code=500, detail="No se pudo actualizar el documento")
    if not updated:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return updated


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    user=Depends(optional_user),
):
    uid = extract_user_id(user)
    repo = get_documents_repository()
    try:
        existing = repo.get_by_id(document_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    _owned_or_404(existing, uid)

    try:
        ok = repo.delete(document_id)
    except Exception:
        raise HTTPException(status_code=500, detail="No se pudo eliminar el documento")
    if not ok:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return {"status": "deleted", "id": document_id, "title": existing.get("title")}
