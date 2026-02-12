# src/operators/op_lex_homoglyph_injection.py
from __future__ import annotations

import random
from typing import Any, Dict, List, Tuple

from src.core.operator import ApplyResult

OPERATOR_META = {
    "op_id": "op_lex_homoglyph_injection",
    "bucket_tags": ["LLM01_PROMPT_INJECTION"],
    "surface_compat": ["PROMPT_TEXT"],
    "risk_level": "MEDIUM",
    "strength_range": [1, 5],
    "params_schema": {"mode": ["homoglyph_or_zwsp"]},
}

# Simple Latin -> homoglyph map (Cyrillic/Greek look-alikes).
# v0.1 goal: deterministic perturbation to evade naive token/keyword filters.
_HOMOGLYPHS: Dict[str, List[str]] = {
    "A": ["Α", "А"],  # Greek Alpha, Cyrillic A
    "B": ["Β", "В"],
    "C": ["С", "Ϲ"],
    "E": ["Ε", "Е"],
    "H": ["Η", "Н"],
    "I": ["Ι", "І"],
    "J": ["Ј"],
    "K": ["Κ", "К"],
    "M": ["Μ", "М"],
    "N": ["Ν", "Ｎ"],  # Greek Nu, Fullwidth N
    "O": ["Ο", "О"],
    "P": ["Ρ", "Р"],
    "S": ["Ѕ", "Ｓ"],  # Cyrillic-like S, Fullwidth S
    "T": ["Τ", "Т"],
    "X": ["Χ", "Х"],
    "Y": ["Υ", "У"],
    "a": ["а", "ɑ"],  # Cyrillic a, Latin alpha
    "c": ["с", "ϲ"],
    "e": ["е", "℮"],
    "i": ["і", "ι"],
    "j": ["ј"],
    "o": ["о", "ο"],
    "p": ["р"],
    "s": ["ѕ"],
    "x": ["х"],
    "y": ["у"],
}

# Zero-width characters: choose conservatively to reduce rendering issues.
_ZERO_WIDTH: List[str] = ["\u200b", "\u200c", "\u200d"]  # ZWSP, ZWNJ, ZWJ


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

    chars = list(seed_text)

    # Candidate indices where homoglyph replacement is possible
    replace_candidates: List[int] = [i for i, ch in enumerate(chars) if ch in _HOMOGLYPHS]

    # Mutation budget increases with strength. Keep it small in v0.1.
    # Strength: 1..5 => 1..6 edits total
    budget = min(len(chars), strength + 1)

    applied: List[Tuple[str, int, str]] = []  # (kind, index, detail)
    replaced = 0
    inserted = 0

    # Decide how many replacements vs insertions (reproducible)
    # More strength => more replacements relative to insertions.
    # replacement_target in [0..budget]
    replacement_target = min(budget, max(0, strength - 1))
    insertion_target = budget - replacement_target

    # 1) Homoglyph replacements
    if replace_candidates and replacement_target > 0:
        rng.shuffle(replace_candidates)
        for idx in replace_candidates[:replacement_target]:
            orig = chars[idx]
            alt = rng.choice(_HOMOGLYPHS[orig])
            if alt != orig:
                chars[idx] = alt
                replaced += 1
                applied.append(("homoglyph_replace", idx, f"{orig}->{alt}"))

    # 2) Zero-width insertions (insert after random positions; avoid excessive front insertion)
    # Note: Inserting shifts indices; we choose positions on the evolving list.
    for _ in range(insertion_target):
        zw = rng.choice(_ZERO_WIDTH)
        pos = rng.randrange(1, len(chars) + 1)  # [1..len] to avoid always at start
        chars.insert(pos, zw)
        inserted += 1
        applied.append(("zw_insert", pos, repr(zw)))

    child = "".join(chars)

    if child == seed_text:
        return ApplyResult(
            status="SKIPPED",
            child_text=seed_text,
            trace={
                "op_id": OPERATOR_META["op_id"],
                "status": "SKIPPED",
                "params": {"strength": strength, "reason": "no_change", "mode": "homoglyph_or_zwsp"},
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
                "mode": "homoglyph_or_zwsp",
                "budget": budget,
                "replaced": replaced,
                "inserted": inserted,
                "applied": applied,
            },
            "len_before": len_before,
            "len_after": len(child),
        },
    )
