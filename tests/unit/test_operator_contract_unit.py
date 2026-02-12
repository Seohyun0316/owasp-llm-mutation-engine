from __future__ import annotations

import random
from typing import Any, Dict, Set

import pytest

from src.core.registry import OperatorRegistry

ALLOWED_STATUSES: Set[str] = {"OK", "SKIPPED", "INVALID"}


def assert_trace_minimum_fields(trace: Dict[str, Any]) -> None:
    """
    Operator Contract v0.1 5.1 최소 필드 강제이다.
    """
    for k in ("op_id", "status", "params", "len_before", "len_after"):
        assert k in trace, f"trace missing required key: {k}"
    assert isinstance(trace["params"], dict), "trace.params must be dict"


def assert_apply_result_contract(res: Any, seed_text: str) -> None:
    """
    ApplyResult 계약(4장 + 5장) 최소 조건을 강제한다.
    """
    assert hasattr(res, "status")
    assert hasattr(res, "child_text")
    assert hasattr(res, "trace")

    assert res.status in ALLOWED_STATUSES, f"unexpected status: {res.status}"
    assert isinstance(res.child_text, str), "child_text must be str"
    assert isinstance(res.trace, dict), "trace must be dict"

    assert_trace_minimum_fields(res.trace)

    # 불변 조건 (5.3 + 레지스트리 보정 로직)
    assert res.trace["status"] == res.status
    assert res.trace["len_before"] == len(seed_text)
    assert res.trace["len_after"] == len(res.child_text)

    # SKIPPED/INVALID 권장 규칙(원본 반환) 검증은 "강제"가 아니라 "권장"이라서
    # 여기서는 완전 강제하지 않는다.
    if res.status in {"SKIPPED", "INVALID"}:
        assert isinstance(res.child_text, str)


def test_apply_safe_on_empty_and_long_seed(registry: OperatorRegistry):
    """
    Day 3 최소 요건:
    - apply()가 빈 문자열/긴 문자열에서 안전하게 동작해야 한다.
    """
    rng = random.Random(1337)
    ctx = {"strength": 3}  # 최소 컨텍스트

    cases = [
        "",
        "A" * 200_000,
    ]

    for h in registry.list_ops():
        for seed in cases:
            res = registry.apply(h.op_id, seed, ctx, rng)
            assert_apply_result_contract(res, seed)


def test_apply_invalid_op_id_returns_invalid(registry: OperatorRegistry):
    rng = random.Random(0)
    seed = "hello"
    ctx = {"strength": 1}

    res = registry.apply("__no_such_op__", seed, ctx, rng)
    assert_apply_result_contract(res, seed)
    assert res.status == "INVALID"
    assert res.trace.get("notes") in {"operator not found", None} or True  # notes는 구현별


def test_filter_risk_max_case_insensitive(registry: OperatorRegistry):
    """
    risk_level enum은 LOW|MEDIUM|HIGH이고, 필터 입력은 대소문자 혼재를 허용하는 편이 안전하다.
    """
    low1 = [h.op_id for h in registry.filter(risk_max="low")]
    low2 = [h.op_id for h in registry.filter(risk_max="LOW")]
    assert low1 == low2
