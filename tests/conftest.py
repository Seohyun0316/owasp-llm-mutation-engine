from __future__ import annotations

import hashlib
import json
import os
import random
from pathlib import Path
from typing import Any, Dict, Iterator, Tuple

import pytest

from src.core.registry import OperatorRegistry


def derive_rng(seed_base: int, testcase_id: str) -> random.Random:
    """
    Operator Contract v0.1 7.3의 권장 규칙을 그대로 구현한 RNG 파생이다.
    """
    h = hashlib.sha256(f"{seed_base}:{testcase_id}".encode("utf-8")).hexdigest()
    derived_seed = int(h[:8], 16)  # 32-bit
    return random.Random(derived_seed)


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
