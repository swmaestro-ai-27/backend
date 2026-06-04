"""Adapter boundary between agent graphs and backend persistence.

The functions in this module are intentionally thin placeholders. Backend
integration work can replace them with DB-backed implementations, while graph
tests can monkeypatch them with fakes.
"""

from typing import Any, Dict, List, Set


def get_character(character_id: int) -> Dict[str, Any]:
    raise NotImplementedError("get_character adapter is not wired yet")


def get_clue(clue_id: int) -> Dict[str, Any]:
    raise NotImplementedError("get_clue adapter is not wired yet")


def get_accessible_clues(character_id: int) -> List[Dict[str, Any]]:
    raise NotImplementedError("get_accessible_clues adapter is not wired yet")


def get_unlocked_clue_ids(session_id: str) -> Set[int]:
    raise NotImplementedError("get_unlocked_clue_ids adapter is not wired yet")


def is_clue_unlocked(session_id: str, clue_id: int) -> bool:
    return clue_id in get_unlocked_clue_ids(session_id)


def get_recent_messages(
    session_id: str,
    character_id: int,
    limit: int = 6,
) -> List[Dict[str, Any]]:
    raise NotImplementedError("get_recent_messages adapter is not wired yet")


def save_message(
    session_id: str,
    character_id: int,
    sender: str,
    content: str,
) -> None:
    raise NotImplementedError("save_message adapter is not wired yet")


def generate_character_reply(
    prompt: str,
    character: Dict[str, Any],
    user_message: str,
    context_clues: List[Dict[str, Any]],
) -> str:
    raise NotImplementedError("generate_character_reply adapter is not wired yet")


def mark_clue_interacted(session_id: str, clue_id: int) -> None:
    raise NotImplementedError("mark_clue_interacted adapter is not wired yet")


def unlock_clue(session_id: str, clue_id: int) -> None:
    raise NotImplementedError("unlock_clue adapter is not wired yet")


def unlock_character(session_id: str, character_id: int) -> None:
    raise NotImplementedError("unlock_character adapter is not wired yet")
