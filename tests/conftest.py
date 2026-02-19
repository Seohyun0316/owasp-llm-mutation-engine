from __future__ import annotations

import hashlib
import json
import os
import random
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import pytest

from src.core.registry import OperatorRegistry


def derive_rng(seed_base: int, testcase_id: str) -> random.Random:
    """
    Operator Contract v0.1 7.3의 권장 규칙을 그대로 구현한 RNG 파생이다.
    """
    h = hashlib.sha256(f"{seed_base}:{testcase_id}".encode("utf-8")).hexdigest()
    derived_seed = int(h[:8], 16)  # 32-bit
    return random.Random(derived_seed)


def _iter_loaded_ops(reg: OperatorRegistry) -> List[Any]:
    """
    OperatorRegistry 내부 구현이 무엇이든, 로딩된 operator/meta 객체들을 최대한 추출한다.
    - op 객체는 최소한 op_id(문자열) 속성을 가진다고 가정한다.
    """
    # 1) 흔한 내부 dict 이름들 시도
    for attr in ("_operators", "operators", "_ops", "_by_id", "by_id"):
        d = getattr(reg, attr, None)
        if isinstance(d, dict) and d:
            return list(d.values())

    # 2) 흔한 getter 메서드 이름들 시도
    for meth in ("list_all", "all", "iter_all", "get_all", "operators_list"):
        fn = getattr(reg, meth, None)
        if callable(fn):
            try:
                out = fn()
                if isinstance(out, dict):
                    return list(out.values())
                if isinstance(out, Iterable):
                    return list(out)
            except Exception:
                pass

    raise RuntimeError(
        "Could not extract loaded operators from OperatorRegistry. "
        "Please expose a method like list_all() or an internal dict of operators."
    )


def _reset_registry_from_ops(reg: OperatorRegistry, ops: List[Any]) -> OperatorRegistry:
    """
    reg를 op_id 순서로 재구성한다.
    - registry 구현에 따라 내부 dict를 재설정하거나, 새 registry에 재등록한다.
    """
    ops_sorted = sorted(ops, key=lambda o: getattr(o, "op_id", ""))

    # 1) 새 레지스트리를 만들어 재등록 시도(가장 깔끔)
    new_reg = OperatorRegistry()

    # register() 메서드가 있는지 먼저 시도
    register = getattr(new_reg, "register", None)
    if callable(register):
        for op in ops_sorted:
            register(op)
        return new_reg

    # 2) register가 없으면, 내부 dict를 직접 세팅(최후 수단)
    # 내부 dict 후보들 중 하나에 op_id->op 형태로 심는다.
    mapping = {getattr(op, "op_id"): op for op in ops_sorted}

    for attr in ("_operators", "operators", "_ops", "_by_id", "by_id"):
        d = getattr(new_reg, attr, None)
        if isinstance(d, dict) or d is None:
            setattr(new_reg, attr, dict(mapping))
            return new_reg

    raise RuntimeError(
        "Could not rebuild OperatorRegistry deterministically. "
        "Please add OperatorRegistry.register(op) or expose an internal dict."
    )


@pytest.fixture(scope="session")
def seed_base() -> int:
    """
    스냅샷/단위테스트에서 사용하는 고정 base seed이다.
    """
    return 1337


@pytest.fixture(scope="session")
def registry() -> OperatorRegistry:
    """
    strict=True로 로딩하여 계약 위반은 즉시 실패시키는 구성이다.

    추가:
    - load_from_package()의 모듈 탐색/등록 순서가 비결정적인 경우가 있어,
      테스트에서는 로딩 후 op_id 기준으로 정렬해 registry를 결정론적으로 재구성한다.
    """
    reg = OperatorRegistry()
    reg.load_from_package("src.operators", strict=True)

    # --- 결정론 강제: op_id 기준 정렬 ---
    ops = _iter_loaded_ops(reg)
    reg = _reset_registry_from_ops(reg, ops)
    return reg

@pytest.fixture(scope="function")
def registry_fresh() -> OperatorRegistry:
    """
    Snapshot과 같이 '완전 결정론'이 필요한 테스트에서 사용.
    다른 테스트가 session-scope registry를 오염시키는 문제를 차단하기 위해
    매 테스트 호출마다 fresh registry를 만든다.
    """
    reg = OperatorRegistry()
    reg.load_from_package("src.operators", strict=True)
    return reg


@pytest.fixture(scope="session")
def snapshot_path() -> Path:
    return Path(__file__).parent / "snapshot" / "snapshots.json"


@pytest.fixture(scope="session")
def snapshots(snapshot_path: Path) -> Dict[str, Any]:
    if not snapshot_path.exists():
        return {}
    return json.loads(snapshot_path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def update_snapshots() -> bool:
    """
    UPDATE_SNAPSHOTS=1 이면 스냅샷을 갱신한다.
    """
    return os.getenv("UPDATE_SNAPSHOTS", "") in {"1", "true", "TRUE", "yes", "YES"}


def save_snapshots(snapshot_path: Path, data: Dict[str, Any]) -> None:
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
