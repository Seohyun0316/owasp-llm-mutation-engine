from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

import pytest

from src.core.mutator import Mutator
from src.core.registry import OperatorRegistry


SNAPSHOT_PATH = Path("tests/snapshot/snapshots.json")


def _load_snapshots() -> Dict[str, Any]:
    if not SNAPSHOT_PATH.exists():
        return {"cases": []}
    with SNAPSHOT_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_snapshots(data: Dict[str, Any]) -> None:
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SNAPSHOT_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)


def _run_case(registry: OperatorRegistry, case: Dict[str, Any]) -> Dict[str, Any]:
    m = Mutator(registry)

    outs = m.generate_children(
        seed_text=case["seed_text"],
        bucket_id=case["bucket_id"],
        surface=case.get("surface", "PROMPT_TEXT"),
        n=int(case.get("n", 3)),
        k=int(case.get("k", 1)),
        seed_base=int(case.get("seed_base", 1337)),
        strength=int(case.get("strength", 2)),
        risk_max=case.get("risk_max"),
        constraints=case.get("constraints") or {},
        metadata=case.get("metadata") or {},
        stats_by_bucket=case.get("stats_by_bucket") or {},
    )

    # 스냅샷은 "결과 텍스트"와 "마지막 status"와 "trace"를 그대로 저장(간단 버전)
    return {
        "outputs": [
            {
                "child_text": o.child_text,
                "last_status": o.last_status,
                "mutation_trace": o.mutation_trace,
            }
            for o in outs
        ]
    }


@pytest.mark.snapshot
def test_snapshot_harness_deterministic(registry: OperatorRegistry):
    """
    Day4 Snapshot harness:
    - 동일 seed_text/seed_base/strength 등에서 결과가 항상 동일함을 검증한다.
    - UPDATE_SNAPSHOTS=1이면 expectations를 갱신한다.
    """
    data = _load_snapshots()
    cases: List[Dict[str, Any]] = data.get("cases", [])
    assert isinstance(cases, list) and len(cases) > 0, "snapshots.json must contain at least 1 case"

    update = os.environ.get("UPDATE_SNAPSHOTS", "") == "1"

    new_cases: List[Dict[str, Any]] = []
    failures: List[str] = []

    for case in cases:
        case_id = case.get("case_id", "<missing>")
        expect = case.get("expect")

        got = _run_case(registry, case)

        if update or expect is None:
            case = dict(case)
            case["expect"] = got
            new_cases.append(case)
            continue

        # 비교: 간단히 JSON 동등성 비교(정확히 동일해야 통과)
        if got != expect:
            failures.append(case_id)
        new_cases.append(case)

    if update:
        _save_snapshots({"cases": new_cases})

    assert not failures, f"snapshot mismatch cases: {failures}"
