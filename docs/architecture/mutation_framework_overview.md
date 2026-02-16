# Mutation Framework Overview (v0.1)

본 문서는 v0.1 Mutation Framework의 핵심 흐름과 모듈 책임을 요약한다.

---

## 1) High-level Flow

1. Seed prompt를 입력으로 받는다.
2. Registry가 등록된 operator 목록을 유지한다.
3. Selector가 버킷/서피스/리스크 기반으로 후보군(candidates)을 만든다.
4. Selection hook이 후보군에서 `op_id + params`를 선택한다.
5. Registry가 operator를 실행한다(`apply()` 호출).
6. Mutator가 trace를 누적하고 Policy A(Validity Guard)를 단일 출구로 적용한다.
7. 결과 child_text + mutation_trace를 출력한다.

---

## 2) Core Modules

### 2.1 OperatorRegistry

책임:
- `src/operators/op_*.py` 자동 탐색(import) 후 등록
- `OPERATOR_META` 검증/중복 방지
- bucket/surface/risk 기반 필터링
- `apply()` wrapper로 예외 처리 및 trace 최소 필드 보강

I/O:
- 입력: `op_id`, `seed_text`, `ctx`, `rng`
- 출력: `ApplyResult(status, child_text, trace, error?)`

---

### 2.2 Selector (+ Selection Hook)

Selector 책임:
- Registry 필터로 후보군 생성
- Selection hook 호출하여 `op_id + params` 결정

Hook I/O(인터페이스 고정):
- 입력: `bucket_id`, `surface`, `stats_by_bucket`
- 출력: `op_id + params`

v0.1:
- 기본은 균등 랜덤 선택(후속으로 가중/통계 기반 확장)

---

### 2.3 Mutator

책임:
- child 생성 루프(n, k)
- `derive_rng(seed_base, testcase_id)`로 per-testcase 결정성 보장
- Registry.apply 실행 및 trace 누적
- Policy A: Validity Guard 단일 출구 적용
- `MutationOutput(child_text, mutation_trace, last_status)` 반환

---

## 3) Determinism Boundary

결정성은 다음이 모두 고정될 때 보장된다.

- 동일 seed_text/bucket/surface/strength/constraints
- 동일 seed_base 및 testcase_id 생성 규칙
- 동일 hook/selector 정책
- 동일 operator 구현(전역 RNG 금지)
- 동일 guard 정책(Policy A)

Snapshot harness가 이를 검증한다.

---

## 4) Extensibility Points

- Selection hook:
  - stats 기반 가중치, 실패율 패널티, 버킷별 다양성 유지 등으로 확장 가능
- Operators:
  - `op_*.py` 추가만으로 플러그인처럼 확장
- Constraints/Guard:
  - schema mode/금지 패턴/출력 포맷 보호 규칙 확장 가능
