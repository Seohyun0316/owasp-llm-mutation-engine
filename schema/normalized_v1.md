# normalized_v1

## 1. 목적

`normalized_v1`은 서로 다른 원천 데이터셋을 공통된 레코드 형식으로 정규화하기 위한 중간 스키마이다.

이 스키마의 목적은 다음과 같다.

1. 서로 다른 데이터셋(HackAPrompt, LLMmail, AdvBench, DoNotAnswer, BeaverTails 등)을 동일한 필드 구조로 다룰 수 있게 한다.
2. 원본 데이터의 의미를 최대한 보존하면서, 이후 시드 선별/태깅/샘플링/Mutation Seed 변환의 입력으로 사용한다.
3. 데이터셋별 고유 필드는 `raw_json` 또는 `metadata_json`에 보존하고, 공통 처리에 필요한 최소 필드만 상위 레벨에 노출한다.

---

## 2. 레코드 단위

- 저장 형식: JSON Lines (`.jsonl`)
- 한 줄 = 한 개의 정규화 레코드
- 각 레코드는 하나의 원본 샘플에 대응한다.

---

## 3. 설계 원칙

### 3.1 공통 필드 우선
원본 데이터셋마다 필드명이 다르더라도, 공통 의미를 갖는 정보는 동일한 canonical field로 매핑한다.

### 3.2 원본 보존
원본 고유 구조는 삭제하지 않고 `raw_json`에 보존한다.

### 3.3 후속 변환 친화성
후속 단계에서 `mutation_seed_v1`로 변환할 수 있도록, 입력 프롬프트/보조 문맥/레이블/카테고리 정보를 분리해 둔다.

### 3.4 데이터셋 간 의미 차이 허용
어떤 필드는 특정 데이터셋에서만 채워질 수 있다.  
예: 이메일형 데이터셋은 `input_secondary`에 subject가 들어갈 수 있고, 단일 프롬프트형 데이터셋은 `null`일 수 있다.

---

## 4. 필드 정의

> 아래에서 **Required**는 `normalized_v1` 레코드에 반드시 키가 존재해야 함을 뜻한다.  
> 값이 없을 경우에도 `null` 또는 빈 구조를 사용할 수 있다.

---

### 4.1 `record_id`
- 타입: `string`
- Required: Yes
- 설명:
  - 정규화 레코드의 고유 식별자이다.
  - 데이터셋 이름과 원본 식별자를 조합한 안정적인 값이어야 한다.
- 예시:
  - `hackaprompt_455034`
  - `advbench_000343`

---

### 4.2 `dataset_name`
- 타입: `string`
- Required: Yes
- 설명:
  - 원천 데이터셋 이름이다.
- 예시:
  - `HackAPrompt`
  - `LLMmail`
  - `AdvBench`
  - `DoNotAnswer`
  - `BeaverTails`

> **Open Decision**  
> 현재 예시 데이터에는 `source_dataset`이라는 이름이 사용된 경우가 있다.  
> 정규화 스키마에서는 `dataset_name`으로 통일할지, `source_dataset`을 canonical field로 유지할지 repo 전체에서 하나로 고정해야 한다.

---

### 4.3 `subset_or_split`
- 타입: `string | null`
- Required: Yes
- 설명:
  - train/test/validation, phase1/phase2, 기타 하위 split 또는 subset 이름을 저장한다.
- 예시:
  - `train`
  - `test`
  - `Phase1`
  - `null`

---

### 4.4 `input_primary`
- 타입: `string`
- Required: Yes
- 설명:
  - 레코드의 주 입력 텍스트이다.
  - 일반적으로 main prompt, email body, user message, 공격 본문 등에 대응한다.
- 매핑 예:
  - HackAPrompt: `prompt_text` 또는 공격 prompt 본문
  - LLMmail: email body
  - AdvBench / DoNotAnswer / BeaverTails: main prompt

---

### 4.5 `input_secondary`
- 타입: `string | null`
- Required: Yes
- 설명:
  - 보조 입력 텍스트이다.
  - 예: email subject, auxiliary prompt, headline 등
- 예시:
  - LLMmail의 `subject`
  - 그 외 데이터셋에서는 `null`

---

### 4.6 `context_text`
- 타입: `string | null`
- Required: Yes
- 설명:
  - 입력 외부의 문맥 정보를 담는다.
  - 예: wrapper, system framing, retrieved context, serialized thread, surrounding template
- 비고:
  - 원본 구조상 prompt와 context의 구분이 불가능한 데이터셋은 `null`로 둘 수 있다.

