from __future__ import annotations

import random

from src.core.registry import OperatorRegistry


def test_constraints_max_chars_no_crash(registry: OperatorRegistry):
    """
    계약 6.3: max_chars 제약이 들어와도 연산자는 안전하게 처리해야 한다.
    v0.1 권장은 SKIPPED이지만, 연산자 정책에 따라 INVALID도 허용한다.
    """
    rng = random.Random(1337)

    seed = "X" * 50
    ctx = {
        "strength": 5,
        "constraints": {"max_chars": 10},
    }

    for h in registry.list_ops():
        res = registry.apply(h.op_id, seed, ctx, rng)

        assert res.status in {"OK", "SKIPPED", "INVALID"}
        # 제약이 매우 빡세므로 OK가 나오더라도 결과가 제약을 넘기면 안 된다(엔진 레벨에서 가드한다면 여기서 완화 가능)
        # 연산자 자체가 SKIPPED를 선택했다면 원본 유지가 기대된다.
        if res.status == "OK":
            assert len(res.child_text) <= 10, (
                f"{h.op_id} returned OK but child_text exceeds max_chars; "
                "either return SKIPPED/INVALID or enforce constraint."
            )
