# Day 3 Done (2026-02-12) — 테스트 하네스 + Operator Registry 안정화

본 문서는 Day 3 과제 완료(종결) 기록이다.

## 1. 목표 및 범위
Day 3의 목표는 다음 3개 항목을 “코드 + 테스트”로 완수하는 것이다.

1) 단위 테스트 하네스 구축  
- 최소: `apply()`가 빈 문자열/긴 문자열에서 안전하게 동작

2) “연산자 자동 등록” 방식 확정  
- 정적 배열 등록 vs 매크로 등록 vs 링크 타임 등록 중 택1

3) Validity Guard(최소 규칙) 구현  
- 길이 제한, 금지 문자/패턴 처리(필요 시), 스키마 모드 placeholder

## 2. 완료 결과 요약

### 2.1 단위 테스트 하네스 구축
- Registry 기반 `apply()` 안정성 검증 테스트를 구축하였다.
- 빈 문자열/긴 문자열에서 예외 없이 `ApplyResult` 반환을 보장한다.
- `ApplyResult.trace` 최소 필드 및 `len_after == len(child_text)` 일치가 검증된다.

검증 명령:
- `python -m pytest -q`
- `python -m pytest -q tests/unit/test_registry_loading.py`

### 2.2 연산자 자동 등록 방식 확정
- 확정 방식: **패키지 스캔 + 동적 import(autoload) 기반 Registry**
- `src/operators/op_*.py` 모듈을 자동 탐색하여 `OPERATOR_META` + `apply()`를 등록한다.
- strict 로딩 모드에서 계약 위반은 즉시 실패하도록 구성하였다.

근거:
- Operator 플러그인 추가/교체를 파일 추가만으로 수행 가능하다.
- 빌드/링크 과정에 의존하지 않고 Python 런타임에서 결정적으로 로딩 가능하다.
- CI에서 strict 로딩으로 계약 위반을 조기 차단할 수 있다.

검증 명령:
- `python -m pytest -q tests/unit/test_registry_loading.py`

### 2.3 Validity Guard(정책 A) 구현
- 정책 A로 확정: **엔진 레벨 단일 출구에서 Guard 강제 적용**이다.
- 길이 제한(`constraints.max_chars`), 제어문자 제거, 스키마 모드 placeholder를 통일적으로 보장한다.
- Mutator 레벨에서 Policy A가 검증된다.

검증 명령:
- `python -m pytest -q tests/unit/test_validity_guard.py tests/unit/test_mutator_policy_a.py`

## 3. 테스트 결과(실측)
- `python -m pytest -q` → 14 passed
- `python -m pytest -q tests/unit/test_registry_loading.py` → 2 passed
- `python -m pytest -q tests/unit/test_validity_guard.py tests/unit/test_mutator_policy_a.py` → 7 passed

## 4. 산출물(주요 파일)
- `src/core/registry.py` (autoload registry + strict 로딩)
- `src/core/mutator.py` (Policy A 엔진 가드 적용 지점)
- `src/core/validity_guard.py` (GuardConfig/guard_text/is_text_valid)
- `tests/unit/test_registry_loading.py`
- `tests/unit/test_operator_contract_unit.py`
- `tests/unit/test_constraints_max_chars.py`
- `tests/unit/test_validity_guard.py`
- `tests/unit/test_mutator_policy_a.py`
- (선택) `tests/snapshot/*` (재현성 스냅샷)

## 5. 결론
Day 3 과제는 테스트로 검증된 형태로 종결되었다.
다음 단계는 Day 4(operators 확장, snapshot 고도화, selector/energy 정책 강화 등)로 진행한다.
