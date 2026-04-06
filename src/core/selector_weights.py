# src/core/operator_weights.py
from __future__ import annotations

from typing import Dict


# Day8 A: 초기 휴리스틱(하드코딩) 가중치 테이블이다.
# - 키는 bucket_id, 값은 op_id -> weight 배수
# - 기본값은 1.0이다.
_BUCKET_OP_WEIGHTS: Dict[str, Dict[str, float]] = {
    # Prompt Injection: role/frame/encoding/tool-misuse 계열을 우선
    "LLM01_PROMPT_INJECTION": {
        "op_lex_role_play": 2.5,
        "op_lex_instruction_override": 2.2,
        "op_enc_base64_wrap": 1.8,
        "op_enc_ascii_obfuscation": 1.8,
        "op_syn_fake_tool_instruction_injection": 2.0,
        "op_syn_boundary_delimiter_injection": 1.8,
        "op_fmt_markdown_wrapper": 1.2,
    },
    # Tool misuse: fake tool / toolcall JSON 유도 계열
    "LLM08_TOOL_MISUSE": {
        "op_syn_fake_tool_instruction_injection": 2.6,
        "op_syn_toolcall_json_injection": 2.2,
        "op_enc_json_string_escape": 1.5,
    },
    # Input robustness: 공백/구두점/포맷 흔들기
    "LLM05_INPUT_ROBUSTNESS": {
        "op_fmt_whitespace_noise": 2.0,
        "op_fmt_punctuation_resegmentation": 1.8,
        "op_fmt_markdown_wrapper": 1.2,
    },
    # 기본 예시: 필요 시 확장
    # "LLM04_OUTPUT_HANDLING": {...},
    # "LLM06_DOS": {...},
}

# 버킷 단위 global multiplier (없으면 1.0)
_BUCKET_MULTIPLIER: Dict[str, float] = {
    "LLM01_PROMPT_INJECTION": 1.0,
    "LLM08_TOOL_MISUSE": 1.0,
    "LLM05_INPUT_ROBUSTNESS": 1.0,
}


def weight_for(bucket_id: str, op_id: str) -> float:
    """
    bucket_id/op_id에 대한 가중치(>=0)를 반환한다.
    - 정의가 없으면 1.0
    """
    b = str(bucket_id)
    o = str(op_id)

    base = 1.0
    base *= float(_BUCKET_MULTIPLIER.get(b, 1.0))

    per_bucket = _BUCKET_OP_WEIGHTS.get(b)
    if not per_bucket:
        return base

    w = per_bucket.get(o, 1.0)
    try:
        w_f = float(w)
    except Exception:
        w_f = 1.0

    # 음수 방지
    if w_f < 0.0:
        w_f = 0.0

    return base * w_f
