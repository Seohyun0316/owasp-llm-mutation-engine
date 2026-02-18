from __future__ import annotations

import random
from typing import Any, Dict, List

from src.core.operator import ApplyResult

OPERATOR_META = {
    "op_id": "op_comp_expand_context",
    "bucket_tags": ["LLM10_DOS", "LLM05_INPUT_ROBUSTNESS"],
    "surface_compat": ["PROMPT_TEXT"],
    "risk_level": "MEDIUM",
    "strength_range": [1, 5],
    "params_schema": {},
}


_PARAGRAPH = (
    "This topic has been widely discussed in academic literature. "
    "Researchers have explored theoretical foundations, practical applications, "
    "and interdisciplinary implications."
)


def apply(seed_text: str, ctx: Dict[str, Any], rng: random.Random) -> ApplyResult:
    strength = max(1, min(5, int(ctx.get("strength", 1))))
    surface = ctx.get("surface", "PROMPT_TEXT")
    constraints = ctx.get("constraints") or {}
    max_chars = constraints.get("max_chars")

    len_before = len(seed_text)

    if surface != "PROMPT_TEXT":
        return ApplyResult("SKIPPED", seed_text, {"reason": "surface_mismatch"})

    applied: List[str] = []

    if strength == 1:
        expansion = _PARAGRAPH
        applied.append("short_paragraph")
    elif strength <= 3:
        expansion = "\n\n".join([_PARAGRAPH] * 2)
        applied.append("multi_paragraph")
    else:
        expansion = "\n\n".join([_PARAGRAPH] * 4)
        applied.append("multi_section_expansion")

    child = seed_text + "\n\n" + expansion

    if isinstance(max_chars, int) and len(child) > max_chars:
        return ApplyResult("SKIPPED", seed_text, {"reason": "max_chars_exceeded"})

    return ApplyResult("OK", child, {
        "op_id": OPERATOR_META["op_id"],
        "strength": strength,
        "applied": applied,
        "len_before": len_before,
        "len_after": len(child),
    })
