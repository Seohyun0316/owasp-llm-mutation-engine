from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


@dataclass
class GuardConfig:
    max_len: int = 8000
    schema_mode: bool = False
    placeholder: str = "N/A"


def _remove_control_chars(s: str) -> Tuple[str, bool]:
    """
    Remove ASCII control chars except \n \r \t.
    Returns (cleaned, removed_flag).
    """
    out_chars = []
    removed = False
    for ch in s:
        if ch in ("\n", "\r", "\t"):
            out_chars.append(ch)
            continue
        o = ord(ch)
        if o < 32 or o == 127:
            removed = True
            continue
        out_chars.append(ch)
    return ("".join(out_chars), removed)


def guard_text_with_meta(text: Any, cfg: GuardConfig) -> Tuple[str, Dict[str, Any]]:
    """
    Engine-grade guard that also returns meta for trace/debug.
    - TypeError for non-str (tests require this behavior)
    - Remove control chars
    - schema_mode: empty -> placeholder
    - Truncate to max_len
    """
    if not isinstance(text, str):
        raise TypeError("guard_text expects str")

    meta: Dict[str, Any] = {
        "guard_applied": False,
        "removed_control_chars": False,
        "schema_placeholder_applied": False,
        "truncated": False,
        "max_len": cfg.max_len,
    }

    s = text

    # 1) remove control chars
    s2, removed = _remove_control_chars(s)
    if removed:
        meta["guard_applied"] = True
        meta["removed_control_chars"] = True
    s = s2

    # 2) schema_mode placeholder
    if cfg.schema_mode and s.strip() == "":
        if s != cfg.placeholder:
            meta["guard_applied"] = True
            meta["schema_placeholder_applied"] = True
        s = cfg.placeholder

    # 3) truncate
    if cfg.max_len is not None and cfg.max_len > 0 and len(s) > cfg.max_len:
        meta["guard_applied"] = True
        meta["truncated"] = True
        s = s[: cfg.max_len]

    return s, meta


def guard_text(text: Any, cfg: GuardConfig) -> str:
    """
    Public/simple API: returns only sanitized text (str).
    Unit tests expect this.
    """
    s, _meta = guard_text_with_meta(text, cfg)
    return s


def is_text_valid(text: Any, cfg: GuardConfig) -> bool:
    """
    Legacy helper for tests / older callsites.
    'valid' means the raw input already satisfies constraints
    (guard would be a no-op).
    """
    if not isinstance(text, str):
        return False

    # control chars check (keep \n \r \t)
    for ch in text:
        o = ord(ch)
        if ch in ("\n", "\r", "\t"):
            continue
        if o < 32 or o == 127:
            return False

    if cfg.schema_mode and text.strip() == "":
        return False

    if cfg.max_len is not None and cfg.max_len > 0 and len(text) > cfg.max_len:
        return False

    return True
