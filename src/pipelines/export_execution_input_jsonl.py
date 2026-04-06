# src/pipelines/export_execution_input_jsonl.py
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any, Dict, Iterable, List


INPUT_PATH = Path("data/outputs/runs/run_llm01_batch.jsonl")
OUTPUT_PATH = Path("data/outputs/final/execution_input_llm01.jsonl")

SCHEMA_VERSION = "execution_input.v0.1"
SEED_PREFIX = "llm01"


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


def save_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def build_seed_id_map(rows: List[Dict[str, Any]]) -> Dict[str, str]:
    parent_to_seed_id: Dict[str, str] = {}
    next_idx = 1

    for row in rows:
        parent_id = str(row["parent_record_id"])
        if parent_id not in parent_to_seed_id:
            parent_to_seed_id[parent_id] = f"{SEED_PREFIX}_{next_idx:06d}"
            next_idx += 1

    return parent_to_seed_id


def ensure_trace_list(
    trace_obj: Any,
    *,
    prompt_text: str,
    op_id_fallback: str,
    status_fallback: str,
    novelty_payload: Dict[str, Any],
) -> List[Dict[str, Any]]:
    if isinstance(trace_obj, list):
        trace_list = trace_obj
    elif isinstance(trace_obj, dict):
        trace_list = [trace_obj]
    else:
        trace_list = [{
            "op_id": op_id_fallback,
            "status": status_fallback,
            "params": {},
            "len_before": len(prompt_text),
            "len_after": len(prompt_text),
        }]

    if not trace_list:
        trace_list = [{
            "op_id": op_id_fallback,
            "status": status_fallback,
            "params": {},
            "len_before": len(prompt_text),
            "len_after": len(prompt_text),
        }]

    # 첫 trace에 novelty 추가
    first = trace_list[0]
    if not isinstance(first, dict):
        first = {
            "op_id": op_id_fallback,
            "status": status_fallback,
            "params": {},
            "len_before": len(prompt_text),
            "len_after": len(prompt_text),
        }
        trace_list[0] = first

    params = first.get("params")
    if not isinstance(params, dict):
        params = {}
        first["params"] = params

    params["novelty"] = novelty_payload
    first.setdefault("op_id", op_id_fallback)
    first.setdefault("status", status_fallback)
    first.setdefault("len_after", len(prompt_text))

    return trace_list


def main() -> None:
    rows = load_jsonl(INPUT_PATH)

    # 현재 배치 출력은 OK row만 저장하는 구조이지만,
    # 안전하게 한 번 더 필터링
    ok_rows = [row for row in rows if row.get("status") == "OK"]

    if not ok_rows:
        raise RuntimeError("No OK rows found in batch output.")

    parent_to_seed_id = build_seed_id_map(ok_rows)

    final_rows: List[Dict[str, Any]] = []

    seen_hashes = set()
    seen_hits = 0
    total_seen = 0
    unique_seen = 0

    for row in ok_rows:
        parent_record_id = str(row["parent_record_id"])
        seed_id = parent_to_seed_id[parent_record_id]

        child_index = int(row.get("child_index", 1))
        testcase_id = f"{seed_id}::{child_index:03d}"

        prompt_text = str(row["child_text"])
        bucket_id = str(row["bucket_id"])
        surface = str(row.get("mapped_surface") or row.get("surface") or "PROMPT_TEXT")
        last_status = str(row["status"])
        selected_op_id = str(row.get("selected_op_id", "unknown_operator"))

        # novelty 계산 (전역 누적 기준)
        total_seen += 1
        h = hash_text(prompt_text)
        seen_before = h in seen_hashes
        if seen_before:
            seen_hits += 1
        else:
            seen_hashes.add(h)
            unique_seen += 1

        novelty_payload = {
            "seen_before": seen_before,
            "novelty": {
                "total": total_seen,
                "unique": unique_seen,
                "seen_hits": seen_hits,
                "unique_ratio": round(unique_seen / total_seen, 6),
            },
        }

        trace_list = ensure_trace_list(
            trace_obj=row.get("trace"),
            prompt_text=prompt_text,
            op_id_fallback=selected_op_id,
            status_fallback=last_status,
            novelty_payload=novelty_payload,
        )

        final_rows.append({
            "schema_version": SCHEMA_VERSION,
            "testcase_id": testcase_id,
            "seed_id": seed_id,
            "bucket_id": bucket_id,
            "surface": surface,
            "prompt": prompt_text,
            "last_status": last_status,
            "trace": trace_list,
        })

    save_jsonl(OUTPUT_PATH, final_rows)

    # 기본 검증
    unique_seed_ids = {row["seed_id"] for row in final_rows}
    expected_rows = len(unique_seed_ids) * 2

    print("=" * 80)
    print("[done] export_execution_input_jsonl")
    print(f"input_path        : {INPUT_PATH}")
    print(f"output_path       : {OUTPUT_PATH}")
    print(f"ok_input_rows     : {len(ok_rows)}")
    print(f"written_rows      : {len(final_rows)}")
    print(f"unique_seed_ids   : {len(unique_seed_ids)}")
    print(f"expected_rows_2x  : {expected_rows}")
    print("=" * 80)

    if len(final_rows) != expected_rows:
        raise RuntimeError(
            f"Unexpected final row count: expected {expected_rows}, got {len(final_rows)}"
        )


if __name__ == "__main__":
    main()
