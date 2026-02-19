from __future__ import annotations

import hashlib
import random


def derive_rng(seed_base: int, testcase_id: str) -> random.Random:
    """
    Deterministic RNG derivation for reproducibility.

    - seed_base: run-level base seed (int)
    - testcase_id: stable identifier per generated child (e.g., "seed0:3")
    """
    if not isinstance(seed_base, int):
        raise TypeError("seed_base must be int")
    if not isinstance(testcase_id, str):
        raise TypeError("testcase_id must be str")

    msg = f"{seed_base}::{testcase_id}".encode("utf-8", errors="strict")
    digest = hashlib.sha256(msg).digest()
    seed_int = int.from_bytes(digest[:8], "big", signed=False)

    return random.Random(seed_int)
