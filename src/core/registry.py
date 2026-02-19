from __future__ import annotations

import importlib
import pkgutil
import random
from dataclasses import dataclass
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Tuple

from .operator import ApplyResult, validate_meta
from .trace import ensure_min_trace_fields
from .validity_guard import GuardConfig, guard_text

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
    - 패치 포인트:
        * discovery 순서 결정화(sorted)
        * risk_level 정규화(LOW|MEDIUM|HIGH)
        * 로드/등록 실패 사유 누적(load_errors)
        * strict 모드 지원(실패 시 예외)
        * ApplyResult trace/status 불일치 방어(Contract 5.3)
    """

    def __init__(self) -> None:
        self._ops: Dict[str, OperatorHandle] = {}
        self.load_errors: List[Tuple[str, str]] = []

    # ---------- internal helpers ----------
    @staticmethod
    def _canon_applied(applied: Any) -> Any:
        """
        params.applied 같은 "순서 의미가 약한" trace를 프로세스 간 결정론적으로 정렬한다.
        expected shape (common):
          - list of [kind, count, detail]  e.g. ["zw_insert", 1, "U+200B"]
        If shape is unexpected, return as-is.
        """
        if not isinstance(applied, list):
            return applied

        def key(x: Any):
            if isinstance(x, list) and len(x) >= 3:
                a0 = str(x[0])
                a1 = x[1]
                try:
                    a1 = int(a1)
                except Exception:
                    a1 = str(a1)
                a2 = str(x[2])
                return (a0, a2, a1)
            return (str(type(x)), str(x))

        try:
            return sorted(applied, key=key)
        except Exception:
            return applied

    # ---------- load / register ----------
    def load_from_package(self, package: str = "src.operators", *, strict: bool = False) -> int:
        pkg = importlib.import_module(package)
        count = 0

        modnames: List[str] = []
        for modinfo in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
            modname = modinfo.name
            if modname.split(".")[-1].startswith("op_"):
                modnames.append(modname)

        for modname in sorted(modnames):
            try:
                module = importlib.import_module(modname)
                count += self._register_from_module(module, strict=strict)
            except Exception as e:
                msg = f"import failed: {e.__class__.__name__}: {e}"
                self.load_errors.append((modname, msg))
                if strict:
                    raise

        return count

    def _register_from_module(self, module: ModuleType, *, strict: bool = False) -> int:
        modname = getattr(module, "__name__", "<unknown>")

        if not hasattr(module, "OPERATOR_META") or not hasattr(module, "apply"):
            reason = "missing OPERATOR_META or apply()"
            self.load_errors.append((modname, reason))
            if strict:
                raise ValueError(f"{modname}: {reason}")
            return 0

        meta = getattr(module, "OPERATOR_META")
        apply_fn = getattr(module, "apply")

        if not isinstance(meta, dict):
            reason = "OPERATOR_META is not dict"
            self.load_errors.append((modname, reason))
            if strict:
                raise ValueError(f"{modname}: {reason}")
            return 0

        if not callable(apply_fn):
            reason = "apply is not callable"
            self.load_errors.append((modname, reason))
            if strict:
                raise ValueError(f"{modname}: {reason}")
            return 0

        self._normalize_meta_inplace(meta)

        err = validate_meta(meta)
        if err:
            reason = f"meta invalid: {err}"
            self.load_errors.append((modname, reason))
            if strict:
                raise ValueError(f"{modname}: {reason}")
            return 0

        op_id = meta["op_id"]
        handle = OperatorHandle(op_id=op_id, meta=meta, apply=apply_fn, module=modname)
        self.register(handle)
        return 1

    def _normalize_meta_inplace(self, meta: Dict[str, Any]) -> None:
        """
        최소한의 메타 정규화이다.
        - risk_level을 LOW|MEDIUM|HIGH로 통일한다.
        - bucket_tags/surface_compat 리스트를 정렬/중복제거하여 프로세스 간 결정론을 강제한다.
        """
        rv = meta.get("risk_level")
        if isinstance(rv, str):
            meta["risk_level"] = rv.upper()

        # set/dict 기반으로 생성된 리스트는 프로세스 간 순서가 흔들릴 수 있음
        for k in ("bucket_tags", "surface_compat"):
            v = meta.get(k)
            if isinstance(v, list):
                try:
                    meta[k] = sorted(set(str(x) for x in v))
                except Exception:
                    try:
                        meta[k] = sorted(v)
                    except Exception:
                        pass

    def register(self, handle: OperatorHandle) -> None:
        if handle.op_id in self._ops:
            raise ValueError(f"duplicate op_id: {handle.op_id}")
        self._ops[handle.op_id] = handle

    # ---------- query ----------
    def list_ops(self) -> List[OperatorHandle]:
        return [self._ops[k] for k in sorted(self._ops.keys())]

    def get(self, op_id: str) -> Optional[OperatorHandle]:
        return self._ops.get(op_id)

    def filter(
        self,
        *,
        bucket_id: Optional[str] = None,
        surface: Optional[str] = None,
        risk_max: Optional[str] = None,
    ) -> List[OperatorHandle]:
        risk_rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
        risk_cap = risk_rank.get(risk_max.upper(), 999) if isinstance(risk_max, str) else 999

        out: List[OperatorHandle] = []

        # dict 순회 대신 op_id 정렬 순회로 결정론 강제
        for h in self.list_ops():
            meta = h.meta
            if bucket_id and bucket_id not in meta.get("bucket_tags", []):
                continue
            if surface and surface not in meta.get("surface_compat", []):
                continue
            if risk_max:
                rl = meta.get("risk_level", "HIGH")
                rl_u = rl.upper() if isinstance(rl, str) else "HIGH"
                if risk_rank.get(rl_u, 2) > risk_cap:
                    continue
            out.append(h)

        out.sort(key=lambda x: x.op_id)
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

        # Contract invariant enforcement:
        # - operator가 trace를 잘못 채워도 registry가 최종값을 강제한다.
        res.trace["op_id"] = h.op_id
        res.trace["status"] = res.status
        res.trace["len_before"] = len(seed_text)
        res.trace["len_after"] = len(res.child_text)

        # Trace 안정화(프로세스 간 결정론):
        params = res.trace.get("params")
        if isinstance(params, dict) and "applied" in params:
            params["applied"] = self._canon_applied(params.get("applied"))
            res.trace["params"] = params

        return res
