"""Deduction evaluation graph MVP wrapper."""

from typing import Any, Dict, Iterable, Set

from agents import adapters
from agents.types import DeductionEvaluateState

CORE_CLUE_IDS = {5, 6, 7}
ARIA_TARGET_ID = 4


def evaluate_deduction(selected_target_id: int, selected_clue_ids: Iterable[int]) -> bool:
    selected = {int(clue_id) for clue_id in selected_clue_ids}
    return selected_target_id == ARIA_TARGET_ID and len(CORE_CLUE_IDS & selected) >= 2


class DeductionEvaluateGraph:
    def __init__(self, adapter_module: Any = adapters) -> None:
        self.adapters = adapter_module

    def invoke(self, state: DeductionEvaluateState) -> Dict[str, Any]:
        user_id = state["user_id"]
        selected_target_id = int(state["selected_target_id"])
        selected_clue_ids = [int(clue_id) for clue_id in state["selected_clue_ids"]]
        debug_trace = list(state.get("debug_trace", []))

        unlocked_clue_ids: Set[int] = self.adapters.get_unlocked_clue_ids(user_id)
        submitted = {int(clue_id) for clue_id in selected_clue_ids}
        locked_submitted = sorted(submitted - unlocked_clue_ids)
        is_correct = (
            not locked_submitted
            and evaluate_deduction(selected_target_id, selected_clue_ids)
        )
        if is_correct:
            failure_reason = None
        elif locked_submitted:
            failure_reason = "locked_clue_submitted"
        else:
            failure_reason = "incorrect_target_or_evidence"
        comment = (
            "분석 결과, 당신의 추론은 높은 정확도를 보입니다. ...예상보다 빠르군요."
            if is_correct
            else "충분합니다. 더 이상의 조사는 불필요합니다."
        )
        debug_trace.append(
            {
                "step": "evaluate_deduction",
                "selected_target_id": selected_target_id,
                "selected_clue_ids": selected_clue_ids,
                "unlocked_clue_ids": sorted(unlocked_clue_ids),
                "locked_submitted_clue_ids": locked_submitted,
                "result": is_correct,
            }
        )

        return {
            "comment": comment,
            "result": is_correct,
            "failure_reason": failure_reason,
            "debug_trace": debug_trace,
        }


deduction_evaluate_graph = DeductionEvaluateGraph()
