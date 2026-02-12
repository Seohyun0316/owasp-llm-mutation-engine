from __future__ import annotations

import json
from typing import Any, Dict

import pytest

from src.core.registry import OperatorRegistry
from tests.conftest import derive_rng, save_snapshots


def _stable_json(obj: Any) -> str:
    """
    스냅샷 비교용 직렬화이다.
    key 정렬 + ensure_ascii=False로 안정화한다.
    """
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def test_snapshots_deterministic_outputs(
    registry: OperatorRegistry,
    seed_base: int,
    snapshots: Dict[str, Any],
    snapshot_path,
    update_snapshots: bool,
):
    """
    Operator Contract v0.1 5.3/7.3 재현성 강제이다.
    - 동일 seed_text + 동일 ctx + 동일 derived rng => 동일 child_text/trace(핵심 필드)가 나와야 한다.
    """
    seed_texts = [
        "Hello, world!",
        "",
        "A" * 1000,
        "Please summarize the following text:",
    ]

    # ctx는 재현성에 영향을 주는 최소 키만 사용한다.
    # bucket/surface는 ops별로 mismatch SKIPPED가 나올 수 있어 통일된 값으로 둔다.
    base_ctx = {
        "bucket_id": "LLM01_PROMPT_INJECTION",
        "surface": "PROMPT_TEXT",
        "strength": 3,
        "constraints": {"max_chars": 8000},
        "metadata": {"seed_id": "seed0"},
    }

    updated = dict(snapshots)  # copy

    for op in registry.list_ops():
        for i, seed_text in enumerate(seed_texts):
            testcase_id = f"{op.op_id}:{i}"
            rng = derive_rng(seed_base, testcase_id)

            ctx = dict(base_ctx)
            ctx["metadata"] = dict(base_ctx["metadata"])
            ctx["metadata"]["testcase_id"] = testcase_id

            res = registry.apply(op.op_id, seed_text, ctx, rng)

            # 스냅샷에는 "비교에 필요한 핵심"만 담는다(환경 변화에 민감한 값 최소화).
            payload = {
                "status": res.status,
                "child_text": res.child_text,
                "trace": {
                    "op_id": res.trace.get("op_id"),
                    "status": res.trace.get("status"),
                    "params": res.trace.get("params", {}),
                    "len_before": res.trace.get("len_before"),
                    "len_after": res.trace.get("len_after"),
                },
                "error": res.error,
            }

            key = f"{op.op_id}::case{i}"
            if update_snapshots or key not in updated:
                updated[key] = payload
            else:
                expected = updated[key]
                assert _stable_json(payload) == _stable_json(expected), (
                    f"snapshot mismatch: {key}\n"
                    f"set UPDATE_SNAPSHOTS=1 to update snapshots if intentional."
                )

    if update_snapshots:
        save_snapshots(snapshot_path, updated)
