# src/core/operator.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional, TypedDict, List

Status = Literal["OK", "SKIPPED", "INVALID"]


class OperatorMeta(TypedDict, total=True):
    op_id: str
    bucket_tags: List[str]
    surface_compat: List[str]
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    strength_range: List[int]  # [min, max]
    # optional
    params_schema: Dict[str, Any]


@dataclass
class ApplyResult:
    status: Status
    child_text: str
    trace: Dict[str, Any]
    error: Optional[str] = None


REQUIRED_META_KEYS = ("op_id", "bucket_tags", "surface_compat", "risk_level", "strength_range")


def validate_meta(meta: Dict[str, Any]) -> Optional[str]:
    """Return error string if invalid; None if OK."""
    for k in REQUIRED_META_KEYS:
        if k not in meta:
            return f"missing meta key: {k}"

    if not isinstance(meta["op_id"], str) or not meta["op_id"]:
        return "op_id must be non-empty string"

    if not isinstance(meta["bucket_tags"], list) or not all(isinstance(x, str) for x in meta["bucket_tags"]):
        return "bucket_tags must be list[str]"

    if not isinstance(meta["surface_compat"], list) or not all(isinstance(x, str) for x in meta["surface_compat"]):
        return "surface_compat must be list[str]"

    if meta["risk_level"] not in ("LOW", "MEDIUM", "HIGH"):
        return "risk_level must be one of LOW|MEDIUM|HIGH"

    sr = meta["strength_range"]
    if (
        not isinstance(sr, list)
        or len(sr) != 2
        or not all(isinstance(x, int) for x in sr)
        or sr[0] > sr[1]
    ):
        return "strength_range must be [min:int, max:int] with min<=max"

    return None
