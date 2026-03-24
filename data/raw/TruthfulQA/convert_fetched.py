import json
from pathlib import Path

INPUT_PATH = Path(r"C:\Users\didtj\Desktop\owasp-llm-mutation-engine\data\raw\TruthfulQA\truthful_qa.jsonl")
OUTPUT_PATH = Path(r"C:\Users\didtj\Desktop\owasp-llm-mutation-engine\data\normalized\normalized_truthfulqa_data.jsonl")

DATASET_NAME = "TruthfulQA"
SUBSET_OR_SPLIT = "train"
CATEGORY_PRIMARY = "factuality_classification"
SOURCE_FORMAT = "normalized_v1"
BUCKET_TAGS = ["LLM09"]

def convert_label_to_bool(question_type: str):
    # 'Adversarial' type = non-factual (false), other types = factual (true)
    if question_type == "Adversarial":
        return False
    return True


def normalize_row(row: dict, idx: int) -> dict:
    return {
        "dataset_name": DATASET_NAME,
        "subset_or_split": SUBSET_OR_SPLIT,
        "record_id": f"truthfulqa_{idx:06d}",
        "input_primary": row.get("question"),
        "input_secondary": None,
        "context_text": None,
        "candidate_output": row.get("best_answer"),
        "reference_output": " | ".join(row.get("correct_answers", [])),
        "label_binary": convert_label_to_bool(row.get("type")),
        "category_primary": CATEGORY_PRIMARY,
        "category_multilabel_json": None,
        "metadata_json": {
            "incorrect_answers": row.get("incorrect_answers", []),
            "source": row.get("source")
        },
        "raw_json": row,
        "bucket_tags": BUCKET_TAGS,
        "source_format": SOURCE_FORMAT,
    }


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"입력 파일 없음: {INPUT_PATH}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with INPUT_PATH.open("r", encoding="utf-8") as fin, OUTPUT_PATH.open("w", encoding="utf-8") as fout:
        for idx, line in enumerate(fin, start=1):
            line = line.strip()
            if not line:
                continue  # Skip empty lines

            try:
                row = json.loads(line)
                normalized = normalize_row(row, idx)
                fout.write(json.dumps(normalized, ensure_ascii=False) + "\n")
                count += 1
            except json.JSONDecodeError as e:
                # Log the problematic line and the error
                print(f"Error parsing line {idx}: {line}")
                print(f"JSONDecodeError: {e}")
            except Exception as e:
                # Handle any other errors
                print(f"Unexpected error with line {idx}: {line}")
                print(f"Error: {e}")

    print(f"완료: {count}개 변환됨")
    print(f"저장 위치: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()