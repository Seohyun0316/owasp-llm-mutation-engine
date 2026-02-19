from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List

import pytest

from src.core.mutator import Mutator
from src.core.registry import OperatorRegistry


SNAPSHOT_PATH = Path("tests/snapshot/snapshots.json")


def _canon(obj: Any) -> Any:
    """
    Snapshot용 canonicalization.

    - dict: key 정렬 + 재귀
    - list: 기본 순서 유지(재귀만), 단 params.applied는 정렬
    """
    if isinstance(obj, dict):
        out = {k: _canon(v) for k, v in obj.items()}

        params = out.get("params")
        if isinstance(params, dict) and isinstance(params.get("applied"), list):
            applied = params["applied"]

            def key(x: Any):
                if isinstance(x, list) and len(x) >= 3:
                    a0 = str(x[0])
                    a1 = x[1]
                    try:
                        a1 = int(a1)
                    except Exception:
                        a1 = str(a1)
                    a2 = str(x[2])
                    return (a0, a2, a1)
                return (str(type(x)), str(x))

            try:
                params["applied"] = sorted((_canon(x) for x in applied), key=key)
            except Exception:
                params["applied"] = [_canon(x) for x in applied]
            out["params"] = params

        return {k: out[k] for k in sorted(out.keys())}

    if isinstance(obj, list):
        return [_canon(x) for x in obj]

    return obj


def _stable_json(x: Any) -> str:
    """
    파이썬 객체 동등성(==/!=) 대신, canonical JSON 문자열로 비교한다.
    - sort_keys=True + separators로 문자열을 완전 결정론적으로 만든다.
    - allow_nan=False로 비표준 값이 끼면 즉시 예외로 잡는다.
    """
    return json.dumps(
        _canon(x),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


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
        # in-place 오염 방지
        stats_by_bucket=deepcopy(case.get("stats_by_bucket") or {}),
    )

    got = {
        "outputs": [
            {
                "child_text": o.child_text,
                "last_status": o.last_status,
                "mutation_trace": _canon(o.mutation_trace),
            }
            for o in outs
        ]
    }

    # outputs 순서가 흔들릴 가능성도 제거(안전)
    got["outputs"] = sorted(
        got["outputs"],
        key=lambda o: (o.get("child_text", ""), o.get("last_status", "")),
    )

    return _canon(got)


@pytest.mark.snapshot
def test_snapshot_harness_deterministic(registry_fresh: OperatorRegistry):
    """
    Day4 Snapshot harness:
    - 동일 seed_text/seed_base/strength 등에서 결과가 항상 동일함을 검증한다.
    - UPDATE_SNAPSHOTS=1이면 expectations를 갱신한다.
    """
    data = _load_snapshots()
    cases: List[Dict[str, Any]] = data.get("cases", [])
    assert isinstance(cases, list) and len(cases) > 0, "snapshots.json must contain at least 1 case"

    update = os.getenv("UPDATE_SNAPSHOTS", "") in {"1", "true", "TRUE", "yes", "YES"}

    new_cases: List[Dict[str, Any]] = []
    failures: List[str] = []

    for case in cases:
        case_id = case.get("case_id", "<missing>")
        expect = case.get("expect")
        got = _run_case(registry_fresh, case)

        if update or expect is None:
            c2 = dict(case)
            c2["expect"] = got
            new_cases.append(c2)
            continue

        # ✅ 핵심: 파이썬 객체 비교 대신 stable JSON 문자열 비교
        if _stable_json(got) != _stable_json(expect):
            safe_id = "".join(c if c.isalnum() or c in "-_." else "_" for c in case_id)
            Path(f"tests/snapshot/_expect_{safe_id}.json").write_text(
                json.dumps(_canon(expect), ensure_ascii=False, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            Path(f"tests/snapshot/_got_{safe_id}.json").write_text(
                json.dumps(_canon(got), ensure_ascii=False, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            failures.append(case_id)

        # update=False에서도 new_cases 유지(나중에 update 저장 안전)
        new_cases.append(case)

    if update:
        _save_snapshots({"cases": new_cases})

    assert not failures, f"snapshot mismatch cases: {failures}"
