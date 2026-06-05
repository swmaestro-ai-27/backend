"""Progress unlock helper for MVP agent flows."""

from typing import Any, Dict

from agents.types import ProgressUnlockInput, ProgressUnlockResult


def apply_next_unlock(
    adapter: Any,
    payload: ProgressUnlockInput,
) -> ProgressUnlockResult:
    next_unlock = payload.get("next_unlock")
    if not next_unlock:
        return {"unlocked_target": None, "error": None}

    unlock_type = next_unlock.get("type")
    unlock_id = next_unlock.get("id")
    user_id = payload["user_id"]

    if unlock_type == "clue":
        adapter.unlock_clue(user_id, int(unlock_id))
    elif unlock_type == "character":
        adapter.unlock_character(user_id, int(unlock_id))
    else:
        return {
            "unlocked_target": None,
            "error": f"unsupported_unlock_type:{unlock_type}",
        }

    return {
        "unlocked_target": {"type": unlock_type, "id": int(unlock_id)},
        "error": None,
    }
