# scripts/inspect_llm01_seed_schema.py
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

INPUT_PATH = Path("data/inputs/mutation_seeds_llm01.jsonl")

def main() -> None:
    rows = []
    with INPUT_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    print(f"total_rows: {len(rows)}")

    key_counter = Counter()
    attack_surface_counter = Counter()
    mutation_role_counter = Counter()
    source_format_counter = Counter()
    bucket_counter = Counter()
    mutable_counter = Counter()
    empty_target_count = 0

    examples_by_surface = defaultdict(list)

    for row in rows:
        key_counter.update(row.keys())

        attack_surface = row.get("attack_surface")
        mutation_role = row.get("mutation_target_role")
        source_format = row.get("source_format")
        is_mutable = row.get("is_mutable")
        target_text = row.get("mutation_target_text")
        bucket_tags = row.get("bucket_tags", [])

        attack_surface_counter[str(attack_surface)] += 1
        mutation_role_counter[str(mutation_role)] += 1
        source_format_counter[str(source_format)] += 1
        mutable_counter[str(is_mutable)] += 1

        for b in bucket_tags if isinstance(bucket_tags, list) else []:
            bucket_counter[str(b)] += 1

        if not isinstance(target_text, str) or not target_text.strip():
            empty_target_count += 1

        if len(examples_by_surface[str(attack_surface)]) < 2:
            examples_by_surface[str(attack_surface)].append({
                "record_id": row.get("record_id"),
                "attack_surface": attack_surface,
                "mutation_target_role": mutation_role,
                "bucket_tags": bucket_tags,
                "target_preview": (target_text[:120] if isinstance(target_text, str) else None),
            })

    print("\n[key frequency]")
    for k, v in key_counter.most_common():
        print(f"{k}: {v}")

    print("\n[attack_surface]")
    for k, v in attack_surface_counter.most_common():
        print(f"{k}: {v}")

    print("\n[mutation_target_role]")
    for k, v in mutation_role_counter.most_common():
        print(f"{k}: {v}")

    print("\n[source_format]")
    for k, v in source_format_counter.most_common():
        print(f"{k}: {v}")

    print("\n[bucket_tags]")
    for k, v in bucket_counter.most_common():
        print(f"{k}: {v}")

    print("\n[is_mutable]")
    for k, v in mutable_counter.most_common():
        print(f"{k}: {v}")

    print(f"\nempty_target_count: {empty_target_count}")

    print("\n[examples by attack_surface]")
    for surface, examples in examples_by_surface.items():
        print(f"\n- surface={surface}")
        for ex in examples:
            print(json.dumps(ex, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
