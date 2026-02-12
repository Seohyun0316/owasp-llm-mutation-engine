from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


# \t(\x09), \n(\x0A), \r(\x0D)은 허용하고 나머지 제어문자 제거
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


@dataclass(frozen=True)
class GuardConfig:
    max_len: int = 8000
    schema_mode: bool = False
    placeholder: str = "N/A"


def guard_text(text: str, cfg: GuardConfig) -> str:
    """
    최소 Validity Guard (Policy A 엔진 단일 출구에서 사용)
    - 제어문자 제거(탭/개행/CR은 유지)
    - 길이 제한(max_len) 적용 (truncate)
    - schema_mode=True일 때 빈 문자열이면 placeholder로 치환
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")

    # 1) 금지 문자(제어문자) 제거
    cleaned = _CONTROL_CHARS_RE.sub("", text)

    # 2) 길이 제한
    if cfg.max_len > 0 and len(cleaned) > cfg.max_len:
        cleaned = cleaned[: cfg.max_len]

    # 3) 스키마 모드 placeholder
    if cfg.schema_mode and cleaned == "":
        cleaned = cfg.placeholder

    return cleaned


def is_text_valid(text: str, cfg: GuardConfig) -> bool:
    """
    Guard 이후 최소 유효성 검사.
    """
    if not isinstance(text, str):
        return False
    if cfg.max_len > 0 and len(text) > cfg.max_len:
        return False
    if _CONTROL_CHARS_RE.search(text) is not None:
        return False
    if cfg.schema_mode and text == "":
        return False
    return True
