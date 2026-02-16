# Operator Stats Logging Policy v0.1

본 문서는 Mutation Framework v0.1에서 **operator_stats_by_bucket** 결과를
나중에 분석 가능하도록 **로그 포맷과 저장 규칙을 고정**한다.

---

## 1. 목적

- bucket_id × op_id 단위로 operator 성능/품질 신호를 누적한다.
- 실험/스모크/퍼징 실행 결과를 파일로 남겨, 후속 분석(집계/시각화/리그레션)에 활용한다.
- 포맷을 버전으로 고정하여, 이후 확장 시 호환성을 관리한다.

---

## 2. 데이터 소스(업데이트 API)

상위 실행 루프(퍼저/스캐너/오라클 평가)가 아래 API로 결과를 기록한다.

- `report_result(bucket_id, op_id, verdict, oracle_score)`

필드 의미:
- `bucket_id`: OWASP 버킷 ID (예: `LLM01_PROMPT_INJECTION`)
- `op_id`: operator id
- `verdict`: PASS/FAIL/UNKNOWN (입력은 문자열/기타여도 정규화됨)
- `oracle_score`: 0..1 점수(가능하면), 없으면 None

---

## 3. 파일 로그 포맷(확정)

### 3.1 포맷 버전
- `schema_version = "operator_stats_by_bucket.v0.1"`

### 3.2 JSON Top-level 구조

```json
{
  "schema_version": "operator_stats_by_bucket.v0.1",
  "generated_at": 1730000000.0,
  "stats": {
    "<bucket_id>": {
      "<op_id>": {
        "n": 0,
        "n_pass": 0,
        "n_fail": 0,
        "n_unknown": 0,
        "pass_rate": 0.0,
        "n_score": 0,
        "avg_oracle_score": 0.0,
        "last_updated_ts": 0.0
      }
    }
  }
}
```

### 3.3 필드 정의

- `generated_at`: epoch seconds(float). 파일 생성 시각.
- `stats[bucket_id][op_id]`:
  - `n`: 총 이벤트 수
  - `n_pass`, `n_fail`, `n_unknown`: verdict 카운트
  - `pass_rate`: n_pass / (n_pass + n_fail), 분모 0이면 0.0
  - `n_score`: oracle_score 관측 수(None 제외)
  - `avg_oracle_score`: oracle_score(0..1)의 단순 평균
  - `last_updated_ts`: 해당 op/bucket 스탯의 마지막 업데이트 epoch seconds

---

## 4. 저장 규칙(권장)

### 4.1 기본 저장 경로(권장)
- `out/stats/operator_stats_by_bucket.v0.1.json`

`out/`은 실행 산출물이므로 git 추적 대상이 아니다(.gitignore 권장).

### 4.2 저장 API
- `OperatorStatsByBucket.dump_json(path)`를 사용해 위 포맷으로 저장한다.

---

## 5. 호환성/확장

- 신규 필드 추가는 **하위 호환**을 유지하는 방식으로만 수행한다.
- breaking change가 필요한 경우:
  - `schema_version`을 `operator_stats_by_bucket.v0.2` 등으로 상향하고
  - 변환 규칙/마이그레이션 노트를 함께 제공한다.
