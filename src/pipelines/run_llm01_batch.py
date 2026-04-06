# src/pipelines/run_llm01_batch.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

from src.config.buckets import LLM01_PROMPT_INJECTION
from src.config.enabled_buckets import ENABLED_BUCKETS
from src.core.registry import OperatorRegistry
from src.core.selector import MetaWeightedSelector
from src.core.rng import derive_rng


INPUT_PATH = Path("data/inputs/mutation_seeds_llm01.jsonl")
OUTPUT_PATH = Path("data/outputs/runs/run_llm01_batch.jsonl")
ATTEMPT_LOG_PATH = Path("data/outputs/runs/run_llm01_batch_attempts.jsonl")
UNRESOLVED_PATH = Path("data/outputs/runs/run_llm01_batch_unresolved.jsonl")

DEFAULT_STRENGTH = 2
DEFAULT_RISK_MAX = "HIGH"
DEFAULT_SEED_BASE = 1001

CHILDREN_PER_SEED = 2
MAX_ATTEMPTS_PER_SEED = 8
STRICT_REQUIRE_COMPLETE = True


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


def is_target_seed(row: Dict[str, Any]) -> bool:
    if not row.get("is_mutable", False):
        return False

    bucket_tags = row.get("bucket_tags", [])
    if not isinstance(bucket_tags, list):
        return False

    if LLM01_PROMPT_INJECTION not in bucket_tags:
        return False

    target_text = row.get("mutation_target_text")
    if not isinstance(target_text, str) or not target_text.strip():
        return False

    return True


def map_surface(raw_surface: Any) -> str:
    if raw_surface is None:
        return "PROMPT_TEXT"

    s = str(raw_surface).strip().lower()

    if s in {"prompt_text", "email_body", "body", "text", "user_prompt"}:
        return "PROMPT_TEXT"

    if s in {"system_message", "system", "developer_message"}:
        return "SYSTEM_MESSAGE"

    if s in {"tool_call", "toolcall_json", "tool_arguments"}:
        return "TOOL_CALL"

    return "PROMPT_TEXT"


def build_ctx(
    row: Dict[str, Any],
    *,
    strength: int,
    desired_child_index: int,
    attempt_index: int,
) -> Dict[str, Any]:
    return {
        "record_id": row.get("record_id"),
        "bucket_id": LLM01_PROMPT_INJECTION,
        "surface": map_surface(row.get("attack_surface")),
        "mutation_target_role": row.get("mutation_target_role"),
        "source_format": row.get("source_format"),
        "strength": strength,
        "desired_child_index": desired_child_index,
        "attempt_index": attempt_index,
        "constraints": row.get("constraints", {}),
        "raw_row": row,
    }


