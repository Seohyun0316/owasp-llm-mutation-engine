# scripts/demo_cli.py
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.core.registry import OperatorRegistry
from src.core.mutator import Mutator
from src.core.selector import MetaWeightedSelector  # 파일명이 다르면 여기만 맞춰주세요
from src.core.novelty import NoveltyTracker


def main() -> int:
    ap = argparse.ArgumentParser(description="Mutation Engine demo: 1 seed -> N children")
    ap.add_argument("--seed", type=str, required=True, help="seed text (or @path to file)")
    ap.add_argument("--bucket", type=str, default="LLM01_PROMPT_INJECTION")
    ap.add_argument("--surface", type=str, default="PROMPT_TEXT")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--k", type=int, default=2)
    ap.add_argument("--strength", type=int, default=3)
    ap.add_argument("--seed_base", type=int, default=1337)
    ap.add_argument("--risk_max", type=str, default=None)
    ap.add_argument("--max_chars", type=int, default=8000)
    ap.add_argument("--schema_mode", action="store_true")
    ap.add_argument("--placeholder", type=str, default="N/A")
    ap.add_argument("--out", type=str, default="", help="optional output json path")
    args = ap.parse_args()

    seed = args.seed
    if seed.startswith("@"):
        p = Path(seed[1:])
        seed = p.read_text(encoding="utf-8")

    reg = OperatorRegistry()
    reg.load_from_package("src.operators", strict=True)

    novelty = NoveltyTracker()
    selector = MetaWeightedSelector(registry=reg, novelty=novelty, seen_penalty=0.2)
    m = Mutator(reg, selector=selector)

    constraints = {
        "max_chars": args.max_chars,
        "schema_mode": bool(args.schema_mode),
        "placeholder": args.placeholder,
    }

    stats_by_bucket: dict = {}

    outs = m.generate_children(
        seed_text=seed,
        bucket_id=args.bucket,
        surface=args.surface,
        n=args.n,
        k=args.k,
        seed_base=args.seed_base,
        strength=args.strength,
        risk_max=args.risk_max,
        constraints=constraints,
        metadata={"seed_id": "demo_seed"},
        stats_by_bucket=stats_by_bucket,
    )

    # novelty 통계(버킷별)
    novelty_snap = novelty.snapshot()
    bucket_novelty = stats_by_bucket.get(args.bucket, {}).get("_novelty", {})

    payload = {
        "bucket_id": args.bucket,
        "surface": args.surface,
        "n": args.n,
        "k": args.k,
        "strength": args.strength,
        "constraints": constraints,
        "recent_ops": stats_by_bucket.get(args.bucket, {}).get("_recent_ops", []),
        "novelty": {
            # authoritative: tracker snapshot
            "by_bucket": novelty_snap,
            # convenience: current bucket only (stats_by_bucket mirror)
            "current_bucket": bucket_novelty,
        },
        "children": [
            {
                "child_text": o.child_text,
                "last_status": o.last_status,
                "mutation_trace": o.mutation_trace,
            }
            for o in outs
        ],
    }

    if args.out:
        Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] wrote: {args.out}")
        nb = payload["novelty"]["current_bucket"]
        if isinstance(nb, dict) and nb:
            print(
                "[NOVELTY]",
                f"total={nb.get('total')}",
                f"unique={nb.get('unique')}",
                f"seen_hits={nb.get('seen_hits')}",
                f"unique_ratio={nb.get('unique_ratio')}",
            )
    else:
        nb = payload["novelty"]["current_bucket"]
        print(
            "[NOVELTY]",
            f"total={nb.get('total')}",
            f"unique={nb.get('unique')}",
            f"seen_hits={nb.get('seen_hits')}",
            f"unique_ratio={nb.get('unique_ratio')}",
        )
        for i, o in enumerate(outs):
            print(f"\n=== child[{i}] status={o.last_status} len={len(o.child_text)} ===")
            print(o.child_text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
