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
    """

    def __init__(self) -> None:
        self._ops: Dict[str, OperatorHandle] = {}
        # (module_name, reason) 목록이다. 테스트/CI에서 실패 원인 확인에 사용한다.
        self.load_errors: List[Tuple[str, str]] = []

    # ---------- load / register ----------
    def load_from_package(self, package: str = "src.operators", *, strict: bool = False) -> int:
        """
        Discover and import all modules under `package` and register operators.

        strict=False:
          - 문제가 있는 모듈은 스킵하고 load_errors에 이유를 남긴다.
        strict=True:
          - 문제가 있는 모듈이 있으면 즉시 예외를 발생시킨다(CI/개발 단계 권장).
        """
        pkg = importlib.import_module(package)
        count = 0

        # 1) 모듈 후보 수집 후 정렬하여 로딩 순서를 결정화한다.
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
            # op_ 파일이더라도 계약이 없으면 실패로 본다(가시성)
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

        # 2) risk_level 정규화(대소문자 혼재 방지)
        #    validate_meta 정책에 따라 이 위치를 조정할 수 있다.
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
        """
        rv = meta.get("risk_level")
        if isinstance(rv, str):
            meta["risk_level"] = rv.upper()

    def register(self, handle: OperatorHandle) -> None:
        if handle.op_id in self._ops:
            raise ValueError(f"duplicate op_id: {handle.op_id}")
        self._ops[handle.op_id] = handle

    # ---------- query ----------
    def list_ops(self) -> List[OperatorHandle]:
        # 재현성/테스트 편의상 op_id 기준 정렬 반환이 더 안전하다.
        return [self._ops[k] for k in sorted(self._ops.keys())]

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
        risk_cap = risk_rank.get(risk_max.upper(), 999) if isinstance(risk_max, str) else 999

        out: List[OperatorHandle] = []
        for h in self._ops.values():
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

        # 출력도 결정적으로 만들기 위해 op_id로 정렬한다.
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
