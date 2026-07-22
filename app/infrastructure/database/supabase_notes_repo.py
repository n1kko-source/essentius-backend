"""Supabase-backed human_notes + factory with in-memory fallback."""

from typing import List, Optional
from datetime import datetime, timezone

from app.domain.interfaces import INotesRepository
from app.infrastructure.database.notes_repo import InMemoryNotesRepository


class SupabaseNotesRepository(INotesRepository):
    def __init__(self):
        from app.infrastructure.database.supabase_client import get_supabase

        self._client = get_supabase()
        self._table = "human_notes"

    def create(self, note: dict) -> dict:
        row = self._to_row(note)
        res = self._client.table(self._table).insert(row).execute()
        return self._from_row(res.data[0])

    def get(self, note_id: str) -> Optional[dict]:
        res = (
            self._client.table(self._table)
            .select("*")
            .eq("id", note_id)
            .limit(1)
            .execute()
        )
        if not res.data:
            return None
        return self._from_row(res.data[0])

    def list_all(self, user_id: Optional[str] = None) -> List[dict]:
        q = self._client.table(self._table).select("*").order("updated_at", desc=True)
        if user_id:
            q = q.eq("user_id", user_id)
        res = q.execute()
        return [self._from_row(r) for r in (res.data or [])]

    def update(self, note_id: str, fields: dict) -> Optional[dict]:
        payload = {**fields, "updated_at": datetime.now(timezone.utc).isoformat()}
        if "linked_note_ids" in payload and payload["linked_note_ids"] is None:
            del payload["linked_note_ids"]
        res = (
            self._client.table(self._table)
            .update(payload)
            .eq("id", note_id)
            .execute()
        )
        if not res.data:
            return None
        return self._from_row(res.data[0])

    def delete(self, note_id: str) -> bool:
        res = self._client.table(self._table).delete().eq("id", note_id).execute()
        return bool(res.data)

    @staticmethod
    def _to_row(note: dict) -> dict:
        return {
            "id": note.get("id"),
            "title": note["title"],
            "body": note["body"],
            "topic": note.get("topic"),
            "user_id": note.get("user_id"),
            "linked_note_ids": note.get("linked_note_ids") or [],
            "human_authored": note.get("human_authored", True),
            "created_at": note.get("created_at"),
            "updated_at": note.get("updated_at"),
        }

    @staticmethod
    def _from_row(row: dict) -> dict:
        return {
            "id": str(row["id"]),
            "title": row["title"],
            "body": row["body"],
            "topic": row.get("topic"),
            "user_id": str(row["user_id"]) if row.get("user_id") else None,
            "linked_note_ids": list(row.get("linked_note_ids") or []),
            "human_authored": bool(row.get("human_authored", True)),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
        }


def get_notes_repository() -> INotesRepository:
    from app.core.config import get_settings

    settings = get_settings()
    backend = (settings.notes_backend or "auto").lower()
    if backend == "memory":
        return InMemoryNotesRepository()
    if backend == "supabase" or backend == "auto":
        if not settings.supabase_url or not settings.supabase_key:
            return InMemoryNotesRepository()
        try:
            return SupabaseNotesRepository()
        except Exception:
            return InMemoryNotesRepository()
    return InMemoryNotesRepository()


class NotesRepoProxy(INotesRepository):
    def __init__(self):
        self._inner: Optional[INotesRepository] = None

    def _repo(self) -> INotesRepository:
        if self._inner is None:
            self._inner = get_notes_repository()
        return self._inner

    def create(self, note: dict) -> dict:
        return self._repo().create(note)

    def get(self, note_id: str) -> Optional[dict]:
        return self._repo().get(note_id)

    def list_all(self, user_id: Optional[str] = None) -> List[dict]:
        return self._repo().list_all(user_id=user_id)

    def update(self, note_id: str, fields: dict) -> Optional[dict]:
        return self._repo().update(note_id, fields)

    def delete(self, note_id: str) -> bool:
        return self._repo().delete(note_id)


notes_repository = NotesRepoProxy()
