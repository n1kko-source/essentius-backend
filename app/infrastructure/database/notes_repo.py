from typing import List, Optional, Dict
from datetime import datetime, timezone
import threading

from app.domain.interfaces import INotesRepository


class InMemoryNotesRepository(INotesRepository):
    """Persistencia MVP en memoria. Usada en tests y cuando no hay Supabase."""

    _store: Dict[str, dict] = {}
    _lock = threading.Lock()

    def create(self, note: dict) -> dict:
        with self._lock:
            note = {
                **note,
                "linked_note_ids": list(note.get("linked_note_ids") or []),
            }
            self._store[note["id"]] = note
            return note.copy()

    def get(self, note_id: str) -> Optional[dict]:
        with self._lock:
            note = self._store.get(note_id)
            return note.copy() if note else None

    def list_all(self, user_id: Optional[str] = None) -> List[dict]:
        with self._lock:
            notes = list(self._store.values())
            if user_id:
                notes = [n for n in notes if n.get("user_id") == user_id]
            notes.sort(key=lambda n: n.get("updated_at", ""), reverse=True)
            return [n.copy() for n in notes]

    def update(self, note_id: str, fields: dict) -> Optional[dict]:
        with self._lock:
            note = self._store.get(note_id)
            if not note:
                return None
            note.update(fields)
            if "linked_note_ids" in fields and fields["linked_note_ids"] is not None:
                note["linked_note_ids"] = list(fields["linked_note_ids"])
            note["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._store[note_id] = note
            return note.copy()

    def delete(self, note_id: str) -> bool:
        with self._lock:
            if note_id not in self._store:
                return False
            del self._store[note_id]
            return True


# Backwards-compatible name; prefer supabase proxy via get_notes_repository
notes_repository = InMemoryNotesRepository()
