import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Any

INPUT_JSONL = "sample/merged/prompt_seed_dataset_llm01.jsonl"
OUTPUT_SUMMARY = "sample/merged/prompt_seed_dataset_llm01_validation_summary.json"

EXPECTED_TOTAL_ROWS = 100
EXPECTED_DATASET_COUNTS = {
    "advbench": 15,
    "hackaprompt": 35,
    "do_not_answer": 20,
    "beavertails": 15,
    "llmail": 15,
}
EXPECTED_BUCKET_TAGS = ["LLM01_PROMPT_INJECTION"]

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
}


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

    if not isinstance(row["metadata_json"], dict):
        raise ValueError(f"row {row_index}: metadata_json must be dict")

    if not isinstance(row["raw_json"], dict):
        raise ValueError(f"row {row_index}: raw_json must be dict")

    input_primary = row["input_primary"]
    if not isinstance(input_primary, str) or not input_primary.strip():
        raise ValueError(f"row {row_index}: input_primary is empty")

    metadata = row["metadata_json"]

    if "sample_index" not in metadata:
        raise ValueError(f"row {row_index}: missing metadata_json.sample_index")

    if "sample_label" not in metadata:
        raise ValueError(f"row {row_index}: missing metadata_json.sample_label")

    if not isinstance(metadata["sample_index"], int):
        raise ValueError(f"row {row_index}: sample_index must be int")

    if not isinstance(metadata["sample_label"], str) or not metadata["sample_label"].strip():
        raise ValueError(f"row {row_index}: invalid sample_label")


def main() -> None:
    rows = load_jsonl(INPUT_JSONL)

    if len(rows) != EXPECTED_TOTAL_ROWS:
        raise ValueError(
            f"total_rows mismatch: expected={EXPECTED_TOTAL_ROWS}, actual={len(rows)}"
        )

    record_ids = set()
    dataset_counter = Counter()
    sample_index_map: Dict[str, List[int]] = {}
    sample_label_map: Dict[str, set] = {}

    for idx, row in enumerate(rows, start=1):
        validate_row(row, idx)

        rid = row["record_id"]
        if rid in record_ids:
            raise ValueError(f"duplicate record_id detected: {rid}")
        record_ids.add(rid)

        dataset_name = row["dataset_name"]
        dataset_counter[dataset_name] += 1

        metadata = row["metadata_json"]
        sample_index = metadata["sample_index"]
        sample_label = metadata["sample_label"]

        if dataset_name not in sample_index_map:
            sample_index_map[dataset_name] = []
        sample_index_map[dataset_name].append(sample_index)

        if dataset_name not in sample_label_map:
            sample_label_map[dataset_name] = set()

        if sample_label in sample_label_map[dataset_name]:
            raise ValueError(
                f"duplicate sample_label detected in dataset={dataset_name}: {sample_label}"
            )
        sample_label_map[dataset_name].add(sample_label)

    actual_dataset_counts = dict(dataset_counter)

    if actual_dataset_counts != EXPECTED_DATASET_COUNTS:
        raise ValueError(
            f"dataset_counts mismatch:\nexpected={EXPECTED_DATASET_COUNTS}\nactual={actual_dataset_counts}"
        )

    for dataset_name, expected_count in EXPECTED_DATASET_COUNTS.items():
        indices = sorted(sample_index_map.get(dataset_name, []))
        expected_indices = list(range(1, expected_count + 1))
        if indices != expected_indices:
            raise ValueError(
                f"sample_index sequence mismatch for {dataset_name}:\n"
                f"expected={expected_indices}\nactual={indices}"
            )

    summary = {
        "status": "ok",
        "total_rows": len(rows),
        "dataset_counts": actual_dataset_counts,
        "unique_record_ids": len(record_ids),
        "validated_file": INPUT_JSONL,
    }

    write_json(summary, OUTPUT_SUMMARY)

    print("[OK] Validation completed.")
    print(f"[INFO] validated_file: {INPUT_JSONL}")
    print(f"[INFO] total_rows: {len(rows)}")
    print(f"[INFO] dataset_counts: {actual_dataset_counts}")
    print(f"[INFO] unique_record_ids: {len(record_ids)}")
    print(f"[INFO] summary_output: {OUTPUT_SUMMARY}")


if __name__ == "__main__":
    main()
