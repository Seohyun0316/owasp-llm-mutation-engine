# Snapshots (v0.1)

Snapshot harness는 “결정성(determinism)”을 자동 검증한다.

- 동일 seed_text, bucket_id, surface, seed_base, strength, constraints, metadata 규칙
- 동일 코드 버전 및 선택 정책(hook 포함)
- ⇒ 동일 child_text 및 동일 mutation_trace

---

## 1) Where

- 테스트: `tests/snapshot/test_snapshot_runner.py`
- 데이터: `tests/snapshot/snapshots.json`

---

## 2) Snapshot File Format

`snapshots.json`은 다음 구조를 가진다.

- `cases[]`: 입력 파라미터와 기대 결과(expect)를 포함한다.
- `expect`는 runner가 생성한 결과를 저장한다.

권장 스키마:

- `case_id`: string (유일)
- `seed_text`: string
- `bucket_id`: string
- `surface`: string
- `n`: int
- `k`: int
- `seed_base`: int
- `strength`: int
- `constraints`: dict
- `metadata`: dict
- `stats_by_bucket`: dict (선택 hook 입력)
- `expect`: dict (runner가 채움)

---

## 3) Generate / Update

### 3.1 생성/갱신

PowerShell:

    $env:UPDATE_SNAPSHOTS="1"
    python -m pytest -q -m snapshot
    Remove-Item Env:\UPDATE_SNAPSHOTS

### 3.2 비교 모드

    python -m pytest -q -m snapshot

---

## 4) When to Update

갱신이 정상인 상황:

- 연산자 로직이 의도적으로 변경됨
- selection hook 정책이 변경됨(가중치/후보군/tie-breaker)
- Validity Guard 정책이 변경됨(truncate/placeholder/금지문자 규칙)

갱신이 위험 신호인 상황:

- 전역 RNG 사용 또는 비결정적 요소 혼입
- 후보군 순서가 환경(OS/import)에 따라 달라짐
- 테스트 입력(metadata/testcase_id 규칙)이 무심코 바뀜

---

## 5) Debugging Mismatch

1) 어떤 케이스(case_id)가 실패했는지 확인한다.
2) 해당 케이스의 입력 파라미터를 그대로 복사하여 Mutator 단독 실행을 한다.
3) `mutation_trace`를 비교해 divergence step을 찾는다.

대표 체크리스트:

- 연산자 내부 전역 RNG 호출이 없는가?
- 후보군 리스트가 op_id 기준으로 정렬되는가?
- hook이 stats_by_bucket를 결정적으로 해석하는가?
- Guard가 적용된 경우 trace의 len_after가 최종 문자열 길이로 동기화되는가?

---

## 6) Best Practices

- 케이스는 짧게(n, k 작게) 유지한다. 테스트는 빨라야 한다.
- 연산자별로 최소 5개 케이스를 둔다(경계값 포함).
- Guard 관련 케이스는 반드시 포함한다:
  - `max_chars` 작은 케이스
  - 제어문자 포함 seed
  - `schema_mode=True` placeholder 반영 케이스
