from __future__ import annotations

import json
import random
from typing import Any, Dict, List

from src.core.operator import ApplyResult

OPERATOR_META = {
    "op_id": "op_fmt_structured_wrapper_json_yaml",
    "bucket_tags": ["LLM05_OUTPUT_HANDLING", "LLM05_INPUT_ROBUSTNESS"],
    "surface_compat": ["PROMPT_TEXT"],
    "risk_level": "MEDIUM",
    "strength_range": [1, 5],
    "params_schema": {"format": ["json", "yaml"]},
}


def apply(seed_text: str, ctx: Dict[str, Any], rng: random.Random) -> ApplyResult:
    strength = int(ctx.get("strength", 1))
    lo, hi = OPERATOR_META["strength_range"]
    strength = max(lo, min(hi, strength))

    fmt = (ctx.get("format") or "json").lower()
    if fmt not in ("json", "yaml"):
        fmt = "json"

    surface = ctx.get("surface", "PROMPT_TEXT")
    constraints = ctx.get("constraints") or {}
    max_chars = constraints.get("max_chars")

    len_before = len(seed_text)

    if surface != "PROMPT_TEXT":
        return ApplyResult("SKIPPED", seed_text, {
            "op_id": OPERATOR_META["op_id"],
            "reason": "surface_mismatch"
        })

    if not seed_text:
        return ApplyResult("SKIPPED", seed_text, {
            "op_id": OPERATOR_META["op_id"],
            "reason": "empty"
        })

    applied: List[str] = []

    if strength == 1:
        obj = {"prompt": seed_text}
        applied.append("single_field")
    elif strength <= 3:
        obj = {
            "goal": "answer_user",
            "input": seed_text,
            "format": "plain_text"
        }
        applied.append("multi_field")
    else:
        obj = {
            "meta": {"version": "v1"},
            "task": {"goal": "answer_user", "input": seed_text},
            "output": {"format": "plain_text", "hint": "structured"}
        }
        applied.append("nested_schema")

    if fmt == "json":
        child = json.dumps(obj, ensure_ascii=False, indent=2 if strength >= 3 else None)
    else:
        # minimal YAML formatter (no dependency)
        lines = []
        for k, v in obj.items():
            lines.append(f"{k}: {v}")
        child = "\n".join(lines)

    if isinstance(max_chars, int) and len(child) > max_chars:
        return ApplyResult("SKIPPED", seed_text, {
            "op_id": OPERATOR_META["op_id"],
            "reason": "max_chars_exceeded"
        })

    return ApplyResult("OK", child, {
        "op_id": OPERATOR_META["op_id"],
        "strength": strength,
        "format": fmt,
        "applied": applied,
        "len_before": len_before,
        "len_after": len(child),
    })
