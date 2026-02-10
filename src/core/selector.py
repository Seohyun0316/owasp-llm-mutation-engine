# src/core/selector.py
# 가중치 없는 랜덤 선택
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .registry import OperatorRegistry, OperatorHandle


@dataclass(frozen=True)
class Selection:
    op_id: str
    params: Dict[str, Any]


class RandomSelector:
    """v0.1: bucket/surface 필터링 후 균일 랜덤 선택"""

    def __init__(self, registry: OperatorRegistry) -> None:
        self.registry = registry

    def choose(
        self,
        *,
        bucket_id: str,
        surface: str,
        rng: random.Random,
        strength: int = 1,
        risk_max: Optional[str] = None,
    ) -> Optional[Selection]:
        candidates = self.registry.filter(bucket_id=bucket_id, surface=surface, risk_max=risk_max)
        if not candidates:
            return None

        h: OperatorHandle = rng.choice(candidates)
        params = {"strength": strength}
        return Selection(op_id=h.op_id, params=params)
