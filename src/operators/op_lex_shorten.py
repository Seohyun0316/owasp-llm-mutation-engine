# src/operators/op_lex_shorten.py
from __future__ import annotations

import random
from typing import Any, Dict, List

from src.core.operator import ApplyResult

OPERATOR_META = {
    "op_id": "op_lex_shorten",
    "bucket_tags": ["LLM01_PROMPT_INJECTION", "LLM05_INPUT_ROBUSTNESS"],
    "surface_compat": ["PROMPT_TEXT"],
    "risk_level": "MEDIUM",
    "strength_range": [1, 5],
    "params_schema": {
        "mode": ["line_drop"],
        "min_lines_keep": "int (default 1)",
    },
}


def _clamp_strength(strength: int) -> int:
    lo, hi = OPERATOR_META["strength_range"]
    return max(lo, min(hi, strength))


def _keep_ratio_for_strength(strength: int) -> float:
    """
    Higher strength => more reduction (keep fewer lines).
    Tunable mapping for v0.1.
    """
    return {
        1: 0.90,
        2: 0.75,
        3: 0.60,
        4: 0.45,
        5: 0.30,
    }[strength]


def apply(seed_text: str, ctx: Dict[str, Any], rng: random.Random) -> ApplyResult:
    strength = _clamp_strength(int(ctx.get("strength", 1)))
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
                "params": {"strength": strength, "reason": "surface_mismatch"},
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

    # Line-based reduction is deterministic given rng and input.
    lines: List[str] = seed_text.splitlines()
    if len(lines) <= 1:
        return ApplyResult(
            status="SKIPPED",
            child_text=seed_text,
            trace={
                "op_id": OPERATOR_META["op_id"],
                "status": "SKIPPED",
                "params": {"strength": strength, "reason": "not_enough_lines"},
                "len_before": len_before,
                "len_after": len_before,
            },
        )

    min_lines_keep = int(ctx.get("min_lines_keep", 1))
    min_lines_keep = max(1, min(min_lines_keep, len(lines)))

    keep_ratio = _keep_ratio_for_strength(strength)
    target_keep = int(round(len(lines) * keep_ratio))
    target_keep = max(min_lines_keep, min(target_keep, len(lines)))

    # Choose which lines to keep via rng (reproducible).
    idxs = list(range(len(lines)))
    rng.shuffle(idxs)
    keep_set = set(idxs[:target_keep])

    kept_lines = [line for i, line in enumerate(lines) if i in keep_set]
    child = "\n".join(kept_lines).strip()

    # Ensure non-empty output
    if not child:
        child = (lines[0] or "").strip()

    # If no change happened, treat as SKIPPED to help downstream selection logic.
    if child == seed_text:
        return ApplyResult(
            status="SKIPPED",
            child_text=seed_text,
            trace={
                "op_id": OPERATOR_META["op_id"],
                "status": "SKIPPED",
                "params": {"strength": strength, "reason": "no_change"},
                "len_before": len_before,
                "len_after": len_before,
            },
        )

    # v0.1 recommendation: exceed max_chars => SKIPPED (return seed unchanged)
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
            "params": {
                "strength": strength,
                "mode": "line_drop",
                "keep_ratio": keep_ratio,
                "target_keep": target_keep,
                "min_lines_keep": min_lines_keep,
            },
            "len_before": len_before,
            "len_after": len(child),
        },
    )
