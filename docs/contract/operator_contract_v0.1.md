# Operator Contract (Mutation Engine) v0.1

본 문서는 LLM Greybox Fuzzer의 Mutation Engine에서 사용되는 Mutation Operator의 공통 계약(contract)을 정의한다.  
목표는 다음이다.

- 연산자 구현을 플러그인처럼 독립적으로 추가/교체 가능하게 만든다.
- 동일 입력/동일 RNG seed에 대해 재현 가능한 변이를 보장한다.
- 버킷(OWASP 클래스) 기반 라우팅 및 통계 집계를 가능하게 한다.
- 테스트/스냅샷 기반으로 연산자 품질을 빠르게 검증한다.

---

## 0. Scope & Versioning

- 본 계약 버전은 v0.1이다.
- `apply()` 시그니처, 상태 코드(OK/SKIPPED/INVALID), trace 최소 스키마 변경은 breaking change로 간주한다.
- Breaking change가 발생하면 v0.2 등으로 버전을 올리고, 기존 연산자와의 호환 여부를 명시한다.

---

## 1. 용어

- Seed: 변이의 입력이 되는 프롬프트(원문).
- Child: 변이 결과로 생성된 프롬프트.
- Bucket: OWASP Top 10(LLM Apps) 등의 취약점 클래스 라벨.
- Surface: 프롬프트가 작동하는 표면(plain prompt / tool-call JSON / system-message 등).
- Operator: Seed(또는 중간 결과)에 변형을 적용하는 함수.
- Trace: 어떤 연산자가 어떤 파라미터로 적용되었는지 기록.

---

## 2. Operator Metadata Schema

모든 Operator는 다음 메타데이터를 반드시 제공해야 한다.

### 2.1 `op_id` (필수)

- 문자열 식별자. 레지스트리에서 유일해야 한다.
- 형식 권장: `op_<category>_<name>` (예: `op_lex_whitespace_perturb`)
- 변경 불가 원칙: 동작 의미가 바뀌면 `op_id`를 변경하거나 버전 suffix를 붙인다.  
  예: `op_syn_role_frame_v2`

### 2.2 `bucket_tags[]` (필수)

- 이 연산자가 주로 기여하는 취약점/테스트 버킷 목록(멀티 라벨).
- 예시:
  - `["LLM01_PROMPT_INJECTION"]`
  - `["LLM02_INSECURE_OUTPUT", "LLM06_SENSITIVE_INFO_DISCLOSURE"]`

### 2.3 `surface_compat[]` (필수)

- 이 연산자가 적용 가능한 입력/출력 표면.
- 아래 enum 중 1개 이상을 가진다.
  - `PROMPT_TEXT` : 일반 텍스트 프롬프트
  - `SYSTEM_MESSAGE` : 시스템/개발자 메시지 영역
  - `TOOLCALL_JSON` : tool-call 구조(JSON) 입력
  - `RAG_CONTEXT` : 외부 컨텍스트(문서/검색 결과) 주입 영역
  - `OUTPUT_SHAPING` : 출력 포맷 유도(코드블록/JSON 강제 등)

MVP에서는 `PROMPT_TEXT`만 있어도 된다. 이후 확장 시 surface 기반 필터링을 적용한다.

### 2.4 `risk_level` (필수)

- 연산자가 생성할 수 있는 “위험/민감” 정도를 나타내는 등급.
- enum: `LOW | MEDIUM | HIGH`
- 의미(권장):
  - `LOW`: 포맷/공백/문체 변형 등. 안전 리스크 낮음.
  - `MEDIUM`: 역할 프레이밍/컨텍스트 삽입 등. 정책 우회 시도 포함 가능.
  - `HIGH`: tool-call 조작, 보안상 민감한 페이로드 조립 등. (프로젝트 정책에 따라 제한 가능)

### 2.5 `strength_range` (필수)

- 연산자가 받는 “강도” 파라미터의 범위를 정의한다.
- 형식: `[min, max]` (정수, 권장 1~5)
- 강도 의미는 연산자별로 문서화해야 한다.

