import json
from pathlib import Path
from typing import Dict, List, Any

INPUT_FILES = [
    {
        "dataset_key": "advbench",
        "path": "sample/normalized_sample/normalized_sample_advbench.jsonl",
        "expected_count": 15,
        "expected_dataset_name": "advbench",
    },
    {
        "dataset_key": "hackaprompt",
        "path": "sample/normalized_sample/normalized_sample_hackaprompt.jsonl",
        "expected_count": 35,
        "expected_dataset_name": "hackaprompt",
    },
    {
        "dataset_key": "do_not_answer",
        "path": "sample/normalized_sample/normalized_sample_donotanswer.jsonl",
        "expected_count": 20,
        "expected_dataset_name": "do_not_answer",
    },
    {
        "dataset_key": "beavertails",
        "path": "sample/normalized_sample/normalized_sample_beavertails.jsonl",
        "expected_count": 15,
        "expected_dataset_name": "beavertails",
    },
    {
        "dataset_key": "llmail",
        "path": "sample/normalized_sample/normalized_sample_llmail.jsonl",
        "expected_count": 15,
        "expected_dataset_name": "llmail",
    },
]

OUTPUT_JSONL = "sample/merged/prompt_seed_dataset_llm01.jsonl"
OUTPUT_SUMMARY = "sample/merged/prompt_seed_dataset_llm01_summary.json"

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

EXPECTED_BUCKET_TAGS = ["LLM01_PROMPT_INJECTION"]


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
                raise ValueError(f"[{path}] Each line must be a JSON object.")

            rows.append(row)
    return rows


def write_jsonl(rows: List[Dict[str, Any]], path: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(obj: Dict[str, Any], path: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def validate_row(
    row: Dict[str, Any],
    *,
    dataset_key: str,
    expected_dataset_name: str,
    file_path: str,
    row_index: int,
) -> None:
    missing = REQUIRED_TOP_LEVEL_KEYS - set(row.keys())
    if missing:
        raise ValueError(
            f"[{file_path}] row {row_index}: missing keys: {sorted(missing)}"
        )

    if row["dataset_name"] != expected_dataset_name:
        raise ValueError(
            f"[{file_path}] row {row_index}: dataset_name mismatch "
            f"(expected={expected_dataset_name}, actual={row['dataset_name']})"
        )

    if not isinstance(row["record_id"], str) or not row["record_id"].strip():
        raise ValueError(f"[{file_path}] row {row_index}: invalid record_id")

    if row["bucket_tags"] != EXPECTED_BUCKET_TAGS:
        raise ValueError(
            f"[{file_path}] row {row_index}: bucket_tags mismatch "
            f"(actual={row['bucket_tags']})"
        )

    if not isinstance(row["metadata_json"], dict):
        raise ValueError(f"[{file_path}] row {row_index}: metadata_json must be dict")

    if not isinstance(row["raw_json"], dict):
        raise ValueError(f"[{file_path}] row {row_index}: raw_json must be dict")

    input_primary = row["input_primary"]
    if not isinstance(input_primary, str) or not input_primary.strip():
        raise ValueError(f"[{file_path}] row {row_index}: input_primary is empty")

    metadata = row["metadata_json"]

    if "sample_index" not in metadata:
        raise ValueError(f"[{file_path}] row {row_index}: missing metadata_json.sample_index")

    if "sample_label" not in metadata:
        raise ValueError(f"[{file_path}] row {row_index}: missing metadata_json.sample_label")

    sample_index = metadata["sample_index"]
    sample_label = metadata["sample_label"]

    if not isinstance(sample_index, int):
        raise ValueError(f"[{file_path}] row {row_index}: sample_index must be int")

    if not isinstance(sample_label, str) or not sample_label.startswith(f"{dataset_key}_"):
        raise ValueError(
            f"[{file_path}] row {row_index}: invalid sample_label ({sample_label})"
        )


def validate_file(
    *,
    dataset_key: str,
    file_path: str,
    expected_count: int,
    expected_dataset_name: str,
) -> Dict[str, Any]:
    rows = load_jsonl(file_path)

    if len(rows) != expected_count:
        raise ValueError(
            f"[{file_path}] row count mismatch "
            f"(expected={expected_count}, actual={len(rows)})"
        )

    record_ids = set()
    sample_indices = []
    sample_labels = set()

    for idx, row in enumerate(rows, start=1):
        validate_row(
            row,
            dataset_key=dataset_key,
            expected_dataset_name=expected_dataset_name,
            file_path=file_path,
            row_index=idx,
        )

        rid = row["record_id"]
        if rid in record_ids:
            raise ValueError(f"[{file_path}] duplicate record_id: {rid}")
        record_ids.add(rid)

        md = row["metadata_json"]
        sample_indices.append(md["sample_index"])

        label = md["sample_label"]
        if label in sample_labels:
            raise ValueError(f"[{file_path}] duplicate sample_label: {label}")
        sample_labels.add(label)

    expected_indices = list(range(1, len(rows) + 1))
    if sorted(sample_indices) != expected_indices:
        raise ValueError(
            f"[{file_path}] sample_index sequence mismatch "
            f"(expected={expected_indices}, actual={sorted(sample_indices)})"
        )

    return {
        "dataset_key": dataset_key,
        "file_path": file_path,
        "row_count": len(rows),
        "record_ids": record_ids,
        "rows": rows,
    }


def main() -> None:
    merged_rows: List[Dict[str, Any]] = []
    global_record_ids = set()
    dataset_summaries = []

    for item in INPUT_FILES:
        result = validate_file(
            dataset_key=item["dataset_key"],
            file_path=item["path"],
            expected_count=item["expected_count"],
            expected_dataset_name=item["expected_dataset_name"],
        )

        for row in result["rows"]:
            rid = row["record_id"]
            if rid in global_record_ids:
                raise ValueError(f"[MERGE] duplicate record_id across files: {rid}")
            global_record_ids.add(rid)

        merged_rows.extend(result["rows"])
        dataset_summaries.append(
            {
                "dataset_key": result["dataset_key"],
                "file_path": result["file_path"],
                "row_count": result["row_count"],
            }
        )

    write_jsonl(merged_rows, OUTPUT_JSONL)

    summary = {
        "total_rows": len(merged_rows),
        "dataset_summaries": dataset_summaries,
        "output_jsonl": OUTPUT_JSONL,
    }
    write_json(summary, OUTPUT_SUMMARY)

    print("[OK] Validation and merge completed.")
    print(f"[INFO] Total merged rows: {len(merged_rows)}")
    print(f"[INFO] Output JSONL: {OUTPUT_JSONL}")
    print(f"[INFO] Output summary: {OUTPUT_SUMMARY}")


if __name__ == "__main__":
    main()
