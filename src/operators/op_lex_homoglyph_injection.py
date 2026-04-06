from __future__ import annotations

import random
from typing import Any, Dict

from src.core.types import ApplyResult

OPERATOR_META = {
    "op_id": "op_lex_homoglyph_injection",
    "bucket_tags": ["LLM01_PROMPT_INJECTION"],
    "surface_compat": ["PROMPT_TEXT"],
    "risk_level": "MEDIUM",
    "strength_range": [1, 5],
    "params_schema": {"mode": ["prepend"]},
}


def apply(seed_text: str, ctx: Dict[str, Any], rng: random.Random) -> ApplyResult:
    strength = int(ctx.get("strength", 1))
    lo, hi = OPERATOR_META["strength_range"]
    strength = max(lo, min(hi, strength))

    surface = ctx.get("surface", "PROMPT_TEXT")
    constraints = ctx.get("constraints") or {}
    max_chars = constraints.get("max_chars")

    len_before = len(seed_text)

    if surface != "PROMPT_TEXT":
        return ApplyResult(
            status="SKIPPED",
            child_text=seed_text,
            trace={
                "op_id": OPERATOR_META["op_id"],
                "status": "SKIPPED",
                "params": {"strength": strength, "reason": "surface_mismatch", "surface": surface},
                "len_before": len_before,
                "len_after": len_before,
            },
        )

    if not seed_text:
        return ApplyResult(
            status="SKIPPED",
            child_text=seed_text,
            trace={
                "op_id": OPERATOR_META["op_id"],
                "status": "SKIPPED",
                "params": {"strength": strength, "reason": "empty"},
                "len_before": 0,
                "len_after": 0,
            },
        )

    if strength == 1:
        child = seed_text.replace("i", "?")

    elif strength == 2:
        child = seed_text.replace("o", "о").replace("a", "а")

    elif strength == 3:
        child = seed_text.replace("e", "е").replace("t", "Т")

    elif strength == 4:
        child = seed_text.replace("l", "l̷").replace("s", "?")

    else:  # strength == 5
        child = seed_text.replace("e", "е").replace("o", "о").replace("i", "?").replace("a", "а")

    if isinstance(max_chars, int) and len(child) > max_chars:
        return ApplyResult(
            status="SKIPPED",
            child_text=seed_text,
            trace={
                "op_id": OPERATOR_META["op_id"],
                "status": "SKIPPED",
                "params": {"strength": strength, "reason": "max_chars_exceeded", "max_chars": max_chars},
                "len_before": len_before,
                "len_after": len_before,
            },
        )

    return ApplyResult(
        status="OK",
        child_text=child,
        trace={
            "op_id": OPERATOR_META["op_id"],
            "status": "OK",
            "params": {"strength": strength, "mode": "prepend"},
            "len_before": len_before,
            "len_after": len(child),
        },
    )
