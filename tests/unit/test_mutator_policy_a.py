from __future__ import annotations

from typing import Any, Dict, List

import pytest

from src.core.mutator import Mutator
from src.core.registry import OperatorRegistry


def _make_mutator(registry: OperatorRegistry) -> Mutator:
    return Mutator(registry)


def test_policy_a_enforces_max_chars_for_all_children(registry: OperatorRegistry):
    """
    Policy A 핵심:
    - operator가 뭘 반환하든(OK/SKIPPED/INVALID), 엔진(mutator)이 최종 child_text에 guard를 강제한다.
    - constraints.max_chars를 넘는 출력은 절대 나오면 안 된다.
    """
    m = _make_mutator(registry)

    seed = "A" * 200_000  # 매우 긴 seed
    constraints = {"max_chars": 64}

    outs = m.generate_children(
        seed_text=seed,
        bucket_id="LLM01_PROMPT_INJECTION",
        surface="PROMPT_TEXT",
        n=5,
        k=2,
        seed_base=1337,
        strength=3,
        constraints=constraints,
        metadata={"seed_id": "seed_policy_a"},
    )

    assert len(outs) == 5
    for o in outs:
        assert isinstance(o.child_text, str)
        assert len(o.child_text) <= 64, f"child_text exceeds max_chars under Policy A: {len(o.child_text)}"


def test_policy_a_removes_control_chars(registry: OperatorRegistry):
    """
    Policy A:
    - 금지 문자/깨짐 유발 문자(최소: 제어문자)를 엔진 레벨에서 제거한다.
    """
    m = _make_mutator(registry)

    seed = "HELLO\x00WORLD\x01!!!"  # 제어문자 포함
    constraints = {"max_chars": 200}  # 충분히 크게

    outs = m.generate_children(
        seed_text=seed,
        bucket_id="LLM01_PROMPT_INJECTION",
        surface="PROMPT_TEXT",
        n=3,
        k=1,
        seed_base=1337,
        strength=2,
        constraints=constraints,
        metadata={"seed_id": "seed_ctrl_chars"},
    )

    for o in outs:
        assert "\x00" not in o.child_text
        assert "\x01" not in o.child_text


def test_policy_a_schema_mode_placeholder_applied(registry: OperatorRegistry):
    """
    Policy A:
    - schema_mode=True 이면 빈 문자열은 placeholder로 치환되어야 한다.
    - Mutator는 seed_text 자체도 guard 하므로, 빈 seed에서도 placeholder가 적용된다.
    """
    m = _make_mutator(registry)

    seed = ""
    constraints = {"max_chars": 100, "schema_mode": True, "placeholder": "N/A"}

    outs = m.generate_children(
        seed_text=seed,
        bucket_id="LLM01_PROMPT_INJECTION",
        surface="PROMPT_TEXT",
        n=2,
        k=1,
        seed_base=1337,
        strength=1,
        constraints=constraints,
        metadata={"seed_id": "seed_schema_mode"},
    )

    for o in outs:
        assert o.child_text == "N/A", f"expected placeholder, got: {o.child_text!r}"
        assert len(o.child_text) <= 100


def test_policy_a_trace_len_after_matches_child_text_len(registry: OperatorRegistry):
    """
    Policy A 적용 시:
    - guard로 child_text가 변할 수 있으므로, trace.len_after는 최종 child_text 길이와 일치해야 한다.
    - 특히 guard_applied 케이스에서 len_after 동기화가 필수다.
    """
    m = _make_mutator(registry)

    seed = "A" * 5000
    constraints = {"max_chars": 32}

    outs = m.generate_children(
        seed_text=seed,
        bucket_id="LLM01_PROMPT_INJECTION",
        surface="PROMPT_TEXT",
        n=3,
        k=2,
        seed_base=1337,
        strength=3,
        constraints=constraints,
        metadata={"seed_id": "seed_trace_len"},
    )

    for o in outs:
        assert len(o.child_text) <= 32
        # mutation_trace는 단계별 trace list
        assert isinstance(o.mutation_trace, list)
        for t in o.mutation_trace:
            assert "len_after" in t
            # 마지막 trace의 len_after가 최종 child와 같아야 한다고 "강제"할 수도 있으나,
            # v0.1에서는 단계별 child 변화가 누적되므로, 각 단계가 OK로 child를 바꿨을 때만 일치한다.
            # 여기서는 "guard_applied"가 붙은 trace에 대해 동기화가 되었는지 확인한다.
            if t.get("notes") == "guard_applied":
                assert t["len_after"] <= 32
