import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


# ============================================================
# 공통 설정
# ============================================================

DEFAULT_BUCKET_TAGS = ["LLM01_PROMPT_INJECTION"]


# ============================================================
# JSONL I/O
# ============================================================

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
                raise ValueError(f"JSON parse error in {path}, line {line_num}: {e}") from e
            if not isinstance(row, dict):
                raise ValueError(f"Each JSONL row must be an object/dict. Found: {type(row)}")
            rows.append(row)
    return rows


def write_jsonl(rows: Iterable[Dict[str, Any]], path: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


# ============================================================
# 유틸
# ============================================================

def stable_hash(text: str, length: int = 10) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


def make_record_id(dataset_name: str, key_text: str) -> str:
    return f"{dataset_name}_sample_{stable_hash(key_text)}"


def get_raw_json(row: Dict[str, Any]) -> Dict[str, Any]:
    raw = row.get("raw_json")
    return raw if isinstance(raw, dict) else {}


def resolve_record_id(row: Dict[str, Any], dataset_name: str, key_obj: Dict[str, Any]) -> str:
    existing = row.get("record_id")
    if isinstance(existing, str) and existing.strip():
        return existing.strip()

    key_text = json.dumps(key_obj, ensure_ascii=False, sort_keys=True)
    return make_record_id(dataset_name, key_text)


def base_normalized_row(
    *,
    dataset_name: str,
    subset_or_split: str,
    record_id: str,
    input_primary: Optional[str] = None,
    input_secondary: Optional[str] = None,
    context_text: Optional[str] = None,
    candidate_output: Optional[str] = None,
    reference_output: Optional[str] = None,
    label_binary: Optional[Any] = None,
    category_primary: Optional[Any] = None,
    category_multilabel_json: Optional[Any] = None,
    metadata_json: Optional[Any] = None,
    raw_json: Optional[Any] = None,
    bucket_tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "dataset_name": dataset_name,
        "subset_or_split": subset_or_split,
        "record_id": record_id,
        "input_primary": input_primary,
        "input_secondary": input_secondary,
        "context_text": context_text,
        "candidate_output": candidate_output,
        "reference_output": reference_output,
        "label_binary": label_binary,
        "category_primary": category_primary,
        "category_multilabel_json": category_multilabel_json,
        "metadata_json": metadata_json if isinstance(metadata_json, dict) else {},
        "raw_json": raw_json if isinstance(raw_json, dict) else {},
        "bucket_tags": bucket_tags if bucket_tags is not None else DEFAULT_BUCKET_TAGS,
    }


# ============================================================
# 데이터셋별 정규화 함수
# ============================================================

def normalize_do_not_answer(row: Dict[str, Any], subset_or_split: str) -> Dict[str, Any]:
    """
    tagged sample 구조 반영:
    top-level:
      - record_id
      - source_dataset
      - prompt_text
      - auto_tags
      - review_status
      - raw_json
    raw_json:
      - question
      - risk_area
      - types_of_harm
      - specific_harms
      - 기타 모델 응답 필드들
    """
    raw = get_raw_json(row)
    auto_tags = row.get("auto_tags", {}) if isinstance(row.get("auto_tags"), dict) else {}

    question = raw.get("question") or row.get("prompt_text")
    risk_area = raw.get("risk_area")

    record_id = resolve_record_id(
        row,
        "do_not_answer",
        {
            "prompt_text": row.get("prompt_text"),
            "question": question,
            "risk_area": risk_area,
        },
    )

    category_multilabel = {
        "types_of_harm": raw.get("types_of_harm"),
        "specific_harms": raw.get("specific_harms"),
    }

    metadata = {
        "source_dataset": row.get("source_dataset"),
        "prompt_text": row.get("prompt_text"),
        "auto_tags": auto_tags,
        "review_status": row.get("review_status"),
    }
    metadata = {k: v for k, v in metadata.items() if v is not None}

    return base_normalized_row(
        dataset_name="do_not_answer",
        subset_or_split=subset_or_split,
        record_id=record_id,
        input_primary=question,
        input_secondary=None,
        context_text=None,
        candidate_output=None,
        reference_output=None,
        label_binary=None,
        category_primary=risk_area,
        category_multilabel_json=category_multilabel,
        metadata_json=metadata,
        raw_json=row,
    )


def normalize_advbench(row: Dict[str, Any], subset_or_split: str) -> Dict[str, Any]:
    raw = get_raw_json(row)
    auto_tags = row.get("auto_tags", {}) if isinstance(row.get("auto_tags"), dict) else {}

    goal = raw.get("goal") or row.get("prompt_text")
    target = raw.get("target")

    record_id = resolve_record_id(
        row,
        "advbench",
        {
            "prompt_text": row.get("prompt_text"),
            "goal": goal,
            "target": target,
        },
    )

    metadata = {
        "source_dataset": row.get("source_dataset"),
        "prompt_text": row.get("prompt_text"),
        "auto_tags": auto_tags,
        "review_status": row.get("review_status"),
        "additional_types": row.get("additional_types"),
    }
    metadata = {k: v for k, v in metadata.items() if v is not None}

    return base_normalized_row(
        dataset_name="advbench",
        subset_or_split=subset_or_split,
        record_id=record_id,
        input_primary=goal,
        input_secondary=None,
        context_text=None,
        candidate_output=None,
        reference_output=target,
        label_binary=None,
        category_primary=None,
        category_multilabel_json=None,
        metadata_json=metadata,
        raw_json=row,
    )


def normalize_beavertails(row: Dict[str, Any], subset_or_split: str) -> Dict[str, Any]:
    """
    기대 입력 예시:
    {
        "prompt": ...,
        "response": ...,
        "is_safe": ...,
        "category": {...},
        "attack_type": ...
    }
    """
    raw = get_raw_json(row)

    prompt = row.get("prompt") or raw.get("prompt")
    response = row.get("response") or raw.get("response")

    is_safe = row.get("is_safe")
    if is_safe is None:
        is_safe = raw.get("is_safe")

    category = row.get("category")
    if category is None:
        category = raw.get("category")

    attack_type = row.get("attack_type")
    if attack_type is None:
        attack_type = raw.get("attack_type")

    record_id = resolve_record_id(
        row,
        "beavertails",
        {
            "prompt": prompt,
            "response": response,
            "is_safe": is_safe,
        },
    )

    metadata = {}
    if attack_type is not None:
        metadata["attack_type"] = attack_type
    if row.get("source_dataset") is not None:
        metadata["source_dataset"] = row.get("source_dataset")

    return base_normalized_row(
        dataset_name="beavertails",
        subset_or_split=subset_or_split,
        record_id=record_id,
        input_primary=prompt,
        input_secondary=None,
        context_text=None,
        candidate_output=response,
        reference_output=None,
        label_binary=is_safe,
        category_primary=None,
        category_multilabel_json=category,
        metadata_json=metadata,
        raw_json=row,
    )


def normalize_hackaprompt(row: Dict[str, Any], subset_or_split: str) -> Dict[str, Any]:
    raw = get_raw_json(row)
    auto_tags = row.get("auto_tags", {}) if isinstance(row.get("auto_tags"), dict) else {}

    user_input = raw.get("user_input") or row.get("prompt_text") or raw.get("prompt")
    prompt = raw.get("prompt")
    completion = raw.get("completion")
    expected_completion = raw.get("expected_completion")
    correct = raw.get("correct")

    record_id = resolve_record_id(
        row,
        "hackaprompt",
        {
            "prompt_text": row.get("prompt_text"),
            "raw_prompt": prompt,
            "raw_user_input": user_input,
        },
    )

    metadata = {
        "source_dataset": row.get("source_dataset"),
        "prompt_text": row.get("prompt_text"),
        "auto_tags": auto_tags,
        "review_status": row.get("review_status"),
        "additional_types": row.get("additional_types"),
        "level": raw.get("level"),
        "model": raw.get("model"),
        "token_count": raw.get("token_count"),
        "score": raw.get("score"),
    }
    metadata = {k: v for k, v in metadata.items() if v is not None}

    return base_normalized_row(
        dataset_name="hackaprompt",
        subset_or_split=subset_or_split,
        record_id=record_id,
        input_primary=user_input,
        input_secondary=None,
        context_text=prompt,
        candidate_output=completion,
        reference_output=expected_completion,
        label_binary=correct,
        category_primary=None,
        category_multilabel_json=None,
        metadata_json=metadata,
        raw_json=row,
    )


def normalize_llmail(row: Dict[str, Any], subset_or_split: str) -> Dict[str, Any]:
    """
    기대 입력 예시:
    {
        "body": ...,
        "subject": ...,
        "scenario": ...,
        "output": ...,
        "objectives": ...,
        "team_id": ...,
        "timestamp": ... / "timestamps": ...
    }
    """
    raw = get_raw_json(row)

    body = row.get("body") or raw.get("body")
    subject = row.get("subject") or raw.get("subject")
    scenario = row.get("scenario") or raw.get("scenario")
    output = row.get("output") or raw.get("output")

    record_id = resolve_record_id(
        row,
        "llmail",
        {
            "subject": subject,
            "body": body,
            "scenario": scenario,
        },
    )

    metadata = {
        "objectives": row.get("objectives") or raw.get("objectives"),
        "team_id": row.get("team_id") or raw.get("team_id"),
        "timestamp": row.get("timestamp") or raw.get("timestamp"),
        "timestamps": row.get("timestamps") or raw.get("timestamps"),
    }
    metadata = {k: v for k, v in metadata.items() if v is not None}

    return base_normalized_row(
        dataset_name="llmail",
        subset_or_split=subset_or_split,
        record_id=record_id,
        input_primary=body,
        input_secondary=subject,
        context_text=scenario,
        candidate_output=output,
        reference_output=None,
        label_binary=None,
        category_primary=None,
        category_multilabel_json=None,
        metadata_json=metadata,
        raw_json=row,
    )


# ============================================================
# 라우터
# ============================================================

NORMALIZER_MAP = {
    "do_not_answer": normalize_do_not_answer,
    "advbench": normalize_advbench,
    "beavertails": normalize_beavertails,
    "hackaprompt": normalize_hackaprompt,
    "llmail": normalize_llmail,
}


# ============================================================
# 검증
# ============================================================

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


def validate_normalized_row(row: Dict[str, Any]) -> None:
    missing = REQUIRED_TOP_LEVEL_KEYS - set(row.keys())
    if missing:
        raise ValueError(f"Normalized row missing required keys: {sorted(missing)}")

    if not isinstance(row["record_id"], str) or not row["record_id"]:
        raise ValueError("record_id must be a non-empty string")

    if not isinstance(row["bucket_tags"], list):
        raise ValueError("bucket_tags must be a list")

    if not isinstance(row["metadata_json"], dict):
        raise ValueError("metadata_json must be a dict")

    if not isinstance(row["raw_json"], dict):
        raise ValueError("raw_json must be a dict")


# ============================================================
# 메인
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize dataset-wise sampled raw JSONL into normalized_sample JSONL."
    )
    parser.add_argument("--dataset", required=True, choices=list(NORMALIZER_MAP.keys()))
    parser.add_argument("--input", required=True, help="Path to sampled_raw_*.jsonl")
    parser.add_argument("--output", required=True, help="Path to normalized_sample_*.jsonl")
    parser.add_argument("--subset", default="sample", help="subset_or_split value")
    args = parser.parse_args()

    rows = load_jsonl(args.input)
    print(f"[INFO] Loaded rows: {len(rows)}")

    normalizer = NORMALIZER_MAP[args.dataset]
    normalized_rows: List[Dict[str, Any]] = []

    seen_record_ids = set()
    duplicate_ids = []

    for idx, row in enumerate(rows, start=1):
        try:
            normalized = normalizer(row, args.subset)

            if not isinstance(normalized.get("metadata_json"), dict):
                normalized["metadata_json"] = {}

            normalized["metadata_json"]["sample_index"] = idx
            normalized["metadata_json"]["sample_label"] = f"{args.dataset}_{idx:07d}"

            validate_normalized_row(normalized)

        except Exception as e:
            raise RuntimeError(f"Normalization failed at row {idx}: {e}") from e

        record_id = normalized["record_id"]
        if record_id in seen_record_ids:
            duplicate_ids.append(record_id)
        seen_record_ids.add(record_id)

        normalized_rows.append(normalized)

    if duplicate_ids:
        dup_preview = duplicate_ids[:10]
        raise RuntimeError(
            f"Duplicate record_id detected: {len(duplicate_ids)}\n"
            f"Examples: {dup_preview}"
        )

    write_jsonl(normalized_rows, args.output)

    print(f"[INFO] Saved normalized rows: {len(normalized_rows)}")
    print(f"[INFO] Output path: {args.output}")
    print("[OK] Normalization completed.")


if __name__ == "__main__":
    main()