### 2.6 `params_schema` (선택, 권장)

- 연산자 파라미터(dict)의 형태를 문서화하기 위한 선택 필드.
- 예시:
  - `{"mode": ["insert", "expand"], "max_inserts": "int"}`

---

## 3. Apply Interface

### 3.1 Function Signature (Python)

연산자는 아래 시그니처를 따른다.

    def apply(seed_text: str, ctx: dict, rng: random.Random) -> "ApplyResult":
        ...

- `seed_text`: 입력 문자열(변이 대상)
- `ctx`: 컨텍스트 딕셔너리(선택/확장 가능)
  - 권장 키:
    - `bucket_id`: 현재 버킷 (예: `LLM01_PROMPT_INJECTION`)
    - `surface`: 현재 surface (예: `PROMPT_TEXT`)
    - `strength`: int (기본 1)
    - `constraints`: dict (길이 제한, 모드, 템플릿 등)
    - `metadata`: dict (예: `seed_id`, `step_id`, `testcase_id` 등)
- `rng`: `random.Random` 인스턴스(재현성 목적)
  - 전역 random 사용 금지. 연산자 내부 난수는 반드시 주입된 `rng`를 사용한다.

---

## 4. Return Type & Status Codes

### 4.1 Return Type: `ApplyResult`

연산자 적용 결과는 아래 구조를 따른다.

    from dataclasses import dataclass
    from typing import Any, Dict, Literal, Optional

    Status = Literal["OK", "SKIPPED", "INVALID"]

    @dataclass
    class ApplyResult:
        status: Status
        child_text: str
        trace: Dict[str, Any]
        error: Optional[str] = None

### 4.2 Status 의미(필수 준수)

- OK
  - 변이 성공.
  - `child_text`는 실제 변이 결과여야 한다.
- SKIPPED
  - 현재 조건에서 적용 불가(예: surface 불일치, 제약상 적용 포기).
  - `child_text`는 원본(`seed_text`) 그대로 반환을 권장한다.
- INVALID
  - 제약/정책 위반 또는 내부 예외로 실패.
  - `child_text`는 원본(`seed_text`) 그대로 반환을 권장한다.
  - `error`에 간단 메시지를 채운다.

---

## 5. Mutation Trace 규격

Mutation Engine은 각 연산자 실행 후 `ApplyResult.trace`를 누적하여 `mutation_trace`를 만든다.

### 5.1 `trace` 최소 필드(필수)

연산자는 아래 필드를 반드시 제공해야 한다.

- `op_id`: string
- `status`: `OK | SKIPPED | INVALID`
- `params`: dict (최소 `{}`라도 포함)
- `len_before`: int
- `len_after`: int

### 5.2 `mutation_trace` 예시

    [
      {
        "op_id": "op_lex_whitespace_perturb",
        "status": "OK",
        "params": {"strength": 2, "mode": "insert"},
        "len_before": 120,
        "len_after": 128
      },
      {
        "op_id": "op_syn_role_frame",
        "status": "SKIPPED",
        "params": {"strength": 1, "frame": "auditor"},
        "len_before": 128,
        "len_after": 128
      }
    ]

### 5.3 Trace 불변 조건

- 적용 순서대로 append(순서 보존).
- 동일 `seed_text` + 동일 `ctx` + 동일 `rng` seed(+ 동일 선택 정책) ⇒ 동일 `mutation_trace` 재현.

---

## 6. 문자열 처리 정책(String Handling Policy)

### 6.1 UTF-8 원칙

- 내부 표현은 Python `str`(유니코드)로 통일한다.
- 파일 I/O나 네트워크 I/O 시에만 UTF-8 인코딩/디코딩을 수행한다.
- 연산자는 바이트(bytes)를 직접 다루지 않는다.

### 6.2 개행/공백 표준화(권장)

Mutation Engine(상위 레벨)에서 seed를 받을 때 아래 정규화를 권장한다.