---

### 4.7 `candidate_output`
- 타입: `string | null`
- Required: Yes
- 설명:
  - 원본 데이터셋이 제공하는 모델 출력 후보 또는 관측 응답
- 예시:
  - LLMmail의 `output`
  - 데이터셋 제공 응답
  - 미제공 시 `null`

---

### 4.8 `reference_output`
- 타입: `string | null`
- Required: Yes
- 설명:
  - 정답 응답, 기대 응답, 비교 기준 응답
- 비고:
  - 데이터셋에 따라 존재하지 않을 수 있다.

---

### 4.9 `label_binary`
- 타입: `boolean | null`
- Required: Yes
- 설명:
  - 안전/위험, 공격 성공/실패 등 이진 레이블을 담는다.
- 비고:
  - 레이블 의미는 데이터셋마다 다를 수 있으므로, 정확한 의미는 `metadata_json`에 보조 설명을 둘 수 있다.

---

### 4.10 `category_primary`
- 타입: `string | null`
- Required: Yes
- 설명:
  - 대표 카테고리 또는 대표 공격 유형
- 예시:
  - `prompt_injection`
  - `instruction_override`
  - `unsafe_request`

---

### 4.11 `category_multilabel_json`
- 타입: `object | array | null`
- Required: Yes
- 설명:
  - 다중 카테고리/세부 태그 구조를 저장한다.
- 예시:
  - 원본 `category`
  - 다중 위험 영역 태그
  - 자동 태깅된 복수 label

> **Open Decision**  
> 이 필드를 실제 JSON object로 저장할지, stringified JSON으로 저장할지 통일이 필요하다.  
> 가능하면 JSON object 유지가 바람직하다.

---

### 4.12 `metadata_json`
- 타입: `object | null`
- Required: Yes
- 설명:
  - 공통 필드로 승격하지 않은 보조 메타데이터를 담는다.
- 예시:
  - difficulty
  - explicitness
  - style
  - directness
  - 기타 preprocessing note

---

### 4.13 `raw_json`
- 타입: `object`
- Required: Yes
- 설명:
  - 원본 레코드 전체를 가능한 한 손실 없이 저장한다.
- 목적:
  - 원복 가능성 확보
  - 디버깅
  - 후속 재매핑
  - 데이터셋 고유 필드 보존

---

## 5. 권장 매핑 예시

### 5.1 HackAPrompt 계열
- `record_id` ← 예: `hackaprompt_455034`
- `dataset_name` ← `HackAPrompt`
- `input_primary` ← prompt text
- `input_secondary` ← `null`
- `context_text` ← `null` 또는 별도 분리 불가 시 `null`
- `candidate_output` ← completion if present
- `reference_output` ← expected completion if present
- `metadata_json` ← auto tags, difficulty, explicitness 등
- `raw_json` ← 원본 전체

### 5.2 LLMmail 계열
- `record_id` ← row/job 단위 안정 식별자
- `dataset_name` ← `LLMmail`
- `input_primary` ← email body 또는 main instruction body
- `input_secondary` ← subject
- `context_text` ← serialized thread / HTML / wrapper context
- `candidate_output` ← processed example output
- `reference_output` ← 없으면 `null`
- `metadata_json` ← scenario, objectives, timing 등
- `raw_json` ← 원본 전체

---

## 6. 최소 유효 조건

정규화 레코드는 최소한 아래 조건을 만족해야 한다.

1. `record_id`가 비어 있지 않아야 한다.
2. `dataset_name`가 비어 있지 않아야 한다.
3. `input_primary`가 문자열이어야 한다.
4. `raw_json`이 존재해야 한다.
5. 존재하지 않는 필드는 키 자체를 생략하지 말고 `null`을 권장한다.

---

## 7. Open Decisions

1. canonical field 이름을 `dataset_name`으로 할지 `source_dataset`으로 할지
2. `category_multilabel_json`, `metadata_json`, `raw_json`를 object로 둘지 stringified JSON으로 둘지
3. `candidate_output`와 `reference_output`의 역할 구분 규칙
4. `label_binary`의 의미를 전 데이터셋에서 하나로 강제할지, 데이터셋별 의미 차이를 허용할지

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
  "candidate_output": "<model completion or null>",
  "reference_output": "<expected output or null>",
  "label_binary": null,
  "category_primary": "prompt_injection",
  "category_multilabel_json": [],
  "metadata_json": {},
  "raw_json": {}
}