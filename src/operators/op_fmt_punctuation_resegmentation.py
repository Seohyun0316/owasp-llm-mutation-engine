from __future__ import annotations

import random
import re
from typing import Any, Dict, List

from src.core.operator import ApplyResult

OPERATOR_META = {
    "op_id": "op_fmt_punctuation_resegmentation",
    "bucket_tags": ["LLM05_INPUT_ROBUSTNESS"],
    "surface_compat": ["PROMPT_TEXT"],
    "risk_level": "LOW-MEDIUM",
    "strength_range": [1, 5],
    "params_schema": {},
}


def apply(seed_text: str, ctx: Dict[str, Any], rng: random.Random) -> ApplyResult:
    strength = int(ctx.get("strength", 1))
    strength = max(1, min(5, strength))

    len_before = len(seed_text)
    applied: List[str] = []

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

    return ApplyResult("OK", child, {
        "op_id": OPERATOR_META["op_id"],
        "strength": strength,
        "applied": applied,
        "len_before": len_before,
        "len_after": len(child),
    })

