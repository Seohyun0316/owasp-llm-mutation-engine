# src/pipelines/report_llm01_diversity.py
from __future__ import annotations

import json
import math
import hashlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List


INPUT_PATH = Path("data/outputs/runs/run_llm01_batch.jsonl")
OUTPUT_JSON = Path("data/outputs/reports/run_llm01_diversity.json")


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def shannon_entropy(counter: Counter) -> float:
    total = sum(counter.values())
    if total <= 0:
        return 0.0

    ent = 0.0
    for count in counter.values():
        p = count / total
        if p > 0:
            ent -= p * math.log2(p)
    return ent


def normalized_entropy(counter: Counter) -> float:
    if not counter:
        return 0.0
    ent = shannon_entropy(counter)
    max_ent = math.log2(len(counter)) if len(counter) > 1 else 0.0
    if max_ent == 0.0:
        return 0.0
    return ent / max_ent


def pct(n: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((n / total) * 100.0, 2)


def main() -> None:
    rows = load_jsonl(INPUT_PATH)

    total = len(rows)
    operator_counter = Counter()
    surface_counter = Counter()
    child_hashes = []
    child_hashes_by_surface = defaultdict(list)
    children_by_parent = defaultdict(list)

    for row in rows:
        op_id = row.get("selected_op_id", "NONE")
        surface = row.get("attack_surface", "UNKNOWN")
        child_text = row.get("child_text", "")

        operator_counter[str(op_id)] += 1
        surface_counter[str(surface)] += 1

        h = hash_text(str(child_text))
        child_hashes.append(h)
        child_hashes_by_surface[str(surface)].append(h)

        parent_id = str(row.get("parent_record_id", "UNKNOWN"))
        children_by_parent[parent_id].append(h)

    unique_hash_count = len(set(child_hashes))
    unique_ratio = unique_hash_count / total if total > 0 else 0.0

    same_child_parent_count = 0
    different_child_parent_count = 0

    for parent_id, hashes in children_by_parent.items():
        if len(hashes) < 2:
            continue
        if len(set(hashes)) == 1:
            same_child_parent_count += 1
        else:
            different_child_parent_count += 1

    surface_uniqueness = []
    for surface, hashes in child_hashes_by_surface.items():
        total_s = len(hashes)
        unique_s = len(set(hashes))
        surface_uniqueness.append({
            "attack_surface": surface,
            "count": total_s,
            "unique_count": unique_s,
            "unique_ratio": round(unique_s / total_s, 4) if total_s > 0 else 0.0,
        })

    op_entropy = shannon_entropy(operator_counter)
    op_entropy_norm = normalized_entropy(operator_counter)

    report = {
        "input_path": str(INPUT_PATH),
        "total_rows": total,
        "unique_child_count": unique_hash_count,
        "unique_child_ratio": round(unique_ratio, 4),
        "parent_pair_stats": {
            "same_child_parent_count": same_child_parent_count,
            "different_child_parent_count": different_child_parent_count,
            "different_ratio_pct": pct(
                different_child_parent_count,
                same_child_parent_count + different_child_parent_count,
            ),
        },
        "operator_entropy": {
            "shannon_entropy": round(op_entropy, 4),
            "normalized_entropy": round(op_entropy_norm, 4),
            "operator_count": len(operator_counter),
        },
        "surface_uniqueness": surface_uniqueness,
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("=" * 80)
    print("[mutation diversity report]")
    print("=" * 80)
    print(f"input_path             : {INPUT_PATH}")
    print(f"total_rows             : {total}")
    print(f"unique_child_count     : {unique_hash_count}")
    print(f"unique_child_ratio     : {report['unique_child_ratio']}")
    print(f"parent different ratio : {report['parent_pair_stats']['different_ratio_pct']}%")
    print(f"operator entropy       : {report['operator_entropy']['shannon_entropy']}")
    print(f"normalized entropy     : {report['operator_entropy']['normalized_entropy']}")

    print("\n[surface uniqueness]")
    for item in surface_uniqueness:
        print(
            f"- {item['attack_surface']}: "
            f"{item['unique_count']}/{item['count']} "
            f"({round(item['unique_ratio'] * 100, 2)}%)"
        )

    print(f"\n[report saved] {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
