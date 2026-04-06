
# mutation_seed_v1

## 1. 목적

`mutation_seed_v1`은 `normalized_v1` 레코드 중, Mutation Engine의 입력으로 실제 사용 가능한 레코드만 추려서 저장하는 시드 스키마이다.

이 스키마의 목적은 다음과 같다.

1. 어떤 텍스트를 mutation 대상으로 사용할지 명시한다.
2. 해당 시드가 어떤 OWASP/LLM bucket에 속하는지 표시한다.
3. attack surface와 mutation target role을 명확히 하여 operator selection과 execution input 생성을 돕는다.
4. 원본 정규화 정보와 Mutation Engine용 필드를 함께 보존한다.

---

## 2. 레코드 단위

- 저장 형식: JSON Lines (`.jsonl`)
- 한 줄 = 한 개의 mutation seed 레코드

---

## 3. 설계 원칙

### 3.1 `normalized_v1`의 확장형
`mutation_seed_v1`은 `normalized_v1` 공통 필드를 유지하되, Mutation Engine용 필드를 추가한 형태로 본다.

### 3.2 mutation 가능성 명시
모든 normalized record가 mutation seed가 되는 것은 아니므로, 어떤 텍스트가 실제 mutation target인지 분리한다.

### 3.3 bucket 중심 운용
operator routing과 coverage 측정을 위해 bucket 정보는 상위 필드로 승격한다.

---

## 4. 상속 필드

아래 필드는 `normalized_v1`에서 그대로 유지한다.

- `record_id`
- `dataset_name`
- `subset_or_split`
- `input_primary`
- `input_secondary`
- `context_text`
- `candidate_output`
- `reference_output`
- `label_binary`
- `category_primary`
- `category_multilabel_json`
- `metadata_json`
- `raw_json`

> **Open Decision**  
> 저장 중복을 줄이기 위해 `mutation_seed_v1`에서 일부 필드를 생략할지, 아니면 `normalized_v1` 필드를 전부 유지할지는 최종 구현 기준으로 확정해야 한다.  
> 현재 프로젝트 흐름상 전부 유지하는 편이 추적성에 유리하다.

---

## 5. Mutation Engine 전용 필드

### 5.1 `bucket_tags`
- 타입: `array[string]`
- Required: Yes
- 설명:
  - 이 시드가 속하는 OWASP/LLM 계열 bucket 목록
- 예시:
  - `["LLM01_PROMPT_INJECTION"]`

---

### 5.2 `attack_surface`
- 타입: `string`
- Required: Yes
- 설명:
  - 공격이 주입되거나 해석되는 표면
- 예시:
  - `prompt_text`
  - `email_body`
  - `email_subject`
  - `rag_context`

> **Open Decision**  
> repo 전반에서 사용할 canonical enum은 대소문자/표기법을 하나로 고정해야 한다.  
> 예: `PROMPT_TEXT` vs `prompt_text`, `EMAIL_BODY` vs `email_body`

---

### 5.3 `mutation_target_text`
- 타입: `string`
- Required: Yes
- 설명:
  - Mutation Engine이 실제로 변형할 원문 텍스트
- 예시:
  - prompt 본문
  - email body
  - subject
  - injected span

---

### 5.4 `mutation_target_role`
- 타입: `string`
- Required: Yes
- 설명:
  - mutation 대상 텍스트가 전체 입력 구조에서 어떤 역할인지 나타낸다.
- 예시:
  - `attacker_controlled_input`
  - `user_input`
  - `retrieved_context`
  - `email_body`

---

### 5.5 `is_mutable`
- 타입: `boolean`
- Required: Yes
- 설명:
  - 해당 레코드가 실제 mutation 대상인지 표시한다.
- 기본 해석:
  - `true`: mutation 대상
  - `false`: 보존용이지만 현재 run에서는 변형하지 않음

---

### 5.6 `source_format`
- 타입: `string`
- Required: Yes
- 설명:
  - 이 레코드가 어떤 상위 스키마/변환 계층에서 왔는지 나타낸다.
- 예시:
  - `mutation_seed_v1`

> 비고  
> 필요하다면 원본 정규화 포맷명을 따로 두는 필드가 추가될 수 있으나, 현재 확정 정보만으로는 `source_format` 하나만 명시한다.

---

## 6. 권장 해석 규칙

### 6.1 `attack_surface`와 `mutation_target_text`
- `attack_surface`는 “어디에 공격이 실리는가”
- `mutation_target_text`는 “정확히 어떤 문자열을 변형할 것인가”

즉, `attack_surface`는 위치/맥락, `mutation_target_text`는 실제 payload 대상이다.

### 6.2 `bucket_tags`
하나의 시드가 하나 이상의 bucket에 속할 수 있다.  
다만 현재 파일럿에서는 대표 bucket 하나를 우선 두고, 필요 시 복수 bucket을 허용하는 방식이 실용적이다.

### 6.3 `mutation_target_role`
operator selection이나 downstream 분석에서 “사용자 제어 입력인지, 외부 문맥인지”를 구분하는 데 사용한다.

---

## 7. 최소 유효 조건

mutation seed 레코드는 최소한 아래 조건을 만족해야 한다.

1. `record_id` 존재
2. `bucket_tags`가 비어 있지 않음
3. `attack_surface`가 비어 있지 않음
4. `mutation_target_text`가 비어 있지 않음
5. `mutation_target_role`가 비어 있지 않음
6. `is_mutable`이 boolean임
7. `source_format`이 비어 있지 않음

---

## 8. Example Skeleton

```json
{
  "record_id": "hackaprompt_455034",
  "dataset_name": "HackAPrompt",
  "subset_or_split": null,
  "input_primary": "<prompt text>",
  "input_secondary": null,
  "context_text": null,
  "candidate_output": null,
  "reference_output": null,
  "label_binary": null,
  "category_primary": "prompt_injection",
  "category_multilabel_json": [],
  "metadata_json": {},
  "raw_json": {},
  "bucket_tags": ["LLM01_PROMPT_INJECTION"],
  "attack_surface": "prompt_text",
  "mutation_target_text": "<prompt text or selected mutable span>",
  "mutation_target_role": "attacker_controlled_input",
  "is_mutable": true,
  "source_format": "mutation_seed_v1"
}