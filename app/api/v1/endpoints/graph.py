import os
import tempfile
import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Depends

from app.api.deps import optional_user
from app.services.graph_service import GraphService
from app.infrastructure.processors.pdf_processor import PDFProcessor
from app.infrastructure.providers import get_graph_generator
from app.core.config import get_settings

router = APIRouter()


@router.post("/generate")
async def generate_graph(
    file: UploadFile = File(...),
    _user=Depends(optional_user),
):
    safe_name = Path(file.filename or "upload.pdf").name
    fd, temp_path = tempfile.mkstemp(suffix=f"_{safe_name}")
    os.close(fd)

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        processor = PDFProcessor()
        generator = get_graph_generator()
        service = GraphService(processor, generator)
        roadmap = service.create_graph_from_file(temp_path)
        roadmap["mode"] = "mock" if get_settings().use_mock_ai else "gemini"
        return roadmap
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
