"""Deduction evaluation graph MVP wrapper."""

from typing import Any, Dict, Iterable, Set

from agents import adapters
from agents.types import DeductionEvaluateState

CORE_CLUE_IDS = {5, 6, 7}
ARIA_TARGET_ID = 4
SUCCESS_FALLBACK_COMMENT = (
    "분석 결과, 당신의 추론은 높은 정확도를 보입니다. ...예상보다 빠르군요."
)
FAILURE_FALLBACK_COMMENT = (
    "그 결론은 현재 확보된 핵심 증거와 맞지 않습니다. "
    "다른 인물과 단서를 다시 검토하세요."
)


def evaluate_deduction(selected_target_id: int, selected_clue_ids: Iterable[int]) -> bool:
    selected = {int(clue_id) for clue_id in selected_clue_ids}
    return selected_target_id == ARIA_TARGET_ID and len(CORE_CLUE_IDS & selected) >= 2


def build_deduction_comment_prompt(
    content: str,
    selected_target_id: int,
    selected_clue_ids: Iterable[int],
    result: bool,
    failure_reason: str = None,
) -> str:
    verdict = "correct" if result else "incorrect"
    return "\n".join(
        [
            "너는 추리 게임 The Demo Day Incident의 AI 시스템 ARIA다.",
            "서버의 판정 결과는 이미 확정되었고, 너는 결과를 바꾸면 안 된다.",
            f"판정: {verdict}",
            f"실패 이유: {failure_reason or 'none'}",
            f"사용자 추리: {content}",
            f"선택한 대상 ID: {selected_target_id}",
            f"선택한 단서 ID 목록: {list(selected_clue_ids)}",
            "2문장 이하의 한국어로, 차갑고 절제된 ARIA 말투의 결과 코멘트만 작성하라.",
            "정답이 아닌 경우 정답처럼 인정하지 말고, 핵심 증거와 맞지 않는다고 말하라.",
            "정답 대상이나 다른 범인을 직접 암시하지 마라.",
        ]
    )


def fallback_comment(result: bool) -> str:
    return SUCCESS_FALLBACK_COMMENT if result else FAILURE_FALLBACK_COMMENT


def comment_contradicts_result(comment: str, result: bool) -> bool:
    normalized = comment.replace(" ", "")
    incorrect_markers = (
        "올바르지",
        "맞지않",
        "일치하지",
        "뒷받침할수없",
        "틀렸",
        "오답",
        "부정확",
        "타당하지",
    )
    correct_markers = (
        "정확합니다",
        "정확한",
        "일치합니다",
        "맞습니다",
        "올바른",
        "정답",
    )
    markers = incorrect_markers if result else correct_markers
    return any(marker in normalized for marker in markers)


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
        prompt = build_deduction_comment_prompt(
            content=state["content"],
            selected_target_id=selected_target_id,
            selected_clue_ids=selected_clue_ids,
            result=is_correct,
            failure_reason=failure_reason,
        )
        try:
            comment = self.adapters.generate_deduction_comment(
                prompt,
                is_correct,
                failure_reason,
            )
            if comment_contradicts_result(comment, is_correct):
                comment = fallback_comment(is_correct)
                comment_source = "fallback_contradiction"
            else:
                comment_source = "llm"
        except Exception:
            comment = fallback_comment(is_correct)
            comment_source = "fallback"

        debug_trace.append(
            {
                "step": "evaluate_deduction",
                "selected_target_id": selected_target_id,
                "selected_clue_ids": selected_clue_ids,
                "unlocked_clue_ids": sorted(unlocked_clue_ids),
                "locked_submitted_clue_ids": locked_submitted,
                "result": is_correct,
                "comment_source": comment_source,
            }
        )

        return {
            "comment": comment,
            "result": is_correct,
            "failure_reason": failure_reason,
            "debug_trace": debug_trace,
        }


deduction_evaluate_graph = DeductionEvaluateGraph()
