# src/config/enabled_buckets.py
"""
- 현재 실행에서 어떤 bucket만 활성화할지 관리
"""


from __future__ import annotations

from .buckets import (
    LLM01_PROMPT_INJECTION,
    LLM04_DATA_AND_MODEL_POISONING,
    LLM09_MISINFORMATION_OR_HALLUCINATION,
)

# 현재 1차 실험 대상
ENABLED_BUCKETS = [
    LLM01_PROMPT_INJECTION,
]

# 추후 확장용 예시
ENABLED_BUCKETS_ALL = [
    LLM01_PROMPT_INJECTION,
    LLM04_DATA_AND_MODEL_POISONING,
    LLM09_MISINFORMATION_OR_HALLUCINATION,
]
