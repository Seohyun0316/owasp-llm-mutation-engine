from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .operator import ApplyResult
from .registry import OperatorRegistry
from .selector import RandomSelector
from .trace import trace_to_json
from .validity_guard import GuardConfig, guard_text


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
    - Policy A: 엔진 레벨에서 Validity Guard를 단일 출구로 강제 적용한다.
    """

    def __init__(self, registry: OperatorRegistry) -> None:
        self.registry = registry
        self.selector = RandomSelector(registry)

    @staticmethod
    def _guard_cfg_from_constraints(constraints: Dict[str, Any]) -> GuardConfig:
        """
        Policy A: constraints -> GuardConfig 매핑을 중앙화한다.
        """
        max_chars = constraints.get("max_chars")
        schema_mode = constraints.get("schema_mode", False)
        placeholder = constraints.get("placeholder", "N/A")

        return GuardConfig(
            max_len=int(max_chars) if isinstance(max_chars, int) and max_chars > 0 else 8000,
            schema_mode=bool(schema_mode),
            placeholder=str(placeholder),
        )

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

        guard_cfg = self._guard_cfg_from_constraints(constraints)

        # (선택) 입력 seed도 동일한 정책으로 한번 정규화할지 여부.
        # Policy A 관점에서는 이게 더 일관적이다.
        seed_text = guard_text(seed_text, guard_cfg)

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

                # --- Policy A: operator 결과는 엔진이 최종 정규화한다 ---
                guarded_child = guard_text(res.child_text, guard_cfg)

                # guard로 child_text가 바뀌면 trace len_after를 동기화하고 notes를 남긴다.
                if guarded_child != res.child_text:
                    res.child_text = guarded_child
                    res.trace["len_after"] = len(res.child_text)
                    res.trace.setdefault("notes", "guard_applied")

                mtrace.append(res.trace)
                last_status = res.status

                # SKIPPED/INVALID면 child 유지, OK면 업데이트
                if res.status == "OK":
                    child = res.child_text
                else:
                    # (선택) OK가 아니어도 child 자체는 항상 guard 상태로 유지한다.
                    # 지금 child는 이미 guard 적용된 seed 또는 이전 OK의 결과이므로 그대로 둔다.
                    pass

            # 최종 출력도 한 번 더 보장(방어적)
            child = guard_text(child, guard_cfg)

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
