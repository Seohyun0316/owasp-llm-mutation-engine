# src/core/novelty.py
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Dict, Set


def _hash_text(s: str) -> str:
    # Policy A guard 이후 텍스트를 넣는 것을 전제로 함.
    # 안정적 비교를 위해 개행/공백을 그대로 포함한 원문 해시를 사용한다.
    return hashlib.sha256(s.encode("utf-8", errors="replace")).hexdigest()


@dataclass
class BucketNoveltyStats:
    total: int = 0
    unique: int = 0
    seen_hits: int = 0
    hashes: Set[str] = field(default_factory=set)

    def mark(self, text: str) -> bool:
        """
        Returns:
          True  => 이미 본 결과(duplicate)
          False => 처음 보는 결과(unique)
        """
        self.total += 1
        h = _hash_text(text)
        if h in self.hashes:
            self.seen_hits += 1
            return True
        self.hashes.add(h)
        self.unique += 1
        return False

    @property
    def unique_ratio(self) -> float:
        if self.total <= 0:
            return 0.0
        return float(self.unique) / float(self.total)


class NoveltyTracker:
    """
    bucket별로 child_text 해시를 기록하여 novelty 통계를 제공한다.
    - seen_hits: 중복으로 판정된 횟수
    - unique_ratio: unique / total
    """

    def __init__(self) -> None:
        self._by_bucket: Dict[str, BucketNoveltyStats] = {}

    def _get(self, bucket_id: str) -> BucketNoveltyStats:
        if bucket_id not in self._by_bucket:
            self._by_bucket[bucket_id] = BucketNoveltyStats()
        return self._by_bucket[bucket_id]

    def mark_seen(self, bucket_id: str, child_text: str) -> bool:
        return self._get(bucket_id).mark(child_text)

    def snapshot(self) -> Dict[str, dict]:
        out: Dict[str, dict] = {}
        for b, st in self._by_bucket.items():
            out[b] = {
                "total": st.total,
                "unique": st.unique,
                "seen_hits": st.seen_hits,
                "unique_ratio": st.unique_ratio,
            }
        return out

    def snapshot_one(self, bucket_id: str) -> dict:
        st = self._get(bucket_id)
        return {
            "total": st.total,
            "unique": st.unique,
            "seen_hits": st.seen_hits,
            "unique_ratio": st.unique_ratio,
        }
