# Day 4 Done (2026-02-13) — Operator Selection Hook(가중 선택) + Snapshot Harness

본 문서는 Day 4(A) 과제 완료(종결) 기록이다.

## 1. 목표 및 범위
Day 4(A)의 목표는 다음 3개 항목을 “코드 + 테스트”로 완수하는 것이다.

1) Operator Selection Hook 구현(빈 구현이라도 인터페이스 고정)
- 입력: `bucket_id`, `surface`, `stats_by_bucket`
- 출력: `op_id + params`

2) Mutator → Selector.choose(..., stats_by_bucket=...) 파이프 연결

3) Snapshot 테스트 러너(간단) 구현
- 동일 `seed_text/seed_base/strength/constraints`에서 결과가 동일한지 검증
- `UPDATE_SNAPSHOTS=1`로 스냅샷 생성/갱신 지원

## 2. 완료 결과 요약

### 2.1 Hook 인터페이스 고정
- `SelectionDecision`(op_id + params) 및 `SelectionHook.choose(...)` 인터페이스를 코드로 고정하였다.
- 기본 훅 구현을 제공하여(stats 구조 미고정 상태에서도) 실행 가능한 최소 구성을 갖췄다.
- v0.1에서는 기본 훅이 후보 연산자 집합에서 균등 랜덤 선택을 수행한다(빈 구현 수준).

### 2.2 Mutator → Selector 파이프 연결
- `Mutator.generate_children(..., stats_by_bucket=...)`가 `RandomSelector.choose(..., stats_by_bucket=...)`로 통계를 전달한다.
- 선택 정책/통계 로직이 확장되더라도 Mutator/Selector 경계가 깨지지 않도록 인터페이스를 고정하였다.

### 2.3 Snapshot harness(러너) 구현
- `tests/snapshot/test_snapshot_runner.py`에서 스냅샷 러너를 구현하였다.
- `UPDATE_SNAPSHOTS=1` 환경 변수로 스냅샷을 생성/갱신할 수 있다.
- 기본 모드에서는 스냅샷 기대값과 실행 결과가 완전히 동일해야 통과한다(JSON 동등성 비교).

## 3. 테스트 결과(실측)
아래 커맨드에서 모두 `1 passed, ...`를 확인하였다.

- 스냅샷 생성/갱신:
  - `UPDATE_SNAPSHOTS=1 python -m pytest -q -m snapshot`
- 스냅샷 비교 검증:
  - `python -m pytest -q -m snapshot`

(추가로 전체 테스트도 정상 통과하는 상태를 유지한다.)

## 4. 산출물(주요 파일)
- `src/core/selection_hook.py` (SelectionDecision/SelectionHook 및 기본 훅)
- `src/core/selector.py` (hook 기반 선택 경로 연결)
- `src/core/mutator.py` (stats_by_bucket 전달 및 selection 파이프 유지)
- `tests/snapshot/test_snapshot_runner.py` (스냅샷 러너)
- `tests/snapshot/snapshots.json` (스냅샷 케이스/기대값)

## 5. 결론
Day 4(A)는 인터페이스 고정 및 스냅샷 기반 재현성 검증까지 포함하여 종결되었다.  
다음 단계는 Day 4(B) 착수(Formatting/Syntactic 연산자 3종 시작 및 연산자별 스냅샷 최소 5개 추가)로 진행한다.
