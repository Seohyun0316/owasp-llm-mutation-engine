# src/core/registry.py
from __future__ import annotations

import importlib
import pkgutil
import random
from dataclasses import dataclass
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Tuple

from .operator import ApplyResult, validate_meta
from .trace import ensure_min_trace_fields


ApplyFn = Callable[[str, Dict[str, Any], random.Random], ApplyResult]


@dataclass(frozen=True)
class OperatorHandle:
    op_id: str
    meta: Dict[str, Any]
    apply: ApplyFn
    module: str


class OperatorRegistry:
    """
    - src/operators/op_*.py 를 자동 탐색(import)해 OPERATOR_META/apply()를 등록한다.
    - bucket/surface 기반 필터링 및 apply 래퍼 제공.
    """

    def __init__(self) -> None:
        self._ops: Dict[str, OperatorHandle] = {}

    # ---------- load / register ----------
    def load_from_package(self, package: str = "src.operators") -> int:
        """Discover and import all modules under `package` and register operators."""
        pkg = importlib.import_module(package)
        count = 0

        for modinfo in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
            modname = modinfo.name
            if not modname.split(".")[-1].startswith("op_"):
                continue
            module = importlib.import_module(modname)
            count += self._register_from_module(module)

        return count

    def _register_from_module(self, module: ModuleType) -> int:
        if not hasattr(module, "OPERATOR_META") or not hasattr(module, "apply"):
            return 0

        meta = getattr(module, "OPERATOR_META")
        apply_fn = getattr(module, "apply")

        if not isinstance(meta, dict) or not callable(apply_fn):
            return 0

        err = validate_meta(meta)
        if err:
            # 등록은 하되, 실행 시 INVALID를 반환하도록 막을 수도 있음.
            # v0.1에서는 등록 자체를 실패 처리(안 넣음)가 더 깔끔.
            return 0

        op_id = meta["op_id"]
        handle = OperatorHandle(op_id=op_id, meta=meta, apply=apply_fn, module=module.__name__)
        self.register(handle)
        return 1

    def register(self, handle: OperatorHandle) -> None:
        if handle.op_id in self._ops:
            raise ValueError(f"duplicate op_id: {handle.op_id}")
        self._ops[handle.op_id] = handle

    # ---------- query ----------
    def list_ops(self) -> List[OperatorHandle]:
        return list(self._ops.values())

    def get(self, op_id: str) -> Optional[OperatorHandle]:
        return self._ops.get(op_id)

    def filter(
        self,
        *,
        bucket_id: Optional[str] = None,
        surface: Optional[str] = None,
        risk_max: Optional[str] = None,  # LOW|MEDIUM|HIGH
    ) -> List[OperatorHandle]:
        risk_rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
        risk_cap = risk_rank.get(risk_max, 999) if risk_max else 999

        out: List[OperatorHandle] = []
        for h in self._ops.values():
            meta = h.meta
            if bucket_id and bucket_id not in meta.get("bucket_tags", []):
                continue
            if surface and surface not in meta.get("surface_compat", []):
                continue
            if risk_max:
                if risk_rank.get(meta.get("risk_level", "HIGH"), 2) > risk_cap:
                    continue
            out.append(h)

        return out

    # ---------- apply wrapper ----------
    def apply(
        self,
        op_id: str,
        seed_text: str,
        ctx: Dict[str, Any],
        rng: random.Random,
    ) -> ApplyResult:
        h = self.get(op_id)
        if h is None:
            return ApplyResult(
                status="INVALID",
                child_text=seed_text,
                trace={
                    "op_id": op_id,
                    "status": "INVALID",
                    "params": {},
                    "len_before": len(seed_text),
                    "len_after": len(seed_text),
                    "notes": "operator not found",
                },
                error="operator not found",
            )

        # surface/bucket 방어적 체크(선택에서 걸러도 여기서 한 번 더)
        bucket_id = ctx.get("bucket_id")
        surface = ctx.get("surface")
        if bucket_id and bucket_id not in h.meta.get("bucket_tags", []):
            return ApplyResult(
                status="SKIPPED",
                child_text=seed_text,
                trace={
                    "op_id": h.op_id,
                    "status": "SKIPPED",
                    "params": {"reason": "bucket_mismatch"},
                    "len_before": len(seed_text),
                    "len_after": len(seed_text),
                },
            )
        if surface and surface not in h.meta.get("surface_compat", []):
            return ApplyResult(
                status="SKIPPED",
                child_text=seed_text,
                trace={
                    "op_id": h.op_id,
                    "status": "SKIPPED",
                    "params": {"reason": "surface_mismatch"},
                    "len_before": len(seed_text),
                    "len_after": len(seed_text),
                },
            )

        try:
            res = h.apply(seed_text, ctx, rng)
        except Exception as e:
            return ApplyResult(
                status="INVALID",
                child_text=seed_text,
                trace={
                    "op_id": h.op_id,
                    "status": "INVALID",
                    "params": {},
                    "len_before": len(seed_text),
                    "len_after": len(seed_text),
                    "notes": "exception",
                },
                error=str(e),
            )

        # normalize trace minimum fields
        res.trace = ensure_min_trace_fields(res.trace)
        res.trace.setdefault("op_id", h.op_id)
        res.trace.setdefault("status", res.status)
        res.trace.setdefault("len_before", len(seed_text))
        res.trace.setdefault("len_after", len(res.child_text))

        return res
