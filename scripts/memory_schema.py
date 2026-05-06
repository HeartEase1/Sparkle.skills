# -*- coding: utf-8 -*-
"""Portable schema helpers for Skill-native long-term memory.

This module has no AstrBot dependency. It is designed for any runtime that
supports Skills and can read/write local files or call Python scripts.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict

CST = timezone(timedelta(hours=8))

MEMORY_VERSION = "1.0.0"

EVENT_TYPES = {
    "user_message", "assistant_message", "system_note", "manual_note"
}

FACT_TYPES = {
    "user_profile", "user_preference", "character_preference",
    "relationship", "boundary", "project", "important_event", "other"
}

CORRECTION_TYPES = {
    "profile", "personality", "interaction", "memory", "relations", "other"
}


def now_iso() -> str:
    return datetime.now(CST).replace(microsecond=0).isoformat()


def default_index(character: str = "unknown", game: str = "unknown") -> Dict[str, Any]:
    t = now_iso()
    return {
        "memory_version": MEMORY_VERSION,
        "character": character,
        "game": game,
        "created_at": t,
        "updated_at": t,
        "stats": {
            "events": 0,
            "facts": 0,
            "relationship_events": 0,
            "corrections": 0,
            "summaries": 0
        }
    }


def default_facts() -> Dict[str, Any]:
    return {
        "user": {
            "preferred_names": [],
            "disliked_names": [],
            "profile": {},
            "preferences": [],
            "boundaries": [],
            "projects": []
        },
        "character": {
            "preferred_names": [],
            "user_calls_character": [],
            "style_preferences": [],
            "corrections_pending_merge": []
        },
        "relationship": {
            "stage": "unknown",
            "tone": [],
            "shared_history": [],
            "important_events": []
        },
        "misc": {}
    }


def default_relationship() -> Dict[str, Any]:
    return {
        "stage": "unknown",
        "tone": [],
        "character_calls_user": None,
        "user_calls_character": [],
        "boundaries": [],
        "shared_history": [],
        "updated_at": now_iso()
    }
