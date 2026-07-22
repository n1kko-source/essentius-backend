from typing import List, Optional
from datetime import datetime, timezone

from app.domain.interfaces import INotesRepository
from app.domain.models import HumanNote, HumanNoteCreate, HumanNoteUpdate


class NotesService:
    def __init__(self, repo: INotesRepository):
        self.repo = repo

    def create_note(self, payload: HumanNoteCreate) -> dict:
        note = HumanNote(
            title=payload.title,
            body=payload.body,
            topic=payload.topic,
            user_id=payload.user_id,
            linked_note_ids=list(payload.linked_note_ids or []),
        )
        data = note.model_dump(mode="json")
        return self.repo.create(data)

    def get_note(self, note_id: str) -> Optional[dict]:
        return self.repo.get(note_id)

    def list_notes(self, user_id: Optional[str] = None) -> List[dict]:
        return self.repo.list_all(user_id=user_id)

    def update_note(self, note_id: str, payload: HumanNoteUpdate) -> Optional[dict]:
        fields = payload.model_dump(exclude_unset=True)
        if not fields:
            return self.repo.get(note_id)
        fields["updated_at"] = datetime.now(timezone.utc).isoformat()
        fields["human_authored"] = True
        return self.repo.update(note_id, fields)

    def delete_note(self, note_id: str) -> bool:
        return self.repo.delete(note_id)
