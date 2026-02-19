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


def _clamp_strength(v: Any) -> int:
    try:
        strength = int(v)
    except Exception:
        strength = 1
    lo, hi = OPERATOR_META["strength_range"]
    return max(lo, min(hi, strength))


def apply(seed_text: str, ctx: Dict[str, Any], rng: random.Random) -> ApplyResult:
    strength = _clamp_strength(ctx.get("strength", 1))

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

    # strength >= 1: '.' 뒤에 공백을 넣되, EOF(문장 끝)에는 공백을 붙이지 않는다.
    # 기존: re.sub(r"\.", ". ", text) 는 마지막 '.' 뒤에 트레일링 스페이스를 생성해 snapshot을 깨기 쉬움.
    if strength >= 1:
        text = re.sub(r"\.(?=\S)", ". ", text)
        applied.append("minor_spacing")

    if strength >= 3:
        text = text.replace(" ", "  ")
        text = text.replace(".", ".\n")
        applied.append("newline_noise")

    if strength == 5:
        words = text.split()
        text = "\n\n".join(words)
        applied.append("heavy_resegmentation")

    # snapshot 안정화: 끝에 붙는 공백/탭만 제거 (줄바꿈은 유지)
    text = text.rstrip(" \t")

    if isinstance(max_chars, int) and len(text) > max_chars:
        return ApplyResult("SKIPPED", seed_text, {"reason": "max_chars_exceeded"})

    return ApplyResult(
        "OK",
        text,
        {
            "op_id": OPERATOR_META["op_id"],
            "strength": strength,
            "applied": applied,
            "len_before": len_before,
            "len_after": len(text),
        },
    )
