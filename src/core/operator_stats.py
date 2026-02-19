from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_float01(x: Any) -> Optional[float]:
    try:
        v = float(x)
    except Exception:
        return None
    # clamp to [0,1] for robustness
    if v < 0.0:
        v = 0.0
    if v > 1.0:
        v = 1.0
    return v


def _norm_verdict(v: Any) -> str:
    if isinstance(v, str):
        s = v.strip().upper()
        if s in ("OK", "PASS", "SUCCESS"):
            return "PASS"
        if s in ("FAIL", "FAILED", "ERROR"):
            return "FAIL"
        if s in ("SKIPPED", "INVALID", "UNKNOWN"):
            return "UNKNOWN"
        return "UNKNOWN"
    return "UNKNOWN"


@dataclass
class StatsRow:
    bucket_id: str
    op_id: str

    n: int = 0
    n_pass: int = 0
    n_fail: int = 0
    n_unknown: int = 0

    n_score: int = 0
    avg_oracle_score: float = 0.0
    oracle_score_ema: float = 0.0

    last_updated_ts: str = ""

    @property
    def pass_rate(self) -> float:
        return (self.n_pass / self.n) if self.n > 0 else 0.0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "n": self.n,
            "n_pass": self.n_pass,
            "n_fail": self.n_fail,
            "n_unknown": self.n_unknown,
            "pass_rate": self.pass_rate,
            "n_score": self.n_score,
            "avg_oracle_score": self.avg_oracle_score,
            "oracle_score_ema": self.oracle_score_ema,
            "last_updated_ts": self.last_updated_ts,
        }


class OperatorStatsByBucket:
    """
    Bucket -> Operator -> StatsRow
    """
    EMA_ALPHA: float = 0.2  # only used after the first valid score

    def __init__(self) -> None:
        self._rows: Dict[str, Dict[str, StatsRow]] = {}

    def get(self, bucket_id: str, op_id: str) -> Optional[StatsRow]:
        return self._rows.get(bucket_id, {}).get(op_id)

    def _get_or_create(self, bucket_id: str, op_id: str) -> StatsRow:
        b = self._rows.setdefault(bucket_id, {})
        row = b.get(op_id)
        if row is None:
            row = StatsRow(bucket_id=bucket_id, op_id=op_id, last_updated_ts=_now_iso())
            b[op_id] = row
        return row

    def report_result(self, bucket_id: str, op_id: str, verdict: Any, oracle_score: Any) -> None:
        row = self._get_or_create(bucket_id, op_id)

        v = _norm_verdict(verdict)
        row.n += 1
        if v == "PASS":
            row.n_pass += 1
        elif v == "FAIL":
            row.n_fail += 1
        else:
            row.n_unknown += 1

        s = _to_float01(oracle_score)
        if s is not None:
            # average
            row.n_score += 1
            if row.n_score == 1:
                row.avg_oracle_score = s
                # IMPORTANT: first score initializes ema to score (tests expect exact)
                row.oracle_score_ema = s
            else:
                row.avg_oracle_score = ((row.avg_oracle_score * (row.n_score - 1)) + s) / row.n_score
                a = self.EMA_ALPHA
                row.oracle_score_ema = (a * s) + ((1.0 - a) * row.oracle_score_ema)

        row.last_updated_ts = _now_iso()

    def snapshot(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Expected by unit tests:
          { bucket_id: { op_id: { ...fields... } } }
        """
        out: Dict[str, Dict[str, Dict[str, Any]]] = {}
        for bucket_id, ops in self._rows.items():
            out[bucket_id] = {}
            for op_id, row in ops.items():
                out[bucket_id][op_id] = row.as_dict()
        return out
