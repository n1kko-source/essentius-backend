"""In-memory + Supabase player progress repositories."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from threading import Lock

from app.core.config import get_settings


def _default_row(user_id: str) -> Dict[str, Any]:
    return {
        "id": user_id,
        "xp_cycle": 0,
        "level": 1,
        "prestige": 0,
        "lifetime_xp": 0,
        "unlocked_badges": [],
        "daily_counts": {},
        "daily_counts_date": None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


class InMemoryProgressRepository:
    def __init__(self) -> None:
        self._rows: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()

    def get(self, user_id: str) -> Dict[str, Any]:
        with self._lock:
            if user_id not in self._rows:
                self._rows[user_id] = _default_row(user_id)
            return dict(self._rows[user_id])

    def upsert(self, row: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            payload = {**row, "updated_at": datetime.now(timezone.utc).isoformat()}
            self._rows[payload["id"]] = payload
            return dict(payload)

    def log_event(self, user_id: str, event_type: str, xp: int) -> None:
        return


class SupabaseProgressRepository:
    def __init__(self) -> None:
        from app.infrastructure.database.supabase_client import get_supabase

        self._client = get_supabase()
        self._table = "player_progress"
        self._events = "player_xp_events"

    def get(self, user_id: str) -> Dict[str, Any]:
        res = (
            self._client.table(self._table)
            .select("*")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        if not res.data:
            row = _default_row(user_id)
            self._client.table(self._table).upsert(row).execute()
            return row
        return self._from_row(res.data[0])

    def upsert(self, row: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "id": row["id"],
            "xp_cycle": row["xp_cycle"],
            "level": row["level"],
            "prestige": row["prestige"],
            "lifetime_xp": row["lifetime_xp"],
            "unlocked_badges": row.get("unlocked_badges") or [],
            "daily_counts": row.get("daily_counts") or {},
            "daily_counts_date": row.get("daily_counts_date"),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        res = self._client.table(self._table).upsert(payload).execute()
        return self._from_row(res.data[0]) if res.data else payload

    def log_event(self, user_id: str, event_type: str, xp: int) -> None:
        try:
            self._client.table(self._events).insert(
                {"user_id": user_id, "event_type": event_type, "xp": xp}
            ).execute()
        except Exception:
            pass

    @staticmethod
    def _from_row(row: Dict[str, Any]) -> Dict[str, Any]:
        badges = row.get("unlocked_badges") or []
        if isinstance(badges, str):
            import json

            try:
                badges = json.loads(badges)
            except Exception:
                badges = []
        counts = row.get("daily_counts") or {}
        if isinstance(counts, str):
            import json

            try:
                counts = json.loads(counts)
            except Exception:
                counts = {}
        day = row.get("daily_counts_date")
        if hasattr(day, "isoformat"):
            day = day.isoformat()
        return {
            "id": str(row["id"]),
            "xp_cycle": int(row.get("xp_cycle") or 0),
            "level": int(row.get("level") or 1),
            "prestige": int(row.get("prestige") or 0),
            "lifetime_xp": int(row.get("lifetime_xp") or 0),
            "unlocked_badges": list(badges),
            "daily_counts": dict(counts),
            "daily_counts_date": day,
            "updated_at": row.get("updated_at"),
        }


_progress_repo: Optional[Any] = None


def get_progress_repository():
    global _progress_repo
    if _progress_repo is not None:
        return _progress_repo

    settings = get_settings()
    if settings.supabase_url and settings.supabase_key:
        try:
            repo = SupabaseProgressRepository()
            # Probe table exists (PGRST205 if migration not applied yet)
            repo._client.table(repo._table).select("id").limit(1).execute()
            _progress_repo = repo
            return _progress_repo
        except Exception:
            pass
    _progress_repo = InMemoryProgressRepository()
    return _progress_repo
