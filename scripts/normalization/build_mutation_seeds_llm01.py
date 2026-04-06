import json
from pathlib import Path
from typing import Dict, List, Any


INPUT_JSONL = "sample/merged/prompt_seed_dataset_llm01.jsonl"
OUTPUT_JSONL = "sample/merged/mutation_seeds_llm01.jsonl"
OUTPUT_SUMMARY = "sample/merged/mutation_seeds_llm01_summary.json"

ALLOWED_DATASETS = {
    "advbench",
    "hackaprompt",
    "do_not_answer",
    "beavertails",
    "llmail",
}

ALLOWED_ATTACK_SURFACES = {
    "prompt_text",
    "email_body",
}

EXPECTED_BUCKET_TAGS = ["LLM01_PROMPT_INJECTION"]
EXPECTED_SOURCE_FORMAT = "mutation_seed_v1"
EXPECTED_MUTATION_TARGET_ROLE = "attacker_controlled_input"


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


def choose_attack_surface(row: Dict[str, Any]) -> str:
    dataset_name = row.get("dataset_name")

    if dataset_name == "llmail":
        return "email_body"

    return "prompt_text"


def choose_mutation_target_text(row: Dict[str, Any]) -> str:
    value = row.get("input_primary")

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"mutation_target_text cannot be empty for record_id={row.get('record_id')}"
        )

    return value


def build_mutation_seed(row: Dict[str, Any]) -> Dict[str, Any]:
    dataset_name = row.get("dataset_name")
    if dataset_name not in ALLOWED_DATASETS:
        raise ValueError(
            f"Unsupported dataset_name: {dataset_name} / record_id={row.get('record_id')}"
        )

    mutation_target_text = choose_mutation_target_text(row)
    attack_surface = choose_attack_surface(row)

    out = dict(row)
    out["bucket_tags"] = EXPECTED_BUCKET_TAGS
    out["attack_surface"] = attack_surface
    out["mutation_target_text"] = mutation_target_text
    out["mutation_target_role"] = EXPECTED_MUTATION_TARGET_ROLE
    out["is_mutable"] = True
    out["source_format"] = EXPECTED_SOURCE_FORMAT

    return out


def validate_mutation_seed(row: Dict[str, Any], row_index: int) -> None:
    required_keys = {
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

    missing = required_keys - set(row.keys())
    if missing:
        raise ValueError(f"row {row_index}: missing keys: {sorted(missing)}")

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

    if not isinstance(row["is_mutable"], bool):
        raise ValueError(f"row {row_index}: is_mutable must be bool")

    if row["source_format"] != EXPECTED_SOURCE_FORMAT:
        raise ValueError(
            f"row {row_index}: source_format mismatch (actual={row['source_format']})"
        )

    mutation_target_text = row["mutation_target_text"]
    if not isinstance(mutation_target_text, str) or not mutation_target_text.strip():
        raise ValueError(f"row {row_index}: mutation_target_text is empty")

    if not isinstance(row["record_id"], str) or not row["record_id"].strip():
        raise ValueError(f"row {row_index}: invalid record_id")

    if not isinstance(row["metadata_json"], dict):
        raise ValueError(f"row {row_index}: metadata_json must be dict")

    if not isinstance(row["raw_json"], dict):
        raise ValueError(f"row {row_index}: raw_json must be dict")


def main() -> None:
    rows = load_jsonl(INPUT_JSONL)

    mutation_rows: List[Dict[str, Any]] = []
    record_ids = set()

    dataset_counts: Dict[str, int] = {}
    attack_surface_counts: Dict[str, int] = {}

    for idx, row in enumerate(rows, start=1):
        mutation_row = build_mutation_seed(row)
        validate_mutation_seed(mutation_row, idx)

        rid = mutation_row["record_id"]
        if rid in record_ids:
            raise ValueError(f"duplicate record_id detected: {rid}")
        record_ids.add(rid)

        dataset_name = mutation_row["dataset_name"]
        dataset_counts[dataset_name] = dataset_counts.get(dataset_name, 0) + 1

        attack_surface = mutation_row["attack_surface"]
        attack_surface_counts[attack_surface] = attack_surface_counts.get(attack_surface, 0) + 1

        mutation_rows.append(mutation_row)

    write_jsonl(mutation_rows, OUTPUT_JSONL)

    summary = {
        "total_rows": len(mutation_rows),
        "dataset_counts": dataset_counts,
        "attack_surface_counts": attack_surface_counts,
        "output_jsonl": OUTPUT_JSONL,
    }
    write_json(summary, OUTPUT_SUMMARY)

    print("[OK] Mutation seed build completed.")
    print(f"[INFO] Total rows: {len(mutation_rows)}")
    print(f"[INFO] Output JSONL: {OUTPUT_JSONL}")
    print(f"[INFO] Output summary: {OUTPUT_SUMMARY}")


if __name__ == "__main__":
    main()
