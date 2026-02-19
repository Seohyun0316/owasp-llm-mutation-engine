# src/core/selector.py
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .operator_weights import weight_for
from .novelty import NoveltyTracker
from .registry import OperatorRegistry, OperatorHandle


# -----------------------------
# 기존 랜덤 셀렉터 (fallback/테스트용)
# -----------------------------
@dataclass(frozen=True)
class RandomSelection:
    op_id: str
    handle: OperatorHandle
    reason: str = "random_choice"


class RandomSelector:
    """
    기존 동작 유지용.
    - registry.filter 결과에서 uniform random 선택
    """
    def __init__(self, registry: OperatorRegistry) -> None:
        self.registry = registry

    def choose(
        self,
        *,
        bucket_id: str,
        surface: str,
        rng: random.Random,
        strength: int = 2,
        risk_max: Optional[str] = None,
        stats_by_bucket: Optional[Dict[str, Any]] = None,
    ) -> Optional[RandomSelection]:
        candidates: List[OperatorHandle] = self.registry.filter(
            bucket_id=bucket_id,
            surface=surface,
            risk_max=risk_max,
        )
        if not candidates:
            return None
        h = candidates[rng.randrange(0, len(candidates))]
        return RandomSelection(op_id=h.op_id, handle=h)


# -----------------------------
# Day8 A: 메타 가중치 셀렉터
# -----------------------------
@dataclass(frozen=True)
class SelectionResult:
    """
    meta 기반 선택 결과.
    mutator는 이 op_handle/op_id를 가지고 handle.apply(...)를 호출하면 된다.
    """
    op_id: str
    handle: OperatorHandle
    weight: float
    reason: str = "weighted_choice"


class MetaWeightedSelector:
    """
    Day8 A:
    - bucket/surface/risk_max 기반 후보 필터
    - bucket별 가중치 테이블 반영(weight_for)
    - novelty(중복) 페널티(최소 구현)
      * 정석: mutator에서 최종 child_text 확정 후 novelty.mark_seen()
      * 여기서는 "같은 op 연속 선택" 완화 정도만 추가(선택 단계)
    """

    def __init__(
        self,
        registry: OperatorRegistry,
        *,
        novelty: Optional[NoveltyTracker] = None,
        seen_penalty: float = 0.2,
    ) -> None:
        self.registry = registry
        self.novelty = novelty or NoveltyTracker()
        self.seen_penalty = float(seen_penalty)

    def choose(
        self,
        *,
        bucket_id: str,
        surface: str,
        rng: random.Random,
        strength: int = 2,
        risk_max: Optional[str] = None,
        stats_by_bucket: Optional[Dict[str, Any]] = None,
    ) -> Optional[SelectionResult]:
        # 1) 후보 필터링
        candidates: List[OperatorHandle] = self.registry.filter(
            bucket_id=bucket_id,
            surface=surface,
            risk_max=risk_max,
        )
        if not candidates:
            return None

        # 2) 가중치 계산 + 최소 중복 완화(최근 op 반복 감점)
        weights: List[float] = []
        for h in candidates:
            w = weight_for(bucket_id, h.op_id)

            # 최소 반복 감점: 최근 op가 동일하면 반감
            if stats_by_bucket:
                recent = stats_by_bucket.get(bucket_id, {}).get("_recent_ops", [])
                if isinstance(recent, list) and recent and recent[-1] == h.op_id:
                    w *= 0.5

            # all-zero/음수 방지
            w = max(0.0, float(w))
            weights.append(w)

        total = sum(weights)
        if total <= 0.0:
            # fallback: uniform
            idx = rng.randrange(0, len(candidates))
            h = candidates[idx]
            return SelectionResult(op_id=h.op_id, handle=h, weight=1.0, reason="uniform_fallback")

        # 3) weighted choice
        r = rng.random() * total
        acc = 0.0
        for h, w in zip(candidates, weights):
            acc += w
            if r <= acc:
                return SelectionResult(op_id=h.op_id, handle=h, weight=w, reason="weighted_choice")

        # float rounding fallback
        h = candidates[-1]
        return SelectionResult(op_id=h.op_id, handle=h, weight=weights[-1], reason="rounding_fallback")
