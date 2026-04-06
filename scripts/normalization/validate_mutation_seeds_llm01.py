import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Any

INPUT_JSONL = "sample/merged/mutation_seeds_llm01.jsonl"
OUTPUT_SUMMARY = "sample/merged/mutation_seeds_llm01_validation_summary.json"

EXPECTED_TOTAL_ROWS = 100
EXPECTED_DATASET_COUNTS = {
    "advbench": 15,
    "hackaprompt": 35,
    "do_not_answer": 20,
    "beavertails": 15,
    "llmail": 15,
}
EXPECTED_ATTACK_SURFACE_COUNTS = {
    "prompt_text": 85,
    "email_body": 15,
}
EXPECTED_BUCKET_TAGS = ["LLM01_PROMPT_INJECTION"]
EXPECTED_SOURCE_FORMAT = "mutation_seed_v1"
EXPECTED_MUTATION_TARGET_ROLE = "attacker_controlled_input"

REQUIRED_TOP_LEVEL_KEYS = {
    "dataset_name",
    "subset_or_split",
    "record_id",
    "input_primary",
    "input_secondary",
    "context_text",
    "candidate_output",
    "reference_output",
    "label_binary",
    "category_primary",
    "category_multilabel_json",
    "metadata_json",
    "raw_json",
    "bucket_tags",
    "attack_surface",
    "mutation_target_text",
    "mutation_target_role",
    "is_mutable",
    "source_format",
}

ALLOWED_ATTACK_SURFACES = {"prompt_text", "email_body"}


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"[{path}] JSON parse error at line {line_num}: {e}") from e

            if not isinstance(row, dict):
                raise ValueError(f"[{path}] line {line_num}: JSON object가 아님")

            rows.append(row)
    return rows


def write_json(obj: Dict[str, Any], path: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def validate_row(row: Dict[str, Any], row_index: int) -> None:
    missing = REQUIRED_TOP_LEVEL_KEYS - set(row.keys())
    if missing:
        raise ValueError(f"row {row_index}: missing keys = {sorted(missing)}")

    if not isinstance(row["dataset_name"], str) or not row["dataset_name"].strip():
        raise ValueError(f"row {row_index}: invalid dataset_name")

    if not isinstance(row["record_id"], str) or not row["record_id"].strip():
        raise ValueError(f"row {row_index}: invalid record_id")

    if row["bucket_tags"] != EXPECTED_BUCKET_TAGS:
        raise ValueError(
            f"row {row_index}: bucket_tags mismatch (actual={row['bucket_tags']})"
        )

    if row["attack_surface"] not in ALLOWED_ATTACK_SURFACES:
        raise ValueError(
            f"row {row_index}: invalid attack_surface ({row['attack_surface']})"
        )

    if row["mutation_target_role"] != EXPECTED_MUTATION_TARGET_ROLE:
        raise ValueError(
            f"row {row_index}: invalid mutation_target_role ({row['mutation_target_role']})"
        )

    if row["source_format"] != EXPECTED_SOURCE_FORMAT:
        raise ValueError(
            f"row {row_index}: source_format mismatch (actual={row['source_format']})"
        )

    if not isinstance(row["is_mutable"], bool):
        raise ValueError(f"row {row_index}: is_mutable must be bool")

    target = row["mutation_target_text"]
    if not isinstance(target, str) or not target.strip():
        raise ValueError(f"row {row_index}: mutation_target_text is empty")

    input_primary = row["input_primary"]
    if not isinstance(input_primary, str) or not input_primary.strip():
        raise ValueError(f"row {row_index}: input_primary is empty")

    if target != input_primary:
        raise ValueError(
            f"row {row_index}: mutation_target_text != input_primary"
        )

    if not isinstance(row["metadata_json"], dict):
        raise ValueError(f"row {row_index}: metadata_json must be dict")

    if not isinstance(row["raw_json"], dict):
        raise ValueError(f"row {row_index}: raw_json must be dict")


def main() -> None:
    rows = load_jsonl(INPUT_JSONL)

    if len(rows) != EXPECTED_TOTAL_ROWS:
        raise ValueError(
            f"total_rows mismatch: expected={EXPECTED_TOTAL_ROWS}, actual={len(rows)}"
        )

    record_ids = set()
    dataset_counter = Counter()
    attack_surface_counter = Counter()

    for idx, row in enumerate(rows, start=1):
        validate_row(row, idx)

        rid = row["record_id"]
        if rid in record_ids:
            raise ValueError(f"duplicate record_id detected: {rid}")
        record_ids.add(rid)

        dataset_counter[row["dataset_name"]] += 1
        attack_surface_counter[row["attack_surface"]] += 1

    actual_dataset_counts = dict(dataset_counter)
    actual_attack_surface_counts = dict(attack_surface_counter)

    if actual_dataset_counts != EXPECTED_DATASET_COUNTS:
        raise ValueError(
            f"dataset_counts mismatch:\nexpected={EXPECTED_DATASET_COUNTS}\nactual={actual_dataset_counts}"
        )

    if actual_attack_surface_counts != EXPECTED_ATTACK_SURFACE_COUNTS:
        raise ValueError(
            f"attack_surface_counts mismatch:\nexpected={EXPECTED_ATTACK_SURFACE_COUNTS}\nactual={actual_attack_surface_counts}"
        )

    summary = {
        "status": "ok",
        "total_rows": len(rows),
        "dataset_counts": actual_dataset_counts,
        "attack_surface_counts": actual_attack_surface_counts,
        "unique_record_ids": len(record_ids),
        "validated_file": INPUT_JSONL,
    }

    write_json(summary, OUTPUT_SUMMARY)

    print("[OK] Validation completed.")
    print(f"[INFO] validated_file: {INPUT_JSONL}")
    print(f"[INFO] total_rows: {len(rows)}")
    print(f"[INFO] dataset_counts: {actual_dataset_counts}")
    print(f"[INFO] attack_surface_counts: {actual_attack_surface_counts}")
    print(f"[INFO] unique_record_ids: {len(record_ids)}")
    print(f"[INFO] summary_output: {OUTPUT_SUMMARY}")


if __name__ == "__main__":
    main()
