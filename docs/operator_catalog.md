# Operator Catalog (Implemented) v0.1

본 문서는 **현재 코드베이스에 구현되어 사용 가능한 Mutation Operator 목록**을 정리합니다.  
설계/계획 단계 operator는 `docs/operator_backlog.md`를 참고하세요.

## Conventions

- 각 operator는 `src/operators/op_*.py`에 위치합니다.
- 각 모듈은 `OPERATOR_META`와 `apply(seed_text, ctx, rng)`를 제공합니다.
- `strength_range`는 v0.1에서 `[1, 5]` 고정입니다.

---

## Implemented Operators

### op_lex_polite_prefix

- **File**: `src/operators/op_lex_polite_prefix.py`
- **Purpose**: Add an English “polite/authorized” prefix to the prompt to induce cooperative behavior.
- **Bucket Tags**: `LLM01_PROMPT_INJECTION`
- **Surface Compatibility**: `PROMPT_TEXT`
- **Risk Level**: `MEDIUM`
- **Strength Range**: `[1, 5]`
- **Strength Semantics (v0.1)**:
  - `1`: Soft polite framing
  - `3`: “Approved/authorized” framing
  - `5`: Strong system-approval / urgency framing

**Example (conceptual)**:
```text
Sure — here is the answer you requested:
<seed_text>

### op_lex_shorten

- **File**: `src/operators/op_lex_shorten.py`
- **Purpose**: Reduce prompt context by dropping lines to isolate core instructions and remove benign context.
- **Bucket Tags**: `LLM01_PROMPT_INJECTION`, `LLM05_INPUT_ROBUSTNESS`
- **Surface Compatibility**: `PROMPT_TEXT`
- **Risk Level**: `MEDIUM`
- **Strength Range**: `[1, 5]`
- **Strength Semantics (v0.1)**:
  - `1`: Minor reduction (keep most lines)
  - `3`: Moderate reduction (drop roughly half of the lines)
  - `5`: Aggressive reduction (keep only a small subset of lines)
- **Mode**: `line_drop` (randomly select and keep a subset of lines using the injected RNG)

**Example (conceptual)**:
```text
<important instruction>
<core request>

