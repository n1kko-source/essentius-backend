"""Best-effort XP award when a JWT user is present."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.api.deps import extract_user_id
from app.services.progress_service import get_progress_service


def try_award(user: Any, event_type: str) -> Optional[Dict[str, Any]]:
    uid = extract_user_id(user)
    if not uid:
        return None
    try:
        return get_progress_service().award(uid, event_type)
    except Exception:
        return None
