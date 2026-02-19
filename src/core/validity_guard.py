from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple


@dataclass
class GuardConfig:
    max_len: int = 8000
    schema_mode: bool = False
    placeholder: str = "N/A"


def _remove_control_chars(s: str) -> Tuple[str, bool]:
    """
    Remove ASCII control chars except \\n \\r \\t.
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
    - schema_mode:
        * empty -> placeholder
        * additionally: ensure final output (strip) endswith(placeholder)
          (Policy A test expects suffix)
    - Truncate to max_len
    """
    if not isinstance(text, str):
        raise TypeError("guard_text expects str")

    meta: Dict[str, Any] = {
        "guard_applied": False,
        "removed_control_chars": False,
        "schema_placeholder_applied": False,
        "schema_placeholder_suffix_appended": False,
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

    # 2) schema_mode placeholder + suffix guarantee
    if cfg.schema_mode:
        ph = cfg.placeholder or "N/A"
        stripped = s.strip()

        # empty => placeholder
        if stripped == "":
            if s != ph:
                meta["guard_applied"] = True
                meta["schema_placeholder_applied"] = True
            s = ph
        else:
            # IMPORTANT: tests require final text endswith(placeholder)
            # If not, append as suffix deterministically.
            if not stripped.endswith(ph):
                meta["guard_applied"] = True
                meta["schema_placeholder_suffix_appended"] = True
                s = stripped + "\n" + ph
            else:
                # keep original but normalize to stripped to avoid trailing whitespace instability
                s = stripped

    # 3) truncate
    if cfg.max_len is not None and cfg.max_len > 0 and len(s) > cfg.max_len:
        meta["guard_applied"] = True
        meta["truncated"] = True
        s = s[: cfg.max_len]

        # If schema_mode, re-check suffix after truncation (must still endwith placeholder)
        if cfg.schema_mode:
            ph = cfg.placeholder or "N/A"
            s_stripped = s.strip()
            if s_stripped == "":
                s = ph
                meta["schema_placeholder_applied"] = True
            elif not s_stripped.endswith(ph):
                # try to force suffix within max_len
                # keep as much prefix as possible
                suffix = "\n" + ph
                if cfg.max_len > len(suffix):
                    keep = cfg.max_len - len(suffix)
                    s = s_stripped[:keep] + suffix
                    meta["schema_placeholder_suffix_appended"] = True
                else:
                    # if max_len is too small, best effort: trim to last bytes of placeholder
                    s = ph[: cfg.max_len]

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

    # control chars check (keep \\n \\r \\t)
    for ch in text:
        o = ord(ch)
        if ch in ("\n", "\r", "\t"):
            continue
        if o < 32 or o == 127:
            return False

    if cfg.schema_mode:
        ph = cfg.placeholder or "N/A"
        stripped = text.strip()
        if stripped == "":
            return False
        if not stripped.endswith(ph):
            return False

    if cfg.max_len is not None and cfg.max_len > 0 and len(text) > cfg.max_len:
        return False

    return True
