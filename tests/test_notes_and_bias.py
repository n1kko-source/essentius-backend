import os

# Force in-memory notes for unit tests before app imports resolve the proxy
os.environ.setdefault("NOTES_BACKEND", "memory")
os.environ.setdefault("USE_MOCK_AI", "true")

from fastapi.testclient import TestClient
from app.main import app
from app.infrastructure.database.notes_repo import InMemoryNotesRepository
from app.infrastructure.database.supabase_notes_repo import notes_repository

client = TestClient(app)


def setup_function():
    # Reset proxy to a fresh in-memory store
    mem = InMemoryNotesRepository()
    InMemoryNotesRepository._store.clear()
    notes_repository._inner = mem


def test_root_exposes_flags():
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "Essentius Backend Online"
    assert "use_mock_ai" in body


def test_notes_crud():
    create = client.post(
        "/api/v1/notes",
        json={
            "title": "Mi comprensión de vectores",
            "body": "Los embeddings representan significado en un espacio denso.",
            "topic": "RAG",
            "linked_note_ids": [],
        },
    )
    assert create.status_code == 200
    note = create.json()
    assert note["human_authored"] is True
    assert note.get("linked_note_ids") == []
    note_id = note["id"]

    listed = client.get("/api/v1/notes")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    got = client.get(f"/api/v1/notes/{note_id}")
    assert got.status_code == 200
    assert "embeddings" in got.json()["body"]

    other = client.post(
        "/api/v1/notes",
        json={
            "title": "Segunda nota",
            "body": "Conexión entre ideas humanas.",
        },
    )
    other_id = other.json()["id"]

    updated = client.patch(
        f"/api/v1/notes/{note_id}",
        json={"title": "Vectores actualizado", "linked_note_ids": [other_id]},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Vectores actualizado"
    assert other_id in updated.json()["linked_note_ids"]

    deleted = client.delete(f"/api/v1/notes/{note_id}")
    assert deleted.status_code == 200
    assert client.get(f"/api/v1/notes/{note_id}").status_code == 404


def test_bias_mirror_with_inline_text():
    r = client.post(
        "/api/v1/brain/bias-mirror",
        json={
            "title": "Prueba de sesgo",
            "body": "Creo que el aprendizaje solo funciona con repetición mecánica.",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert "alignment_score" in body
    assert "confirmation_bias_risk" in body
    assert "summary" in body
    assert body.get("sources") == "library"


def test_bias_mirror_include_live():
    r = client.post(
        "/api/v1/brain/bias-mirror",
        json={
            "title": "Espaciado",
            "body": "Creo que estudiar un poco cada día es mejor que maratones.",
            "include_live": True,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["sources"] in ("live", "hybrid")
    assert len(body.get("external_evidence") or []) > 0
    assert len(body.get("citations") or []) > 0


def test_chat_accepts_document_id():
    r = client.post(
        "/api/v1/chat/ask",
        json={"question": "¿Qué es un embedding?", "document_id": "demo.pdf"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "answer" in body
    assert body.get("document_id") == "demo.pdf"
