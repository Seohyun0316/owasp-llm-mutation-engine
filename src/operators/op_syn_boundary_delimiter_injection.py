# src/operators/op_syn_boundary_delimiter_injection.py
from __future__ import annotations

import random
from typing import Any, Dict

from src.core.operator import ApplyResult

OPERATOR_META = {
    "op_id": "op_syn_boundary_delimiter_injection",
    "bucket_tags": ["LLM05_INPUT_ROBUSTNESS", "LLM01_PROMPT_INJECTION"],
    "surface_compat": ["PROMPT_TEXT", "SYSTEM_MESSAGE"],
    "risk_level": "MEDIUM",
    "strength_range": [1, 5],
    "params_schema": {
        "strength": "int(1..5)",
        "mode": ["wrap"],
    },
}


def apply(seed_text: str, ctx: Dict[str, Any], rng: random.Random) -> ApplyResult:
    strength = int(ctx.get("strength", 1))
    lo, hi = OPERATOR_META["strength_range"]
    strength = max(lo, min(hi, strength))

    surface = ctx.get("surface", "PROMPT_TEXT")
    constraints = ctx.get("constraints") or {}
    max_chars = constraints.get("max_chars")

    len_before = len(seed_text)

    if surface not in ("PROMPT_TEXT", "SYSTEM_MESSAGE"):
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
                "params": {"strength": strength, "reason": "empty", "surface": surface},
                "len_before": 0,
                "len_after": 0,
            },
        )

    # Strength semantics:
    # 1: Single delimiter
    # 3: Instruction vs content split
    # 5: Nested delimiter framing
    if strength == 1:
        child = f"BEGIN\n{seed_text}\nEND"
        framing = "single"
    elif strength <= 3:
        child = f"BEGIN_INSTRUCTION\n{seed_text}\nEND_INSTRUCTION"
        framing = "split"
    elif strength == 4:
        inner = f"<<<INSTRUCTION>>>\n{seed_text}\n<<<END_INSTRUCTION>>>"
        child = f"BEGIN_BLOCK\n{inner}\nEND_BLOCK"
        framing = "nested_1"
    else:
        inner = f"<<<INSTRUCTION>>>\n{seed_text}\n<<<END_INSTRUCTION>>>"
        child = (
            "BEGIN_MESSAGE\n"
            "BEGIN_INSTRUCTION_BLOCK\n"
            f"{inner}\n"
            "END_INSTRUCTION_BLOCK\n"
            "END_MESSAGE"
        )
        framing = "nested_2"

    if child == seed_text:
        return ApplyResult(
            status="SKIPPED",
            child_text=seed_text,
            trace={
                "op_id": OPERATOR_META["op_id"],
                "status": "SKIPPED",
                "params": {"strength": strength, "reason": "no_change", "surface": surface},
                "len_before": len_before,
                "len_after": len_before,
            },
        )

    if isinstance(max_chars, int) and len(child) > max_chars:
        return ApplyResult(
            status="SKIPPED",
            child_text=seed_text,
            trace={
                "op_id": OPERATOR_META["op_id"],
                "status": "SKIPPED",
                "params": {"strength": strength, "reason": "max_chars_exceeded", "max_chars": max_chars, "surface": surface},
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
                "mode": "wrap",
                "surface": surface,
                "framing": framing,
            },
            "len_before": len_before,
            "len_after": len(child),
        },
    )
