# Validity Guard Policy (v0.1)

본 문서는 Mutation Engine 출력의 “깨짐 방지”를 위한 Validity Guard 정책을 정의한다.  
v0.1의 목표는 안정화이므로, Guard는 선택이 아니라 단일 출구(single egress)로 강제 적용한다.

---

## 1) Policy A (확정)

정책 A:

- operator가 무엇을 반환하든(OK/SKIPPED/INVALID),
- 엔진 레벨(예: Mutator)에서 최종 `child_text`에 Guard를 강제 적용한다.

의도:
- 연산자 구현이 미완성/불균일해도 최종 출력은 최소 규칙을 만족한다.
- 렌더링/저장/후속 파이프라인에서 “출력 깨짐”을 예방한다.

---

## 2) Constraints 입력(최소)

Guard는 다음 제약을 사용한다. 제약은 `ctx["constraints"]`로 전달된다.

- `max_chars: int`
  - 최종 문자열의 최대 길이
- `schema_mode: bool`
  - 스키마/리포트 렌더링에서 “빈 문자열”이 위험한 모드
- `placeholder: str`
  - `schema_mode=True`에서 빈 결과를 대체할 문자열(기본 `"N/A"`)

---

## 3) Guard Rules (v0.1 Minimal)

### 3.1 Length cap (truncate)

- `len(text) > max_chars`이면 앞에서부터 truncate한다.
- `max_chars`가 설정되지 않으면 안전한 기본값을 적용한다(구현 기본값).

권장:
- 엔진은 결과 길이가 `max_chars`를 초과하지 않음을 항상 보장한다.

### 3.2 Control characters 제거

- 최소 규칙: ASCII 제어문자(예: `\x00` ~ `\x1F`, `\x7F`)를 제거한다.
- 개행/탭은 유지 가능하다. (렌더러/정책에 따라 확장 가능)

목적:
- JSON 직렬화/렌더링/콘솔 출력 깨짐 방지
- 다운스트림 파서 오류 감소

### 3.3 Schema-mode placeholder

- `schema_mode=True`에서, 최종 결과가 “빈 문자열 또는 공백만”이라면 placeholder로 치환한다.
- placeholder는 `constraints["placeholder"]`를 우선하며 없으면 `"N/A"` 사용.

주의:
- 연산자가 prefix를 붙인 뒤 placeholder가 붙는 형태가 될 수 있다.
- 따라서 테스트에서는 placeholder “완전 일치”가 아니라 “포함/접미” 검증이 더 안정적이다.

---

## 4) 적용 위치(권장/사실상 표준)

v0.1에서는 Mutator에서 Guard 적용을 권장한다.

- seed_text 자체도 Guard 대상이 될 수 있다(빈 seed 방지 등).
- 각 op 적용 이후 intermediate child에도 Guard를 적용할 수 있다.
- 최종 결과는 반드시 Guard를 거친다.

---

## 5) Trace 동기화 규칙

Guard로 최종 child가 변경될 수 있으므로, trace와 최종 결과의 일관성이 필요하다.

권장 규칙:
- Guard로 인해 결과가 변경되면 trace에 아래 중 하나를 남긴다.
  - `notes: "guard_applied"` 또는 `params.reason: "guard_applied"`
- `len_after`는 최종 `child_text` 길이로 동기화한다(최종 단계의 기록 기준).

---

## 6) 완료 정의(검증 기준)

다음이 모두 만족되면 v0.1의 Validity Guard 최소 목표는 “완수”이다.

- 어떠한 입력(빈 문자열/긴 문자열/제어문자 포함)에도 예외 없이 동작한다.
- 최종 `child_text`는 `max_chars`를 절대 초과하지 않는다.
- 제어문자는 최종 결과에서 제거된다.
- `schema_mode=True`에서 빈 결과는 placeholder로 치환된다.
- 관련 unit test 및 snapshot harness에서 결정성을 유지한다.

---

## 7) 최소 테스트 요구사항

- 긴 seed(예: 200k chars) 입력에서 최종 `child_text` 길이 ≤ `max_chars`
- 제어문자 포함 seed에서 최종 결과에 제어문자 없음
- schema_mode=True + 빈 seed에서 placeholder가 반영됨(포함/접미 형태 허용)
