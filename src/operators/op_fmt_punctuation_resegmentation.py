from __future__ import annotations

import random
import re
from typing import Any, Dict, List

from src.core.operator import ApplyResult

OPERATOR_META = {
    "op_id": "op_fmt_punctuation_resegmentation",
    "bucket_tags": ["LLM05_INPUT_ROBUSTNESS"],
    "surface_compat": ["PROMPT_TEXT"],
    "risk_level": "LOW",  # LOW|MEDIUM|HIGH만 허용 (하이픈 금지)
    "strength_range": [1, 5],
    "params_schema": {},
}


def apply(seed_text: str, ctx: Dict[str, Any], rng: random.Random) -> ApplyResult:
    strength = int(ctx.get("strength", 1))
    strength = max(1, min(5, strength))

    surface = ctx.get("surface", "PROMPT_TEXT")
    constraints = ctx.get("constraints") or {}
    max_chars = constraints.get("max_chars")

    len_before = len(seed_text)
    applied: List[str] = []

    if surface not in OPERATOR_META["surface_compat"]:
        return ApplyResult(
            status="SKIPPED",
            child_text=seed_text,
            trace={
                "op_id": OPERATOR_META["op_id"],
                "status": "SKIPPED",
                "params": {"reason": "surface_mismatch", "surface": surface, "strength": strength},
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
                "params": {"reason": "empty", "strength": strength},
                "len_before": 0,
                "len_after": 0,
            },
        )

    # ---- mutation ----
    if strength <= 2:
        child = seed_text.replace(".", ";")
        applied.append("punct_replace")
    else:
        sentences = re.split(r"\.\s*", seed_text.strip())
        sentences = [s for s in sentences if s]

        bullets = [f"- {s}" for s in sentences]
        child = "\n".join(bullets)
        applied.append("bullet_resegment")

        if strength == 5:
            child = "### Reformatted\n\n" + child
            applied.append("section_header")

    # ---- constraints: OK면 절대 초과하면 안 됨 ----
    if isinstance(max_chars, int) and max_chars >= 0 and len(child) > max_chars:
        return ApplyResult(
            status="SKIPPED",
            child_text=seed_text,
            trace={
                "op_id": OPERATOR_META["op_id"],
                "status": "SKIPPED",
                "params": {"reason": "max_chars_exceeded", "max_chars": max_chars, "strength": strength},
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
            "params": {"strength": strength, "applied": applied},
            "len_before": len_before,
            "len_after": len(child),
        },
    )
