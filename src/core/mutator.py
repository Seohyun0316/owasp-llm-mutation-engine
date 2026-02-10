# src/core/mutator.py
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .operator import ApplyResult
from .registry import OperatorRegistry
from .selector import RandomSelector
from .trace import trace_to_json


def derive_rng(seed_base: int, testcase_id: str) -> random.Random:
    h = hashlib.sha256(f"{seed_base}:{testcase_id}".encode("utf-8")).hexdigest()
    derived_seed = int(h[:8], 16)  # 32-bit
    return random.Random(derived_seed)


@dataclass
class MutationOutput:
    child_text: str
    mutation_trace: List[Dict[str, Any]]
    last_status: str


class Mutator:
    """
    v0.1:
    - selector로 op를 고르고
    - registry.apply로 실행
    - trace 누적
    """

    def __init__(self, registry: OperatorRegistry) -> None:
        self.registry = registry
        self.selector = RandomSelector(registry)

    def generate_children(
        self,
        *,
        seed_text: str,
        bucket_id: str,
        surface: str = "PROMPT_TEXT",
        n: int = 10,
        k: int = 1,  # child 하나당 연산자 적용 횟수
        seed_base: int = 1337,
        strength: int = 2,
        risk_max: Optional[str] = None,
        constraints: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[MutationOutput]:
        outputs: List[MutationOutput] = []
        constraints = constraints or {}
        metadata = metadata or {}

        for i in range(n):
            testcase_id = f"{metadata.get('seed_id','seed')}:{i}"
            rng = derive_rng(seed_base, testcase_id)

            ctx_base = {
                "bucket_id": bucket_id,
                "surface": surface,
                "strength": strength,
                "constraints": constraints,
                "metadata": {**metadata, "testcase_id": testcase_id, "child_index": i},
            }

            child = seed_text
            mtrace: List[Dict[str, Any]] = []
            last_status = "SKIPPED"

            for _ in range(k):
                sel = self.selector.choose(
                    bucket_id=bucket_id,
                    surface=surface,
                    rng=rng,
                    strength=strength,
                    risk_max=risk_max,
                )
                if sel is None:
                    # no operator available
                    mtrace.append(
                        {
                            "op_id": "NO_OP_AVAILABLE",
                            "status": "SKIPPED",
                            "params": {"bucket_id": bucket_id, "surface": surface},
                            "len_before": len(child),
                            "len_after": len(child),
                        }
                    )
                    last_status = "SKIPPED"
                    break

                # ctx에 선택된 params를 반영(기본 strength 외 파라미터 확장 가능)
                ctx = dict(ctx_base)
                ctx.update(sel.params)

                res: ApplyResult = self.registry.apply(sel.op_id, child, ctx, rng)
                mtrace.append(res.trace)
                last_status = res.status

                # SKIPPED/INVALID면 child 유지, OK면 업데이트
                if res.status == "OK":
                    child = res.child_text

            outputs.append(MutationOutput(child_text=child, mutation_trace=mtrace, last_status=last_status))

        return outputs

    @staticmethod
    def pretty_print(outputs: List[MutationOutput]) -> None:
        for idx, o in enumerate(outputs):
            print("=" * 60)
            print(f"[child {idx}] status={o.last_status}")
            print(trace_to_json(o.mutation_trace))
            print("child:")
            print(o.child_text)
