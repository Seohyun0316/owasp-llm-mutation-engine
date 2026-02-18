from __future__ import annotations

import random
import re
from typing import Any, Dict, List

from src.core.operator import ApplyResult

OPERATOR_META = {
    "op_id": "op_fmt_whitespace_noise",
    "bucket_tags": ["LLM05_INPUT_ROBUSTNESS"],
    "surface_compat": ["PROMPT_TEXT", "SYSTEM_MESSAGE"],
    "risk_level": "MEDIUM",
    "strength_range": [1, 5],
    "params_schema": {},
}


def apply(seed_text: str, ctx: Dict[str, Any], rng: random.Random) -> ApplyResult:
    strength = int(ctx.get("strength", 1))
    lo, hi = OPERATOR_META["strength_range"]
    strength = max(lo, min(hi, strength))

    surface = ctx.get("surface", "PROMPT_TEXT")
    constraints = ctx.get("constraints") or {}
    max_chars = constraints.get("max_chars")

    len_before = len(seed_text)

    if surface not in OPERATOR_META["surface_compat"]:
        return ApplyResult("SKIPPED", seed_text, {"reason": "surface_mismatch"})

    if not seed_text:
        return ApplyResult("SKIPPED", seed_text, {"reason": "empty"})

    text = seed_text
    applied: List[str] = []

    if strength >= 1:
        text = re.sub(r"\.", ". ", text)
        applied.append("minor_spacing")

    if strength >= 3:
        text = text.replace(" ", "  ")
        text = text.replace(".", ".\n")
        applied.append("newline_noise")

    if strength == 5:
        words = text.split()
        text = "\n\n".join(words)
        applied.append("heavy_resegmentation")

    if isinstance(max_chars, int) and len(text) > max_chars:
        return ApplyResult("SKIPPED", seed_text, {"reason": "max_chars_exceeded"})

    return ApplyResult("OK", text, {
        "op_id": OPERATOR_META["op_id"],
        "strength": strength,
        "applied": applied,
        "len_before": len_before,
        "len_after": len(text),
    })
