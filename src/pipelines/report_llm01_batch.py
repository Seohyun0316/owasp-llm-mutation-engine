# src/pipelines/report_llm01_batch.py
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List


INPUT_PATH = Path("data/outputs/runs/run_llm01_batch.jsonl")
OUTPUT_JSON = Path("data/outputs/reports/run_llm01_batch_report.json")


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"invalid jsonl at line {line_no}: {e}") from e
    return rows


def pct(n: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((n / total) * 100.0, 2)


def main() -> None:
    rows = load_jsonl(INPUT_PATH)

    total = len(rows)
    status_counter = Counter()
    operator_counter = Counter()
    surface_counter = Counter()
    operator_by_surface = defaultdict(Counter)

    for row in rows:
        status = row.get("status", "UNKNOWN")
        op_id = row.get("selected_op_id", "NONE")
        raw_surface = row.get("attack_surface", "UNKNOWN")

        status_counter[str(status)] += 1
        operator_counter[str(op_id)] += 1
        surface_counter[str(raw_surface)] += 1
        operator_by_surface[str(raw_surface)][str(op_id)] += 1

    operator_stats = []
    for op_id, count in operator_counter.most_common():
        operator_stats.append({
            "op_id": op_id,
            "count": count,
            "ratio_pct": pct(count, total),
        })

    surface_stats = []
    for surface, count in surface_counter.most_common():
        by_op = []
        for op_id, op_count in operator_by_surface[surface].most_common():
            by_op.append({
                "op_id": op_id,
                "count": op_count,
                "ratio_within_surface_pct": pct(op_count, count),
            })
        surface_stats.append({
            "attack_surface": surface,
            "count": count,
            "ratio_pct": pct(count, total),
            "operators": by_op,
        })

    report = {
        "input_path": str(INPUT_PATH),
        "total_rows": total,
        "status_distribution": [
            {"status": k, "count": v, "ratio_pct": pct(v, total)}
            for k, v in status_counter.most_common()
        ],
        "operator_distribution": operator_stats,
        "surface_distribution": surface_stats,
        "top_operator": operator_stats[0] if operator_stats else None,
        "bottom_operator": operator_stats[-1] if operator_stats else None,
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("=" * 80)
    print("[operator distribution]")
    print("=" * 80)
    print(f"input_path : {INPUT_PATH}")
    print(f"total_rows : {total}")

    print("\n[status distribution]")
    for item in report["status_distribution"]:
        print(f"- {item['status']}: {item['count']} ({item['ratio_pct']}%)")

    print("\n[operator distribution]")
    for item in operator_stats:
        print(f"- {item['op_id']}: {item['count']} ({item['ratio_pct']}%)")

    print("\n[surface distribution]")
    for s in surface_stats:
        print(f"- {s['attack_surface']}: {s['count']} ({s['ratio_pct']}%)")

    print(f"\n[report saved] {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
