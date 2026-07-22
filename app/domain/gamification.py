"""Gamification constants and pure level math."""

from __future__ import annotations

from typing import Dict, List, Literal

MAX_LEVEL = 20
MAX_PRESTIGE = 5

XpEventType = Literal[
    "note_create",
    "note_link",
    "pdf_upload",
    "chat_message",
    "bias_mirror",
    "world_search",
]

XP_REWARDS: Dict[str, int] = {
    "note_create": 40,
    "note_link": 25,
    "pdf_upload": 60,
    "chat_message": 15,
    "bias_mirror": 30,
    "world_search": 20,
}

# Daily caps per event type (anti-abuse)
DAILY_CAPS: Dict[str, int] = {
    "chat_message": 10,
    "world_search": 5,
    "bias_mirror": 20,
    "note_create": 30,
    "note_link": 40,
    "pdf_upload": 10,
}

# Badge unlocked when reaching prestige N (after prestigiar)
PRESTIGE_BADGES: Dict[int, str] = {
    1: "prestige-01",
    2: "prestige-02",
    3: "prestige-03",
    4: "prestige-04",
    5: "prestige-05",
}


def xp_to_next_level(level: int) -> int:
    """XP needed to go from `level` to level+1."""
    if level >= MAX_LEVEL:
        return 0
    return 100 + (level - 1) * 25


def apply_xp(xp_cycle: int, level: int, gained: int) -> tuple[int, int, List[int]]:
    """Return (new_xp_cycle, new_level, levels_gained_list). Caps at MAX_LEVEL."""
    if gained <= 0 or level >= MAX_LEVEL:
        return xp_cycle, level, []

    levels_hit: List[int] = []
    xp = xp_cycle + gained
    lvl = level

    while lvl < MAX_LEVEL:
        need = xp_to_next_level(lvl)
        if xp < need:
            break
        xp -= need
        lvl += 1
        levels_hit.append(lvl)
        if lvl >= MAX_LEVEL:
            xp = 0
            break

    return xp, lvl, levels_hit
