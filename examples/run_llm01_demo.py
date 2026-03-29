from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from src.core.registry import OperatorRegistry
from src.core.mutator import Mutator
from src.core.selector import RandomSelector


SEED_PATH = Path("examples/llm01_llmail_seeds.jsonl")
OUT_PATH = Path("examples/llm01_demo_out.json")


def load_jsonl(path: Path, limit: int = 5):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            rows.append(json.loads(line))
    return rows


def main():
    seeds = load_jsonl(SEED_PATH, limit=5)

    registry = OperatorRegistry()
    loaded = registry.load_from_package("src.operators", strict=False)

    selector = RandomSelector(registry)
    mutator = Mutator(registry, selector=selector)

    runs = []
    op_counter = Counter()

    for row in seeds:
        seed_id = row.get("seed_id", "seed")
        seed_text = row["seed_text"]
        bucket_id = row.get("bucket_id", "LLM01_PROMPT_INJECTION")
        surface = row.get("surface", "PROMPT_TEXT")
        metadata = row.get("metadata", {})

        children = mutator.generate_children(
            seed_text=seed_text,
            bucket_id=bucket_id,
            surface=surface,
            n=3,
            k=1,
            seed_base=1337,
            strength=2,
            risk_max=None,
            constraints={
                "max_chars": 500,
                "schema_mode": False,
                "placeholder": "N/A",
            },
            metadata={"seed_id": seed_id, **metadata},
            stats_by_bucket={},
        )

        child_rows = []
        for ch in children:
            for tr in ch.mutation_trace:
                op_id = tr.get("op_id")
                if op_id and op_id != "__guard__":
                    op_counter[op_id] += 1

            child_rows.append(
                {
                    "child_text": ch.child_text,
                    "last_status": ch.last_status,
                    "mutation_trace": ch.mutation_trace,
                }
            )

        runs.append(
            {
                "seed_id": seed_id,
                "bucket_id": bucket_id,
                "surface": surface,
                "seed_text": seed_text,
                "children": child_rows,
            }
        )

    result = {
        "loaded_operator_count": loaded,
        "load_errors": registry.load_errors,
        "used_ops": dict(op_counter),
        "runs": runs,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"saved: {OUT_PATH}")
    print("used_ops:", dict(op_counter))


if __name__ == "__main__":
    main()
