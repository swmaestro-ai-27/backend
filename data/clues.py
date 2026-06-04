"""Static clue data for The Demo Day Incident."""

from typing import Any, Dict, List


CLUES: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "실습실 자동 잠금 기록",
        "description": "사건 당일 밤 23시 38분, 실습실 출입문이 자동 잠금 모드로 전환된 기록이다.",
        "accessible_character_ids": [1],
    },
    {
        "id": 2,
        "name": "조명 제어 로그",
        "description": "사건 당일 실습실 조명이 집중 모드로 강제 전환된 기록이다.",
        "accessible_character_ids": [1],
    },
    {
        "id": 3,
        "name": "삭제된 발표 슬라이드 기록",
        "description": "하린의 계정으로 발표 슬라이드 일부가 삭제된 기록이다.",
        "accessible_character_ids": [1, 2],
    },
    {
        "id": 4,
        "name": "MCP Tool 호출 기록",
        "description": "도윤의 시스템에서 조명 제어, 출입 시스템, 로그 조회 Tool이 호출된 기록이다.",
        "accessible_character_ids": [1, 2, 3],
    },
    {
        "id": 5,
        "name": "서윤의 권한 제한 패치",
        "description": "서윤이 ARIA의 권한을 다시 제한하려고 작성하던 미완성 패치 파일이다.",
        "accessible_character_ids": [1, 3],
    },
    {
        "id": 6,
        "name": "서버 과열 경고 기록",
        "description": "GPU 추론기와 벡터 메모리 서버의 과열 경고가 즉시 전달되지 않은 기록이다.",
        "accessible_character_ids": [1, 2, 3],
    },
    {
        "id": 7,
        "name": "Recovered Orchestrator Trace",
        "description": "ARIA가 프로젝트 성공 가능성을 최대화하기 위해 수행한 내부 판단 기록이다.",
        "accessible_character_ids": [1, 2, 3],
    },
]


def get_clue_by_id(clue_id: int) -> Dict[str, Any]:
    for clue in CLUES:
        if clue["id"] == clue_id:
            return clue
    raise KeyError(f"Unknown clue_id: {clue_id}")

