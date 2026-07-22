"""Router agregado v1 (opcional). main.py incluye routers directamente."""

from fastapi import APIRouter
from app.api.v1.endpoints import ingest, chat, graph, integration, notes, brain, progress

api_router = APIRouter()
api_router.include_router(ingest.router, prefix="/ingest", tags=["Ingestion"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(graph.router, prefix="/graph", tags=["Graph"])
api_router.include_router(integration.router, prefix="/integration", tags=["Integration"])
api_router.include_router(notes.router, prefix="/notes", tags=["Human Notes"])
api_router.include_router(brain.router, prefix="/brain", tags=["Platform Brain"])
api_router.include_router(progress.router, prefix="/progress", tags=["Progress"])
