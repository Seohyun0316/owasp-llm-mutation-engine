# Add Operator (v0.1)

새 Mutation Operator를 추가하는 표준 절차이다.

---

## 1) File Layout

- 파일명 규칙: `src/operators/op_*.py`
- 모듈 공개 객체:
  - `OPERATOR_META` (dict)
  - `apply(seed_text: str, ctx: dict, rng: random.Random) -> ApplyResult`

Registry는 `src.operators` 아래의 `op_*.py`를 자동 탐색하여 등록한다.

---

## 2) Minimal Skeleton

다음 형태를 최소로 만족해야 한다.

    from __future__ import annotations
    import random
    from typing import Any, Dict
    from src.core.operator import ApplyResult

    OPERATOR_META = {
        "op_id": "op_lex_example",
        "bucket_tags": ["LLM01_PROMPT_INJECTION"],
        "surface_compat": ["PROMPT_TEXT"],
        "risk_level": "LOW",
        "strength_range": [1, 5],
    }

    def apply(seed_text: str, ctx: Dict[str, Any], rng: random.Random) -> ApplyResult:
        strength = int(ctx.get("strength", 1))
        child = seed_text + " " + ("!" * min(strength, 5))

        return ApplyResult(
            status="OK",
            child_text=child,
            trace={
                "op_id": OPERATOR_META["op_id"],
                "status": "OK",
                "params": {"strength": strength},
                "len_before": len(seed_text),
                "len_after": len(child),
            },
        )

---

## 3) Contract Checklist (PR 필수)

- `OPERATOR_META` 필수 키 존재
  - `op_id`, `bucket_tags`, `surface_compat`, `risk_level`, `strength_range`
- `apply(seed_text, ctx, rng)` 시그니처 준수
- 전역 RNG 사용 없음(주입된 rng만 사용)
- status는 `OK/SKIPPED/INVALID` 중 하나
- trace 최소 필드 포함
  - `op_id`, `status`, `params`, `len_before`, `len_after`

---

## 4) Testing Requirements

### 4.1 Unit Tests (권장)

- 빈 문자열에서 안전 동작
- 매우 긴 문자열에서 안전 동작
- `constraints.max_chars` 강제 상황에서 Policy A Guard로 최종 결과 길이 보장

### 4.2 Snapshot Tests (권장)

연산자당 최소 5개 케이스를 `tests/snapshot/snapshots.json`에 추가한다.

권장 케이스 유형:

- 짧은 seed(정상)
- 공백/개행 포함 seed
- 빈 문자열 seed(가능하면)
- 길이 제한(max_chars 작은 값)
- strength 경계값(1, 5)

---

## 5) Common Pitfalls

- 전역 random 사용: 결정성 깨짐(스냅샷 불일치)
- trace 필드 누락: 집계/렌더링 깨짐
- output 폭증: Guard가 truncate하긴 하지만, 연산자 자체가 비정상적으로 길이를 키우지 않도록 한다.