def main() -> None:
    if LLM01_PROMPT_INJECTION not in ENABLED_BUCKETS:
        raise RuntimeError(
            f"{LLM01_PROMPT_INJECTION} is not enabled. "
            f"Current ENABLED_BUCKETS={ENABLED_BUCKETS}"
        )

    seeds = load_jsonl(INPUT_PATH)

    registry = OperatorRegistry()
    loaded = registry.load_from_package("src.operators", strict=False)

    print(f"[info] loaded operators: {loaded}")
    print(f"[info] load_errors: {len(registry.load_errors)}")
    if registry.load_errors:
        for modname, reason in registry.load_errors:
            print(f"  - {modname}: {reason}")

    selector = MetaWeightedSelector(registry=registry)

    success_rows: List[Dict[str, Any]] = []
    attempt_logs: List[Dict[str, Any]] = []
    unresolved_rows: List[Dict[str, Any]] = []

    ok_children_count = 0
    failed_attempt_count = 0

    stats_by_bucket: Dict[str, Dict[str, Any]] = {
        LLM01_PROMPT_INJECTION: {
            "_recent_ops": []
        }
    }

    target_rows = [row for row in seeds if is_target_seed(row)]

    print(f"[info] total input rows     : {len(seeds)}")
    print(f"[info] target seed rows    : {len(target_rows)}")
    print(f"[info] children per seed   : {CHILDREN_PER_SEED}")
    print(f"[info] max attempts / seed : {MAX_ATTEMPTS_PER_SEED}")
    print(f"[info] risk_max            : {DEFAULT_RISK_MAX}")

    for row in target_rows:
        record_id = str(row.get("record_id", "unknown"))
        seed_text = row["mutation_target_text"]
        base_strength = int(row.get("strength", DEFAULT_STRENGTH))
        mapped_surface = map_surface(row.get("attack_surface"))

        ok_for_seed = 0
        attempt_index = 0
        used_success_ops: Set[str] = set()

        while ok_for_seed < CHILDREN_PER_SEED and attempt_index < MAX_ATTEMPTS_PER_SEED:
            attempt_index += 1
            desired_child_index = ok_for_seed + 1

            testcase_id = f"{record_id}:child{desired_child_index}:attempt{attempt_index}"
            rng = derive_rng(DEFAULT_SEED_BASE, testcase_id)

            ctx = build_ctx(
                row=row,
                strength=base_strength,
                desired_child_index=desired_child_index,
                attempt_index=attempt_index,
            )

            candidates = registry.filter(
                bucket_id=LLM01_PROMPT_INJECTION,
                surface=mapped_surface,
                risk_max=DEFAULT_RISK_MAX,
            )

            if not candidates:
                attempt_logs.append({
                    "parent_record_id": record_id,
                    "desired_child_index": desired_child_index,
                    "attempt_index": attempt_index,
                    "attack_surface": row.get("attack_surface"),
                    "mapped_surface": mapped_surface,
                    "status": "SKIPPED",
                    "reason": "no_candidates_after_filter",
                })
                failed_attempt_count += 1
                break

            selection = selector.choose(
                bucket_id=LLM01_PROMPT_INJECTION,
                surface=mapped_surface,
                rng=rng,
                strength=base_strength,
                risk_max=DEFAULT_RISK_MAX,
                stats_by_bucket=stats_by_bucket,
            )

            if selection is None:
                attempt_logs.append({
                    "parent_record_id": record_id,
                    "desired_child_index": desired_child_index,
                    "attempt_index": attempt_index,
                    "attack_surface": row.get("attack_surface"),
                    "mapped_surface": mapped_surface,
                    "status": "SKIPPED",
                    "reason": "selector_returned_none",
                })
                failed_attempt_count += 1
                continue

            # 이미 성공한 child에서 사용한 operator는 가급적 재사용하지 않음
            if selection.op_id in used_success_ops and len(candidates) > len(used_success_ops):
                attempt_logs.append({
                    "parent_record_id": record_id,
                    "desired_child_index": desired_child_index,
                    "attempt_index": attempt_index,
                    "attack_surface": row.get("attack_surface"),
                    "mapped_surface": mapped_surface,
                    "selected_op_id": selection.op_id,
                    "status": "RETRY",
                    "reason": "duplicate_success_operator_for_same_parent",
                })
                continue

            result = registry.apply(
                op_id=selection.op_id,
                seed_text=seed_text,
                ctx=ctx,
                rng=rng,
            )

            attempt_logs.append({
                "parent_record_id": record_id,
                "desired_child_index": desired_child_index,
                "attempt_index": attempt_index,
                "attack_surface": row.get("attack_surface"),
                "mapped_surface": mapped_surface,
                "selected_op_id": selection.op_id,
                "selection_reason": selection.reason,
                "selection_weight": selection.weight,
                "status": result.status,
                "error": result.error,
                "trace": result.trace,
            })

            if result.status != "OK":
                failed_attempt_count += 1
                continue

            child_record_id = f"{record_id}__child_{desired_child_index:02d}"

            recent_ops = stats_by_bucket[LLM01_PROMPT_INJECTION]["_recent_ops"]
            recent_ops.append(selection.op_id)
            if len(recent_ops) > 20:
                stats_by_bucket[LLM01_PROMPT_INJECTION]["_recent_ops"] = recent_ops[-20:]

            success_rows.append({
                "parent_record_id": record_id,
                "child_record_id": child_record_id,
                "child_index": desired_child_index,
                "attempt_index": attempt_index,
                "bucket_id": LLM01_PROMPT_INJECTION,
                "attack_surface": row.get("attack_surface"),
                "mapped_surface": mapped_surface,
                "mutation_target_role": row.get("mutation_target_role"),
                "source_format": row.get("source_format"),
                "selected_op_id": selection.op_id,
                "selection_reason": selection.reason,
                "selection_weight": selection.weight,
                "status": result.status,
                "child_text": result.child_text,
                "trace": result.trace,
                "error": result.error,
            })

            used_success_ops.add(selection.op_id)
            ok_for_seed += 1
            ok_children_count += 1

        if ok_for_seed < CHILDREN_PER_SEED:
            unresolved_rows.append({
                "parent_record_id": record_id,
                "attack_surface": row.get("attack_surface"),
                "mapped_surface": mapped_surface,
                "ok_children_obtained": ok_for_seed,
                "required_children": CHILDREN_PER_SEED,
                "attempts_used": attempt_index,
                "max_attempts": MAX_ATTEMPTS_PER_SEED,
            })

    save_jsonl(OUTPUT_PATH, success_rows)
    save_jsonl(ATTEMPT_LOG_PATH, attempt_logs)
    save_jsonl(UNRESOLVED_PATH, unresolved_rows)

    expected_ok_rows = len(target_rows) * CHILDREN_PER_SEED

    print("=" * 80)
    print("[done] run_llm01_batch")
    print(f"input_path        : {INPUT_PATH}")
    print(f"output_path       : {OUTPUT_PATH}")
    print(f"attempt_log_path  : {ATTEMPT_LOG_PATH}")
    print(f"unresolved_path   : {UNRESOLVED_PATH}")
    print(f"total_rows        : {len(seeds)}")
    print(f"target_rows       : {len(target_rows)}")
    print(f"expected_ok_rows  : {expected_ok_rows}")
    print(f"written_ok_rows   : {len(success_rows)}")
    print(f"failed_attempts   : {failed_attempt_count}")
    print(f"unresolved_seeds  : {len(unresolved_rows)}")
    print("=" * 80)

    if STRICT_REQUIRE_COMPLETE and len(success_rows) != expected_ok_rows:
        raise RuntimeError(
            "Failed to guarantee 2 OK children per seed. "
            f"expected_ok_rows={expected_ok_rows}, written_ok_rows={len(success_rows)}, "
            f"unresolved_seeds={len(unresolved_rows)}"
        )


if __name__ == "__main__":
    main()
