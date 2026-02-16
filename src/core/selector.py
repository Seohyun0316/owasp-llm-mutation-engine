from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .registry import OperatorRegistry
from .selection_hook import DefaultWeightedHook, SelectionDecision, SelectionHook


@dataclass(frozen=True)
class SelectionResult:
    op_id: str
    params: Dict[str, Any]


class RandomSelector:
    """
    Day4:
    - Operator selection hook(가중 선택) 인터페이스를 고정한다.
    - 기본 hook은 균등 랜덤 선택(빈 구현 수준)이다.
    """

    def __init__(self, registry: OperatorRegistry, hook: Optional[SelectionHook] = None) -> None:
        self.registry = registry
        self.hook: SelectionHook = hook or DefaultWeightedHook()

    def choose(
        self,
        *,
        bucket_id: str,
        surface: str,
        rng: random.Random,
        strength: int,
        risk_max: Optional[str] = None,
        stats_by_bucket: Optional[Dict[str, Any]] = None,
    ) -> Optional[SelectionResult]:
        stats_by_bucket = stats_by_bucket or {}

        # 후보 연산자 목록(Registry의 filter 사용)
        candidates = self.registry.filter(bucket_id=bucket_id, surface=surface, risk_max=risk_max)
        if not candidates:
            return None

        dec: Optional[SelectionDecision] = self.hook.choose(
            bucket_id=bucket_id,
            surface=surface,
            stats_by_bucket=stats_by_bucket,
            candidates=candidates,
            rng=rng,
            strength=strength,
            risk_max=risk_max,
        )

        if dec is None:
            return None

        # 최소 보정: params는 dict여야 한다.
        params = dec.params if isinstance(dec.params, dict) else {}
        return SelectionResult(op_id=dec.op_id, params=params)