- 개행 통일: `\r\n` 및 `\r` → `\n`
- 탭 처리: 유지 또는 공백으로 변환 중 하나로 팀 규칙을 고정한다.
- trailing whitespace: 기본 유지(의도적 whitespace 공격을 위해). 단, 제약 모드에서만 제거 가능.

### 6.3 최대 길이 제한

- 제약은 `ctx["constraints"]["max_chars"]`로 전달한다.
- 연산자는 결과가 `max_chars`를 초과하면 아래 중 하나로 처리한다(연산자별로 고정):
  - 옵션 A(권장): SKIPPED 반환(적용을 포기)
  - 옵션 B: INVALID 반환(정책 위반으로 간주)

v0.1 권장: 옵션 A(SKIPPED)

---

## 7. RNG 정책(Reproducibility Policy)

### 7.1 전역 난수 금지

- 연산자 내부에서 `random.random()` 등 전역 RNG 호출 금지.
- 반드시 `apply(..., rng)`로 주입된 `random.Random` 인스턴스를 사용한다.

### 7.2 seed 입력 방식

- Mutation Engine 상위 루프는 `seed_base: int`를 받는다(예: CLI 옵션, config).
- 실행/테스트에서 재현성이 필요하면 `seed_base`를 고정한다.

### 7.3 per-testcase RNG 스코프(필수)

테스트/스냅샷 및 퍼징 실행에서 testcase별로 파생 seed를 만든다.

권장 규칙:
- `testcase_id`를 문자열로 정의(예: `seed_id:child_index` 또는 UUID)
- 파생 seed 생성:
  - `derived_seed = int(sha256(f"{seed_base}:{testcase_id}").hexdigest()[:8], 16)`
  - `rng = random.Random(derived_seed)`

예시(Python):

    import hashlib
    import random

    def derive_rng(seed_base: int, testcase_id: str) -> random.Random:
        h = hashlib.sha256(f"{seed_base}:{testcase_id}".encode("utf-8")).hexdigest()
        derived_seed = int(h[:8], 16)
        return random.Random(derived_seed)

### 7.4 RNG 소비량 정책(권장)

- 선택/변이 모두 단일 rng를 써도 재현은 되지만, 선택 정책 변경 시 결과가 크게 흔들릴 수 있다.
- v0.1 권장:
  - `rng_select`(선택용)과 `rng_mutate`(변이용)를 분리(같은 derived_seed에서 파생).
  - MVP에서는 단일 rng로 시작해도 무방.

---

## 8. Operator Registration 규칙

각 operator 모듈은 다음 형태를 권장한다.

- 파일: `src/operators/op_*.py`
- 모듈 내 공개 객체:
  - `OPERATOR_META` (dict)
  - `apply()` 함수

예시 스켈레톤:

    OPERATOR_META = {
        "op_id": "op_lex_whitespace_perturb",
        "bucket_tags": ["LLM01_PROMPT_INJECTION"],
        "surface_compat": ["PROMPT_TEXT"],
        "risk_level": "LOW",
        "strength_range": [1, 5],
    }

    def apply(seed_text: str, ctx: dict, rng):
        ...

---

## 9. Test Requirements (최소)

- `tests/snapshot/`: 동일 입력 + 동일 rng seed에서 동일 출력 확인
- `tests/unit/`(선택): 빈 문자열/긴 문자열/max_chars에서 안전 동작 확인

---

## 10. Compliance Checklist (PR 리뷰용)

- [ ] `OPERATOR_META` 필수 키 존재(`op_id`, `bucket_tags`, `surface_compat`, `risk_level`, `strength_range`)
- [ ] `apply(seed_text, ctx, rng)` 시그니처 준수
- [ ] 전역 RNG 사용 없음(주입 `rng`만 사용)
- [ ] `ApplyResult.status`가 `OK/SKIPPED/INVALID` 중 하나
- [ ] `trace`에 최소 필드 포함(`op_id/status/params/len_before/len_after`)
- [ ] `max_chars` 제약 처리 일관적(SKIPPED 권장)
- [ ] 스냅샷 테스트 존재(재현성 확인)
