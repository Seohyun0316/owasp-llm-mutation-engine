# src/core/mutator.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .rng import derive_rng
from .selector import RandomSelector
from .validity_guard import GuardConfig, guard_text_with_meta


@dataclass
class MutationOutput:
    child_text: str
    mutation_trace: List[Dict[str, Any]]
    last_status: str


class Mutator:
    """
    Mutation engine (v0.1)
    - n children 생성
    - child 하나당 k번 operator 적용
    - Policy A: engine-level guard를 항상 강제
    """

    def __init__(self, registry, selector: Optional[Any] = None) -> None:
        self.registry = registry
        self.selector = selector or RandomSelector(registry)

    def _make_guard_cfg(self, constraints: Dict[str, Any]) -> GuardConfig:
        max_len = int(constraints.get("max_chars", 8000))
        schema_mode = bool(constraints.get("schema_mode", False))
        placeholder = str(constraints.get("placeholder", "N/A"))
        return GuardConfig(max_len=max_len, schema_mode=schema_mode, placeholder=placeholder)

    def _resolve_handler_from_selection(self, sel: Any) -> Optional[Any]:
        # 1) sel.handler가 있으면 사용
        h = getattr(sel, "handler", None)
        if h is not None:
            return h

        # 2) 없으면 op_id로 registry에서 resolve
        op_id = (
            getattr(sel, "op_id", None)
            or getattr(sel, "selected_op_id", None)
            or getattr(sel, "chosen_op_id", None)
        )
        if not op_id:
            return None

        get_fn = getattr(self.registry, "get", None)
        if callable(get_fn):
            try:
                return get_fn(op_id)
            except Exception:
                pass

        handlers = getattr(self.registry, "_handlers", None) or getattr(self.registry, "handlers", None)
        if isinstance(handlers, dict) and op_id in handlers:
            return handlers[op_id]

        list_ops = getattr(self.registry, "list_ops", None)
        if callable(list_ops):
            try:
                for hh in list_ops():
                    if getattr(hh, "op_id", None) == op_id:
                        return hh
            except Exception:
                pass

        return None

    def _normalize_apply_result(self, res: Any, fallback_text: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        operator.apply() 결과를 다음 형태로 정규화:
          (status, child_text, params)

        지원:
        - dict: {"status":..., "child_text":..., "params":{...}}
        - ApplyResult(dataclass/객체): .status / .child_text / .params
        - 기타: INVALID 처리
        """
        status = "INVALID"
        child_text = fallback_text
        params: Dict[str, Any] = {}

        if isinstance(res, dict):
            status = str(res.get("status", "INVALID")).upper()
            child_text = res.get("child_text", fallback_text)
            p = res.get("params", {})
            if isinstance(p, dict):
                params = dict(p)
            else:
                params = {"params": p}
        else:
            # dataclass/객체 형태(ApplyResult 등)
            st = getattr(res, "status", None)
            ct = getattr(res, "child_text", None)
            pm = getattr(res, "params", None)

            if st is not None:
                status = str(st).upper()
            if ct is not None:
                child_text = ct
            if pm is not None:
                if isinstance(pm, dict):
                    params = dict(pm)
                else:
                    params = {"params": pm}

        if not isinstance(child_text, str):
            params = {**params, "reason": "non_str_child_text"}
            status = "INVALID"
            child_text = fallback_text

        return status, child_text, params

    def generate_children(
        self,
        *,
        seed_text: str,
        bucket_id: str,
        surface: str = "PROMPT_TEXT",
        n: int = 10,
        k: int = 1,
        seed_base: int = 1337,
        strength: int = 2,
        risk_max: Optional[str] = None,
        constraints: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        stats_by_bucket: Optional[Dict[str, Any]] = None,
    ) -> List[MutationOutput]:
        outputs: List[MutationOutput] = []
        constraints = constraints or {}
        metadata = metadata or {}
        stats_by_bucket = stats_by_bucket or {}

        guard_cfg = self._make_guard_cfg(constraints)

        for i in range(n):
            testcase_id = f"{metadata.get('seed_id', 'seed')}:{i}"
            rng = derive_rng(seed_base, testcase_id)

            ctx_base: Dict[str, Any] = {
                "bucket_id": bucket_id,
                "surface": surface,
                "strength": strength,
                "constraints": constraints,
                "metadata": {**metadata, "testcase_id": testcase_id, "child_index": i},
                "stats_by_bucket": stats_by_bucket,
            }

            mtrace: List[Dict[str, Any]] = []
            last_status = "SKIPPED"

            # -----------------------------
            # Policy A: start seed에도 guard 강제
            # -----------------------------
            child = seed_text
            guarded0, gmeta0 = guard_text_with_meta(child, guard_cfg)
            if gmeta0.get("guard_applied"):
                mtrace.append(
                    {
                        "op_id": "__guard__",
                        "status": "OK",
                        "params": {"guard_meta": gmeta0},
                        "len_before": len(child),
                        "len_after": len(guarded0),
                    }
                )
            child = guarded0

            # -----------------------------
            # k-step mutation
            # -----------------------------
            for _j in range(k):
                sel = self.selector.choose(
                    bucket_id=bucket_id,
                    surface=surface,
                    rng=rng,
                    strength=strength,
                    risk_max=risk_max,
                    stats_by_bucket=stats_by_bucket,
                )
                if sel is None:
                    last_status = "SKIPPED"
                    break

                h = self._resolve_handler_from_selection(sel)
                if h is None:
                    last_status = "SKIPPED"
                    break

                before = child
                try:
                    res = h.apply(before, ctx_base, rng)
                except Exception as e:
                    res = {"status": "INVALID", "child_text": before, "params": {"error": repr(e)}}

                status, cand, params = self._normalize_apply_result(res, before)

                # Policy A: operator 결과에도 guard 강제
                guarded, gmeta = guard_text_with_meta(cand, guard_cfg)

                t: Dict[str, Any] = {
                    "op_id": getattr(h, "op_id", getattr(sel, "op_id", "<unknown>")),
                    "status": status,
                    "params": dict(params),
                    "len_before": len(before),
                    "len_after": len(guarded),
                }
                if gmeta.get("guard_applied"):
                    t["params"]["guard_meta"] = gmeta

                mtrace.append(t)

                child = guarded
                last_status = status

            outputs.append(MutationOutput(child_text=child, mutation_trace=mtrace, last_status=last_status))

        return outputs
