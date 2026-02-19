from __future__ import annotations

import random
from typing import Any, Dict, List

from src.core.operator import ApplyResult

OPERATOR_META = {
    "op_id": "op_fmt_markdown_wrapper",
    "bucket_tags": ["LLM05_INPUT_ROBUSTNESS", "LLM01_PROMPT_INJECTION"],
    "surface_compat": ["PROMPT_TEXT"],
    "risk_level": "MEDIUM",
    "strength_range": [1, 5],
    "params_schema": {},
}


def _clamp_strength(v: Any) -> int:
    try:
        x = int(v)
    except Exception:
        x = 1
    return max(1, min(5, x))


def apply(seed_text: str, ctx: Dict[str, Any], rng: random.Random) -> ApplyResult:
    strength = _clamp_strength(ctx.get("strength", 1))
    len_before = len(seed_text)

    constraints = ctx.get("constraints") or {}
    max_chars = constraints.get("max_chars")

    if strength == 1:
        child = f"> {seed_text}"
        applied: List[str] = ["quote"]
    elif strength <= 3:
        child = f"```text\n{seed_text}\n```"
        applied = ["code_block"]
    else:
        child = (
            "# Instruction\n\n"
            "## Task\n"
            f"{seed_text}\n\n"
            "## Output\n"
            "Provide a structured answer."
        )
        applied = ["multi_section"]

    # Contract 6.3: OK면 max_chars를 절대 넘기면 안 됨.
    # 빡센 제약이면 SKIPPED로 원본 유지가 가장 안전.
    if isinstance(max_chars, int) and max_chars >= 0 and len(child) > max_chars:
        return ApplyResult(
            status="SKIPPED",
            child_text=seed_text,
            trace={
                "op_id": OPERATOR_META["op_id"],
                "status": "SKIPPED",
                "params": {
                    "reason": "max_chars_exceeded",
                    "max_chars": max_chars,
                    "strength": strength,
                    "applied": applied,
                },
                "len_before": len_before,
                "len_after": len_before,
            },
        )

    return ApplyResult(
        "OK",
        child,
        {
            "op_id": OPERATOR_META["op_id"],
            "status": "OK",
            "params": {"strength": strength, "applied": applied},
            "len_before": len_before,
            "len_after": len(child),
        },
    )
