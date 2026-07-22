"""Document catalog (library list) — Supabase + in-memory fallback."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional
import uuid

from app.core.config import get_settings


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class InMemoryDocumentsRepository:
    def __init__(self) -> None:
        self._rows: List[Dict[str, Any]] = []
        self._lock = Lock()

    def create(
        self, title: str, user_id: Optional[str], chunk_count: int = 0
    ) -> Dict[str, Any]:
        row = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": title,
            "chunk_count": chunk_count,
            "created_at": _now(),
        }
        with self._lock:
            self._rows.insert(0, row)
        return dict(row)

    def list_for_user(self, user_id: Optional[str]) -> List[Dict[str, Any]]:
        with self._lock:
            if not user_id:
                return []
            rows = [r for r in self._rows if r.get("user_id") == user_id]
            return [dict(r) for r in rows]

    def get_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            for row in self._rows:
                if row.get("id") == document_id:
                    return dict(row)
        return None

    def update_title(
        self, document_id: str, title: str
    ) -> Optional[Dict[str, Any]]:
        with self._lock:
            for row in self._rows:
                if row.get("id") == document_id:
                    row["title"] = title
                    return dict(row)
        return None

    def set_chunk_count(
        self, document_id: str, chunk_count: int
    ) -> Optional[Dict[str, Any]]:
        with self._lock:
            for row in self._rows:
                if row.get("id") == document_id:
                    row["chunk_count"] = int(chunk_count)
                    return dict(row)
        return None

    def delete(self, document_id: str) -> bool:
        with self._lock:
            before = len(self._rows)
            self._rows = [r for r in self._rows if r.get("id") != document_id]
            return len(self._rows) < before


class SupabaseDocumentsRepository:
    def __init__(self) -> None:
        from app.infrastructure.database.supabase_client import get_supabase

        self._client = get_supabase()
        self._table = "documents"

    def create(
        self, title: str, user_id: Optional[str], chunk_count: int = 0
    ) -> Dict[str, Any]:
        payload = {
            "title": title,
            "user_id": user_id,
            "chunk_count": chunk_count,
        }
        res = self._client.table(self._table).insert(payload).execute()
        return self._from_row(res.data[0])

    def list_for_user(self, user_id: Optional[str]) -> List[Dict[str, Any]]:
        if not user_id:
            return []
        q = (
            self._client.table(self._table)
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
        )
        res = q.execute()
        return [self._from_row(r) for r in (res.data or [])]

    def get_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        res = (
            self._client.table(self._table)
            .select("*")
            .eq("id", document_id)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        if not rows:
            return None
        return self._from_row(rows[0])

    def update_title(
        self, document_id: str, title: str
    ) -> Optional[Dict[str, Any]]:
        res = (
            self._client.table(self._table)
            .update({"title": title})
            .eq("id", document_id)
            .execute()
        )
        rows = res.data or []
        if not rows:
            return None
        return self._from_row(rows[0])

    def set_chunk_count(
        self, document_id: str, chunk_count: int
    ) -> Optional[Dict[str, Any]]:
        res = (
            self._client.table(self._table)
            .update({"chunk_count": int(chunk_count)})
            .eq("id", document_id)
            .execute()
        )
        rows = res.data or []
        if not rows:
            return None
        return self._from_row(rows[0])

    def delete(self, document_id: str) -> bool:
        res = (
            self._client.table(self._table).delete().eq("id", document_id).execute()
        )
        return bool(res.data)

    @staticmethod
    def _from_row(row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": str(row["id"]),
            "user_id": str(row["user_id"]) if row.get("user_id") else None,
            "title": row["title"],
            "chunk_count": int(row.get("chunk_count") or 0),
            "created_at": row.get("created_at"),
        }


_docs_repo: Optional[Any] = None


def get_documents_repository():
    global _docs_repo
    if _docs_repo is not None:
        return _docs_repo

    settings = get_settings()
    if settings.supabase_url and settings.supabase_key:
        try:
            repo = SupabaseDocumentsRepository()
            repo._client.table(repo._table).select("id").limit(1).execute()
            _docs_repo = repo
            return _docs_repo
        except Exception:
            pass
    _docs_repo = InMemoryDocumentsRepository()
    return _docs_repo
