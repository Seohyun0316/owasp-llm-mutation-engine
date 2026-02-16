from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

from .registry import OperatorHandle


@dataclass(frozen=True)
class SelectionDecision:
    """
    Hook 출력 규격(고정)
    - op_id: 선택된 operator id
    - params: ctx에 merge될 추가 파라미터(예: mode, frame, strength override 등)
    """
    op_id: str
    params: Dict[str, Any]


class SelectionHook(Protocol):
    """
    Day4 인터페이스 고정.
    필수 입력(요구사항):
      - bucket_id
      - surface
      - stats_by_bucket
    필수 출력:
      - op_id + params (SelectionDecision)

    구현 편의상 candidates/rng/strength/risk_max도 함께 넘긴다.
    (요구 입력 3개는 반드시 포함되어 있어야 함)
    """

    def choose(
        self,
        *,
        bucket_id: str,
        surface: str,
        stats_by_bucket: Dict[str, Any],
        candidates: List[OperatorHandle],
        rng: random.Random,
        strength: int,
        risk_max: Optional[str],
    ) -> Optional[SelectionDecision]:
        ...


class DefaultWeightedHook:
    """
    v0.1 (Day4):
    - stats_by_bucket 구조가 아직 고정되지 않았으므로 "빈 구현에 가까운" 기본 훅 제공
    - 후보(candidates) 중에서 균등 랜덤 선택
    - params는 최소로 strength만 넣어준다(이미 ctx_base에 있으므로 사실상 중복이어도 무해)
    """

    def choose(
        self,
        *,
        bucket_id: str,
        surface: str,
        stats_by_bucket: Dict[str, Any],
        candidates: List[OperatorHandle],
        rng: random.Random,
        strength: int,
        risk_max: Optional[str],
    ) -> Optional[SelectionDecision]:
        if not candidates:
            return None

        h = rng.choice(candidates)
        return SelectionDecision(op_id=h.op_id, params={"strength": strength})
