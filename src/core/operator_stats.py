from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Literal


Verdict = Literal["PASS", "FAIL", "UNKNOWN"]


def _norm_verdict(v: object) -> Verdict:
    """
    최소 안정형: 입력이 뭐든 PASS/FAIL/UNKNOWN으로 정규화한다.
    """
    if isinstance(v, str):
        u = v.strip().upper()
        if u in ("PASS", "OK", "SUCCESS", "TRUE", "1"):
            return "PASS"
        if u in ("FAIL", "NG", "ERROR", "FALSE", "0"):
            return "FAIL"
        if u in ("UNKNOWN", "NA", "N/A", "NONE", ""):
            return "UNKNOWN"
    return "UNKNOWN"


def _clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


@dataclass
class OpBucketStats:
    """
    bucket_id 내부에서 op_id 하나에 대한 누적 통계(최소).

    - n: 총 이벤트 수
    - n_pass/n_fail/n_unknown: verdict 카운트
    - avg_oracle_score: oracle_score(0..1)의 단순 평균 (None 제외)
    - n_score: score 관측 수
    - last_updated_ts: 마지막 업데이트 시각
    """
    n: int = 0
    n_pass: int = 0
    n_fail: int = 0
    n_unknown: int = 0

    n_score: int = 0
    avg_oracle_score: float = 0.0

    last_updated_ts: float = 0.0

    def update(self, verdict: Verdict, oracle_score: Optional[float]) -> None:
        self.n += 1
        if verdict == "PASS":
            self.n_pass += 1
        elif verdict == "FAIL":
            self.n_fail += 1
        else:
            self.n_unknown += 1

        if oracle_score is not None:
            s = _clamp01(float(oracle_score))
            # online mean
            self.n_score += 1
            if self.n_score == 1:
                self.avg_oracle_score = s
            else:
                self.avg_oracle_score = self.avg_oracle_score + (s - self.avg_oracle_score) / float(self.n_score)

        self.last_updated_ts = time.time()

    @property
    def pass_rate(self) -> float:
        denom = self.n_pass + self.n_fail
        if denom <= 0:
            return 0.0
        return self.n_pass / denom


@dataclass
class OperatorStatsByBucket:
    """
    Day6 최소 안정형 API:
    - report_result(bucket_id, op_id, verdict, oracle_score)
    - stats[bucket_id][op_id] = OpBucketStats

    NOTE:
    - 스레드 안전성/영속화는 Day6 범위 밖
    """
    stats: Dict[str, Dict[str, OpBucketStats]] = field(default_factory=dict)

    def ensure(self, bucket_id: str, op_id: str) -> OpBucketStats:
        b = str(bucket_id)
        o = str(op_id)
        if b not in self.stats:
            self.stats[b] = {}
        if o not in self.stats[b]:
            self.stats[b][o] = OpBucketStats()
        return self.stats[b][o]

    def get(self, bucket_id: str, op_id: str) -> Optional[OpBucketStats]:
        return self.stats.get(str(bucket_id), {}).get(str(op_id))

    def report_result(
        self,
        bucket_id: str,
        op_id: str,
        verdict: object,
        oracle_score: Optional[object] = None,
    ) -> None:
        """
        요구사항 형태:
            report_result(bucket_id, op_id, verdict, oracle_score)

        최소 안정형 방어:
        - verdict는 PASS/FAIL/UNKNOWN으로 정규화
        - oracle_score는 float 변환 가능하면 0..1 clamp, 아니면 None 처리
        - 어떤 입력이 들어와도 예외를 던지지 않는 것을 목표로 한다.
        """
        b = str(bucket_id)
        o = str(op_id)
        v = _norm_verdict(verdict)

        score_f: Optional[float] = None
        if oracle_score is not None:
            try:
                score_f = float(oracle_score)
            except Exception:
                score_f = None

        st = self.ensure(b, o)
        st.update(v, score_f)

    def snapshot(self) -> Dict[str, Dict[str, dict]]:
        """
        직렬화 가능한 dict 형태로 내보내기(테스트/로그/리포트용).
        """
        out: Dict[str, Dict[str, dict]] = {}
        for bucket_id, ops in self.stats.items():
            out[bucket_id] = {}
            for op_id, st in ops.items():
                out[bucket_id][op_id] = {
                    "n": st.n,
                    "n_pass": st.n_pass,
                    "n_fail": st.n_fail,
                    "n_unknown": st.n_unknown,
                    "pass_rate": st.pass_rate,
                    "n_score": st.n_score,
                    "avg_oracle_score": st.avg_oracle_score,
                    "last_updated_ts": st.last_updated_ts,
                }
        return out

    def dump_json(self, path: str) -> None:
        """
        결과 로그 포맷 확정(v0.1):
        - schema_version + generated_at + stats(snapshot)를 파일로 저장한다.
        - downstream 분석(파이썬/판다스/JS)에서 그대로 로드 가능해야 한다.
        """
        payload = {
            "schema_version": "operator_stats_by_bucket.v0.1",
            "generated_at": time.time(),
            "stats": self.snapshot(),
        }

        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
