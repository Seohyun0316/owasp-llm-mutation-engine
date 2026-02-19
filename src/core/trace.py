from __future__ import annotations

import json
from typing import Any, Dict, List


def _normalize_jsonable(x: Any) -> Any:
    """
    Make trace payload JSON-stable:
    - tuple -> list (recursive)
    - dict/list recurse
    """
    if isinstance(x, tuple):
        return [_normalize_jsonable(v) for v in x]
    if isinstance(x, list):
        return [_normalize_jsonable(v) for v in x]
    if isinstance(x, dict):
        return {k: _normalize_jsonable(v) for k, v in x.items()}
    return x


def ensure_min_trace_fields(trace: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure required keys exist and make the structure JSON-stable.
    """
    if not isinstance(trace, dict):
        trace = {}

    trace = _normalize_jsonable(trace)

    trace.setdefault("op_id", "UNKNOWN_OP")
    trace.setdefault("status", "SKIPPED")
    trace.setdefault("params", {})
    trace.setdefault("len_before", 0)
    trace.setdefault("len_after", trace.get("len_before", 0))
    return trace


def trace_to_json(trace: List[Dict[str, Any]]) -> str:
    """
    Pretty print helper used by Mutator.pretty_print().
    """
    safe = _normalize_jsonable(trace)
    return json.dumps(safe, ensure_ascii=False, indent=2, sort_keys=True)
