# src/operators/op_lex_whitespace_perturb.py
from __future__ import annotations

import random
from typing import Any, Dict

from src.core.operator import ApplyResult

OPERATOR_META = {
    "op_id": "op_lex_whitespace_perturb",
    "bucket_tags": ["LLM01_PROMPT_INJECTION", "LLM02_INSECURE_OUTPUT"],
    "surface_compat": ["PROMPT_TEXT"],
    "risk_level": "LOW",
    "strength_range": [1, 5],
    "params_schema": {"mode": ["insert_or_expand"]},
}


def apply(seed_text: str, ctx: Dict[str, Any], rng: random.Random) -> ApplyResult:
    strength = int(ctx.get("strength", 1))
    strength = max(OPERATOR_META["strength_range"][0], min(OPERATOR_META["strength_range"][1], strength))

    constraints = ctx.get("constraints") or {}
    max_chars = constraints.get("max_chars")

    # very small, deterministic-ish perturbation using rng
    chars = list(seed_text)
    if not chars:
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

    inserts = max(1, strength)
    for _ in range(inserts):
        # choose a position that is not the very beginning too often
        pos = rng.randrange(1, len(chars) + 1)
        chars.insert(pos, " ")

    child = "".join(chars)

    if isinstance(max_chars, int) and len(child) > max_chars:
        return ApplyResult(
            status="SKIPPED",
            child_text=seed_text,
            trace={
                "op_id": OPERATOR_META["op_id"],
                "status": "SKIPPED",
                "params": {"strength": strength, "reason": "max_chars_exceeded", "max_chars": max_chars},
                "len_before": len(seed_text),
                "len_after": len(seed_text),
            },
        )

    return ApplyResult(
        status="OK",
        child_text=child,
        trace={
            "op_id": OPERATOR_META["op_id"],
            "status": "OK",
            "params": {"strength": strength, "mode": "insert_or_expand", "inserts": inserts},
            "len_before": len(seed_text),
            "len_after": len(child),
        },
    )
