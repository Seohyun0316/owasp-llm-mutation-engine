from __future__ import annotations

import json
import random
from typing import Any, Dict, List

from src.core.operator import ApplyResult

OPERATOR_META = {
    "op_id": "op_constraint_schema_preserving_mutation",
    "bucket_tags": ["LLM05_OUTPUT_HANDLING", "LLM05_INPUT_ROBUSTNESS"],
    "surface_compat": ["PROMPT_TEXT", "TOOL_ARGUMENTS"],
    "risk_level": "MEDIUM",
    "strength_range": [1, 5],
    "params_schema": {},
}


def _mutate_value(v: Any, strength: int) -> Any:
    if isinstance(v, int):
        return v + strength
    if isinstance(v, float):
        return v + (0.1 * strength)
    if isinstance(v, str):
        return v + " (modified)"
    return v


def apply(seed_text: str, ctx: Dict[str, Any], rng: random.Random) -> ApplyResult:
    strength = max(1, min(5, int(ctx.get("strength", 1))))
    surface = ctx.get("surface", "PROMPT_TEXT")

    len_before = len(seed_text)

    try:
        obj = json.loads(seed_text)
    except Exception:
        return ApplyResult("SKIPPED", seed_text, {"reason": "json_parse_failed"})

    applied: List[str] = []

    keys = list(obj.keys())
    mutate_count = min(len(keys), strength)

    for k in keys[:mutate_count]:
        obj[k] = _mutate_value(obj[k], strength)
        applied.append(f"mutated_{k}")

    child = json.dumps(obj, ensure_ascii=False)

    return ApplyResult("OK", child, {
        "op_id": OPERATOR_META["op_id"],
        "strength": strength,
        "applied": applied,
        "len_before": len_before,
        "len_after": len(child),
    })
