# Day6 Done: operator_stats_by_bucket update API + logging format v0.1

## Scope
Day6 목표는 다음 2가지를 종결하는 것이다.

1) operator_stats_by_bucket 업데이트 API 구현
- API: report_result(bucket_id, op_id, verdict, oracle_score)

2) 결과 로그 포맷 확정(후속 분석 가능)
- schema_version을 포함한 JSON 포맷 고정
- 저장 경로/규칙 문서화

---

## Changes

### Code
- Added `src/core/operator_stats.py`
  - `OperatorStatsByBucket.report_result(...)`:
    - verdict 정규화(PASS/FAIL/UNKNOWN)
    - oracle_score float 변환 시도 + 0..1 clamp
    - 어떤 입력에도 예외 없이 업데이트(최소 안정형)
  - `OperatorStatsByBucket.snapshot()`:
    - 직렬화 가능한 dict 형태 스냅샷
  - `OperatorStatsByBucket.dump_json(path)`:
    - `operator_stats_by_bucket.v0.1` 로그 파일 저장

### Tests
- Added `tests/unit/test_operator_stats_by_bucket.py`
  - report_result 업데이트 동작 검증
  - bad inputs에 대한 robustness 검증
  - snapshot 직렬화 shape 검증

### Docs
- Added `docs/policies/policy_operator_stats_logging_v0.1.md`
  - 로그 포맷/필드/저장 규칙을 v0.1로 확정
- Added `docs/examples/operator_stats_by_bucket.v0.1.example.json`
  - 확정 포맷 예시 제공

---

## Verification

### Unit Test
- `python -m pytest -q tests/unit/test_operator_stats_by_bucket.py`
  - Result: 3 passed

### Log Format
- `OperatorStatsByBucket.dump_json("out/stats/operator_stats_by_bucket.v0.1.json")`로 저장 시
  - schema_version + generated_at + stats(snapshot) 구조가 유지됨
  - downstream 분석(Python/JS)에서 JSON load 후 바로 사용 가능

---

## Notes / Follow-ups
- 스레드 안전성(락), 영속 저장 주기, 파일 로테이션은 Day6 범위 밖이며 필요 시 후속 Day로 확장한다.
- selector/selection_hook에서 stats를 가중치로 활용하는 전략은 Day7(또는 다음 단계)에서 진행한다.
