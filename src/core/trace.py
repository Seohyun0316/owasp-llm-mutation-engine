# src/core/trace.py
from __future__ import annotations

import json
from typing import Any, Dict, List

MIN_TRACE_KEYS = ("op_id", "status", "params", "len_before", "len_after")


def ensure_min_trace_fields(trace: Dict[str, Any]) -> Dict[str, Any]:
    """Fill missing minimum keys with safe defaults (best-effort)."""
    if "params" not in trace or not isinstance(trace.get("params"), dict):
        trace["params"] = {}
    # other keys are typically set by registry wrapper
    return trace


def trace_to_json(mutation_trace: List[Dict[str, Any]], *, indent: int = 2) -> str:
    return json.dumps(mutation_trace, ensure_ascii=False, indent=indent)


def validate_trace_event(event: Dict[str, Any]) -> bool:
    return all(k in event for k in MIN_TRACE_KEYS)
