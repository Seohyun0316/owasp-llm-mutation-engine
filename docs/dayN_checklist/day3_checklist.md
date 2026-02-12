# Day 3 Checklist — Closeout

## A. 단위 테스트 하네스
- [x] `registry.load_from_package(..., strict=True)` 로딩 테스트 통과
- [x] 모든 operator에 대해 `apply()`가 빈 문자열에서 크래시 없음
- [x] 모든 operator에 대해 `apply()`가 초장문(예: 200k)에서 크래시 없음
- [x] `ApplyResult.status ∈ {OK, SKIPPED, INVALID}` 보장
- [x] trace 최소 필드(`op_id/status/params/len_before/len_after`) 보장
- [x] `trace.len_after == len(child_text)` 보장

## B. 연산자 자동 등록 방식 확정
- [x] 선택: 패키지 스캔 + 동적 import 방식
- [x] 대상: `src/operators/op_*.py`
- [x] 계약: `OPERATOR_META` + `apply()` 확인
- [x] strict 모드에서 계약 위반은 즉시 실패

## C. Validity Guard (Policy A)
- [x] 엔진 레벨 단일 출구에서 guard 강제 적용
- [x] 길이 제한: `constraints.max_chars` 적용
- [x] 금지 문자: 제어문자 제거(최소 규칙)
- [x] schema_mode placeholder 적용
- [x] mutator 기반 정책 A 테스트 통과

## D. 실행 로그(붙여넣기)
- [x] `python -m pytest -q` 통과
- [x] `python -m pytest -q tests/unit/test_registry_loading.py` 통과
- [x] `python -m pytest -q tests/unit/test_validity_guard.py tests/unit/test_mutator_policy_a.py` 통과
