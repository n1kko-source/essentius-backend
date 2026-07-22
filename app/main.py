from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.v1.endpoints import ingest, chat, graph, integration, notes, brain, progress

settings = get_settings()

app = FastAPI(title=settings.app_name, version=settings.app_version)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
# Localhost / LAN (dev) + Vercel (prod / preview)
_CORS_ORIGIN_RE = (
    r"https?://("
    r"localhost|"
    r"127\.0\.0\.1|"
    r"192\.168\.\d{1,3}\.\d{1,3}|"
    r"([a-z0-9-]+\.)+vercel\.app"
    r")(:\d+)?"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["http://localhost:3000"],
    allow_origin_regex=_CORS_ORIGIN_RE,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
    # Chrome: origen 192.168.* → API en 127.0.0.1 (Private Network Access)
    allow_private_network=True,
)

app.include_router(ingest.router, prefix="/api/v1/ingest", tags=["Ingestion"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(graph.router, prefix="/api/v1/graph", tags=["Graph"])
app.include_router(integration.router, prefix="/api/v1/integration", tags=["Integration"])
app.include_router(notes.router, prefix="/api/v1/notes", tags=["Human Notes"])
app.include_router(brain.router, prefix="/api/v1/brain", tags=["Platform Brain"])
app.include_router(progress.router, prefix="/api/v1/progress", tags=["Progress"])


@app.get("/")
async def root():
    return {
        "status": "Essentius Backend Online",
        "use_mock_ai": settings.use_mock_ai,
        "auth_required": settings.auth_required,
    }
