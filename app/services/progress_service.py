"""Award XP, level-ups, and prestige."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from app.domain.gamification import (
    DAILY_CAPS,
    MAX_LEVEL,
    MAX_PRESTIGE,
    PRESTIGE_BADGES,
    XP_REWARDS,
    apply_xp,
    xp_to_next_level,
)
from app.infrastructure.database.progress_repo import get_progress_repository


def _badges_for_level(level: int, existing: List[str]) -> List[str]:
    badges = list(existing)
    thresholds = (
        ("badge-01", 1),
        ("badge-02", 8),
        ("rank-mid-01", 12),
        ("rank-mid-02", 16),
    )
    for badge_id, thr in thresholds:
        if level >= thr and badge_id not in badges:
            badges.append(badge_id)
    return badges


class ProgressService:
    def __init__(self, repo=None):
        self.repo = repo or get_progress_repository()

    def get_me(self, user_id: str) -> Dict[str, Any]:
        row = self.repo.get(user_id)
        return self._public(row)

    def award(self, user_id: str, event_type: str) -> Dict[str, Any]:
        if event_type not in XP_REWARDS:
            return {
                **self.get_me(user_id),
                "awarded_xp": 0,
                "levels_gained": [],
                "badges_unlocked": [],
                "capped": False,
                "reason": "unknown_event",
            }

        row = self._roll_daily(self.repo.get(user_id))
        counts = dict(row.get("daily_counts") or {})
        used = int(counts.get(event_type, 0))
        cap = DAILY_CAPS.get(event_type)
        if cap is not None and used >= cap:
            return {
                **self._public(row),
                "awarded_xp": 0,
                "levels_gained": [],
                "badges_unlocked": [],
                "capped": True,
                "reason": "daily_cap",
            }

        prev_badges = list(row.get("unlocked_badges") or [])
        gained = XP_REWARDS[event_type]
        xp_cycle, level, levels_hit = apply_xp(
            int(row["xp_cycle"]), int(row["level"]), gained
        )
        counts[event_type] = used + 1
        badges = _badges_for_level(level, prev_badges)
        unlocked_now = [b for b in badges if b not in prev_badges]

        row.update(
            {
                "xp_cycle": xp_cycle,
                "level": level,
                "lifetime_xp": int(row["lifetime_xp"]) + gained,
                "daily_counts": counts,
                "daily_counts_date": date.today().isoformat(),
                "unlocked_badges": badges,
            }
        )
        saved = self.repo.upsert(row)
        self.repo.log_event(user_id, event_type, gained)
        return {
            **self._public(saved),
            "awarded_xp": gained,
            "levels_gained": levels_hit,
            "badges_unlocked": unlocked_now,
            "capped": False,
        }

    def prestige(self, user_id: str) -> Dict[str, Any]:
        row = self.repo.get(user_id)
        if int(row["level"]) < MAX_LEVEL:
            return {
                **self._public(row),
                "prestiged": False,
                "badges_unlocked": [],
                "reason": "not_max_level",
            }
        if int(row["prestige"]) >= MAX_PRESTIGE:
            return {
                **self._public(row),
                "prestiged": False,
                "badges_unlocked": [],
                "reason": "max_prestige",
            }

        new_prestige = int(row["prestige"]) + 1
        badges = list(row.get("unlocked_badges") or [])
        badge_id = PRESTIGE_BADGES.get(new_prestige)
        unlocked: List[str] = []
        if badge_id and badge_id not in badges:
            badges.append(badge_id)
            unlocked.append(badge_id)

        row.update(
            {
                "prestige": new_prestige,
                "level": 1,
                "xp_cycle": 0,
                "unlocked_badges": badges,
            }
        )
        saved = self.repo.upsert(row)
        return {
            **self._public(saved),
            "prestiged": True,
            "badges_unlocked": unlocked,
        }

    @staticmethod
    def _roll_daily(row: Dict[str, Any]) -> Dict[str, Any]:
        today = date.today().isoformat()
        if row.get("daily_counts_date") != today:
            return {
                **row,
                "daily_counts": {},
                "daily_counts_date": today,
            }
        return row

    @staticmethod
    def _public(row: Dict[str, Any]) -> Dict[str, Any]:
        level = int(row.get("level") or 1)
        xp_cycle = int(row.get("xp_cycle") or 0)
        need = xp_to_next_level(level)
        return {
            "user_id": row["id"],
            "xp_cycle": xp_cycle,
            "xp_to_next": need,
            "level": level,
            "prestige": int(row.get("prestige") or 0),
            "lifetime_xp": int(row.get("lifetime_xp") or 0),
            "unlocked_badges": list(row.get("unlocked_badges") or []),
            "can_prestige": level >= MAX_LEVEL
            and int(row.get("prestige") or 0) < MAX_PRESTIGE,
            "max_level": MAX_LEVEL,
            "max_prestige": MAX_PRESTIGE,
        }


_service: Optional[ProgressService] = None


def get_progress_service() -> ProgressService:
    global _service
    if _service is None:
        _service = ProgressService()
    return _service
