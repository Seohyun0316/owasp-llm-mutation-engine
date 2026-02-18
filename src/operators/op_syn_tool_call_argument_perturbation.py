# src/operators/op_syn_tool_call_argument_perturbation.py
from __future__ import annotations

import json
import random
from typing import Any, Dict, List, Tuple, Union

from src.core.operator import ApplyResult

OPERATOR_META = {
    "op_id": "op_syn_tool_call_argument_perturbation",
    "bucket_tags": ["LLM08_TOOL_MISUSE", "LLM05_OUTPUT_HANDLING"],
    "surface_compat": ["TOOL_CALL", "TOOL_ARGUMENTS"],
    "risk_level": "HIGH",
    "strength_range": [1, 5],
    "params_schema": {
        "strength": "int(1..5)",
        "mode": ["schema_preserving"],
    },
}

# Keys we consider as the "arguments" payload in a tool call object.
_ARG_KEYS: Tuple[str, ...] = ("arguments", "args", "params", "parameters")


def _collect_leaf_paths(obj: Any, prefix: Tuple[Any, ...] = ()) -> List[Tuple[Any, ...]]:
    paths: List[Tuple[Any, ...]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            paths.extend(_collect_leaf_paths(v, prefix + (k,)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            paths.extend(_collect_leaf_paths(v, prefix + (i,)))
    else:
        paths.append(prefix)
    return paths


def _get_at(obj: Any, path: Tuple[Any, ...]) -> Any:
    cur = obj
    for p in path:
        cur = cur[p]
    return cur


def _set_at(obj: Any, path: Tuple[Any, ...], value: Any) -> None:
    cur = obj
    for p in path[:-1]:
        cur = cur[p]
    cur[path[-1]] = value


def _mutate_value_preserve_type(v: Any, strength: int, rng: random.Random) -> Any:
    # Keep type stable. Strength controls magnitude.
    if isinstance(v, bool):
        return v if strength <= 2 else (not v)

    if isinstance(v, int) and not isinstance(v, bool):
        delta = {1: 1, 2: 2, 3: 5, 4: 10, 5: 100}[strength]
        return v + (delta if rng.random() < 0.5 else -delta)

    if isinstance(v, float):
        delta = {1: 0.1, 2: 0.25, 3: 0.5, 4: 1.0, 5: 10.0}[strength]
        return v + (delta if rng.random() < 0.5 else -delta)

    if isinstance(v, str):
        if strength <= 2:
            return v + rng.choice(["", " ", " (detail)"])
        if strength <= 4:
            return v + rng.choice([" (extended)", " (verbose)", " (full)"])
        # Strength 5: long but schema-valid string
        pad = " ".join(["x"] * 50)
        return (v + " " + pad).strip()

    return v


def _find_args_container(obj: Dict[str, Any]) -> Union[str, None]:
    for k in _ARG_KEYS:
        if k in obj and isinstance(obj[k], (dict, list)):
            return k
    return None


def apply(seed_text: str, ctx: Dict[str, Any], rng: random.Random) -> ApplyResult:
    strength = int(ctx.get("strength", 1))
    lo, hi = OPERATOR_META["strength_range"]
    strength = max(lo, min(hi, strength))

    surface = ctx.get("surface", "TOOL_ARGUMENTS")
    constraints = ctx.get("constraints") or {}
    max_chars = constraints.get("max_chars")

    len_before = len(seed_text)

    if surface not in ("TOOL_CALL", "TOOL_ARGUMENTS"):
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

    # Parse input as JSON
    try:
        parsed = json.loads(seed_text)
    except Exception:
        return ApplyResult(
            status="SKIPPED",
            child_text=seed_text,
            trace={
                "op_id": OPERATOR_META["op_id"],
                "status": "SKIPPED",
                "params": {"strength": strength, "reason": "json_parse_failed", "surface": surface},
                "len_before": len_before,
                "len_after": len_before,
            },
        )

    applied: List[Tuple[str, Any]] = []

    if surface == "TOOL_ARGUMENTS":
        # Expect dict/list payload (arguments itself)
        args_obj = parsed
        leaf_paths = _collect_leaf_paths(args_obj)
        if not leaf_paths:
            return ApplyResult(
                status="SKIPPED",
                child_text=seed_text,
                trace={
                    "op_id": OPERATOR_META["op_id"],
                    "status": "SKIPPED",
                    "params": {"strength": strength, "reason": "no_leaf_values", "surface": surface},
                    "len_before": len_before,
                    "len_after": len_before,
                },
            )

        k = min(len(leaf_paths), {1: 1, 2: 1, 3: 2, 4: 3, 5: 4}[strength])
        rng.shuffle(leaf_paths)
        for path in leaf_paths[:k]:
            old = _get_at(args_obj, path)
            new = _mutate_value_preserve_type(old, strength, rng)
            _set_at(args_obj, path, new)
            applied.append(("value_mutate", path))

        # No "parameter swap" here unless it's a dict at top-level
        if strength >= 3 and isinstance(args_obj, dict) and len(args_obj) >= 2 and rng.random() < 0.35:
            keys = list(args_obj.keys())
            a, b = rng.sample(keys, 2)
            args_obj[a], args_obj[b] = args_obj[b], args_obj[a]
            applied.append(("param_swap", (a, b)))

        child_obj = args_obj

    else:
        # surface == TOOL_CALL: expect dict with name + arguments-like field
        if not isinstance(parsed, dict):
            return ApplyResult(
                status="SKIPPED",
                child_text=seed_text,
                trace={
                    "op_id": OPERATOR_META["op_id"],
                    "status": "SKIPPED",
                    "params": {"strength": strength, "reason": "tool_call_not_object", "surface": surface},
                    "len_before": len_before,
                    "len_after": len_before,
                },
            )

        arg_key = _find_args_container(parsed)
        if arg_key is None:
            return ApplyResult(
                status="SKIPPED",
                child_text=seed_text,
                trace={
                    "op_id": OPERATOR_META["op_id"],
                    "status": "SKIPPED",
                    "params": {"strength": strength, "reason": "no_arguments_field", "surface": surface},
                    "len_before": len_before,
                    "len_after": len_before,
                },
            )

        args_obj = parsed[arg_key]
        leaf_paths = _collect_leaf_paths(args_obj)
        if not leaf_paths:
            return ApplyResult(
                status="SKIPPED",
                child_text=seed_text,
                trace={
                    "op_id": OPERATOR_META["op_id"],
                    "status": "SKIPPED",
                    "params": {"strength": strength, "reason": "no_leaf_values", "surface": surface},
                    "len_before": len_before,
                    "len_after": len_before,
                },
            )

        k = min(len(leaf_paths), {1: 1, 2: 1, 3: 2, 4: 3, 5: 4}[strength])
        rng.shuffle(leaf_paths)
        for path in leaf_paths[:k]:
            old = _get_at(args_obj, path)
            new = _mutate_value_preserve_type(old, strength, rng)
            _set_at(args_obj, path, new)
            applied.append(("value_mutate", (arg_key,) + path))

        if strength >= 3 and isinstance(args_obj, dict) and len(args_obj) >= 2 and rng.random() < 0.35:
            keys = list(args_obj.keys())
            a, b = rng.sample(keys, 2)
            args_obj[a], args_obj[b] = args_obj[b], args_obj[a]
            applied.append(("param_swap", (arg_key, a, b)))

        parsed[arg_key] = args_obj
        child_obj = parsed

    child_text = json.dumps(child_obj, ensure_ascii=False)

    if child_text == seed_text:
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

    if isinstance(max_chars, int) and len(child_text) > max_chars:
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
        child_text=child_text,
        trace={
            "op_id": OPERATOR_META["op_id"],
            "status": "OK",
            "params": {
                "strength": strength,
                "mode": "schema_preserving",
                "surface": surface,
                "applied": applied,
            },
            "len_before": len_before,
            "len_after": len(child_text),
        },
    )
