"""Character chat graph MVP wrapper.

This module keeps the graph boundary separate from FastAPI. It does not depend
on LangGraph yet; the public `invoke` shape is compatible with moving to a
LangGraph implementation later.
"""

from typing import Any, Dict

from agents import adapters
from agents.guard import filter_context_clues
from agents.prompts.templates import build_character_prompt
from agents.types import CharacterChatState


class CharacterChatGraph:
    def __init__(self, adapter_module: Any = adapters) -> None:
        self.adapters = adapter_module

    def invoke(self, state: CharacterChatState) -> Dict[str, Any]:
        session_id = state["session_id"]
        character_id = int(state["character_id"])
        user_message = state["user_message"]
        debug_trace = list(state.get("debug_trace", []))

        character = self.adapters.get_character(character_id)
        recent_messages = self.adapters.get_recent_messages(session_id, character_id)
        accessible_clues = self.adapters.get_accessible_clues(character_id)
        unlocked_clue_ids = self.adapters.get_unlocked_clue_ids(session_id)
        context_clues = filter_context_clues(
            character_id=character_id,
            clues=accessible_clues,
            unlocked_ids=unlocked_clue_ids,
        )
        prompt = build_character_prompt(
            character=character,
            context_clues=context_clues,
            recent_messages=recent_messages,
            user_message=user_message,
        )
        debug_trace.append(
            {
                "step": "build_character_prompt",
                "character_id": character_id,
                "context_clue_ids": [clue["id"] for clue in context_clues],
            }
        )

        # LLM integration belongs to the CharacterChatGraph implementation issue.
        llm_response = state.get("llm_response") or "현재는 캐릭터 응답 생성기가 연결되지 않았습니다."

        self.adapters.save_message(session_id, character_id, "me", user_message)
        self.adapters.save_message(
            session_id,
            character_id,
            str(character.get("name", character_id)),
            llm_response,
        )

        return {
            "content": llm_response,
            "prompt": prompt,
            "used_clue_ids": [],
            "suggested_questions": [],
            "debug_trace": debug_trace,
        }


character_chat_graph = CharacterChatGraph()

