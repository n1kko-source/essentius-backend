from datetime import datetime, timezone
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
import uuid


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class HumanNoteCreate(BaseModel):
    """Nota escrita solo con el cerebro del usuario (sin IA en el editor)."""
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)
    topic: Optional[str] = None
    user_id: Optional[str] = None
    linked_note_ids: List[str] = Field(default_factory=list)


class HumanNoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    body: Optional[str] = Field(None, min_length=1)
    topic: Optional[str] = None
    linked_note_ids: Optional[List[str]] = None


class LibraryDocumentUpdate(BaseModel):
    """Renombrar un documento del catálogo de biblioteca."""
    title: str = Field(..., min_length=1, max_length=500)


class HumanNote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    body: str
    topic: Optional[str] = None
    user_id: Optional[str] = None
    linked_note_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    human_authored: bool = True


class EvidenceLink(BaseModel):
    knowledge_node_id: Optional[str] = None
    source: Optional[str] = None
    excerpt: str
    similarity: float
    relation: str  # supports | contradicts | related | gap
    url: Optional[str] = None


class Citation(BaseModel):
    title: str
    url: str
    snippet: Optional[str] = None


class BiasMirrorRequest(BaseModel):
    note_id: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None
    include_live: bool = False


class BiasMirrorResult(BaseModel):
    note_id: Optional[str] = None
    alignment_score: float = Field(..., ge=0.0, le=1.0)
    coverage_score: float = Field(..., ge=0.0, le=1.0)
    confirmation_bias_risk: float = Field(..., ge=0.0, le=1.0)
    summary: str
    supporting_evidence: List[EvidenceLink] = Field(default_factory=list)
    contradicting_signals: List[EvidenceLink] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    mode: str = "mock"
    sources: Literal["library", "live", "hybrid"] = "library"
    external_evidence: List[EvidenceLink] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
