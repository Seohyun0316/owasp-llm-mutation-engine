# RNG & Determinism Policy (v0.1)

본 문서는 Mutation Framework의 재현성(결정성) 정책을 정의한다.

---

## 1) Goal

동일한 입력 조건에서 동일한 결과를 얻는 것이 목표다.

- 동일 seed_text
- 동일 bucket_id, surface, strength
- 동일 seed_base
- 동일 constraints, metadata 규칙(특히 testcase_id 생성 방식)
- 동일 선택 정책(Selection hook 포함)
- 동일 코드 버전(동일 커밋/태그)
- ⇒ 동일 child_text 및 동일 mutation_trace

---

## 2) Core Rule: 전역 RNG 금지

연산자(operator) 구현은 아래를 금지한다.

- `random.random()`, `random.choice()` 등 전역 RNG 호출 금지

허용/필수:

- `apply(..., rng: random.Random)`로 주입된 rng만 사용

동일 원칙은 selector/hook에도 적용된다.

---

## 3) Per-testcase RNG derivation (v0.1)

v0.1 권장 규칙:

- testcase_id를 문자열로 정의한다.
  - 예: `"{seed_id}:{child_index}"`

- derived_seed:
  - `derived_seed = int(sha256(f"{seed_base}:{testcase_id}").hexdigest()[:8], 16)`
- rng:
  - `rng = random.Random(derived_seed)`

예시:

    import hashlib
    import random

    def derive_rng(seed_base: int, testcase_id: str) -> random.Random:
        h = hashlib.sha256(f"{seed_base}:{testcase_id}".encode("utf-8")).hexdigest()
        derived_seed = int(h[:8], 16)
        return random.Random(derived_seed)

효과:
- child_index마다 독립 seed가 생성되어, n개의 child를 만들어도 결정성이 유지된다.

---

## 4) Selection Hook RNG 사용

Selection hook / selector는 결정성에 민감하다.

원칙:
- hook은 “주입된 rng”만 사용한다.
- 후보군(candidates)의 순서는 안정적이어야 한다(정렬 등으로 고정).

권장:
- 후보군 list를 op_id 기준 정렬 후 선택한다.
- hook이 weights를 사용한다면, weights 계산도 입력(stats_by_bucket 등)에 의해 결정적으로 수행한다.

---

## 5) Snapshot Harness가 최종 게이트

결정성 회귀는 snapshot harness로 검출한다.

- 의도된 변경: 스냅샷 갱신(UPDATE_SNAPSHOTS=1)
- 의도치 않은 변경: 전역 RNG, 후보군 순서 불안정, 환경 의존 문자열 처리 등을 점검한다.

---

## 6) Determinism breaks: 대표 원인

- 연산자 내부 전역 RNG 사용
- rng 호출 횟수/순서가 코드 변경으로 바뀜(특히 조건 분기)
- 후보군 순서가 import 순서/OS에 따라 달라짐
- Guard 정책 변경으로 최종 문자열이 달라짐
- snapshot 케이스의 metadata/testcase_id 규칙이 바뀜

---

## 7) 최소 검증 기준

다음 조건이 만족되면 v0.1 결정성 목표는 “완수”이다.

- 동일 seed_base/testcase_id에서 selector/hook 결과가 동일
- 동일 input에서 Mutator 출력(child_text, mutation_trace)이 동일
- snapshot harness가 기본 모드에서 통과
