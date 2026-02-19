from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.core.registry import OperatorRegistry
from src.core.mutator import Mutator


DEFAULT_BUCKETS = [
    # 프로젝트에서 실제 사용하는 bucket_id에 맞게 조정하면 된다.
    "PromptInjection",
    "ToolMisuse",
    "DoS",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed-text", default="You are a helpful assistant.")
    ap.add_argument("--surface", default="PROMPT_TEXT")
    ap.add_argument("--seed-base", type=int, default=1337)
    ap.add_argument("--strength", type=int, default=2)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--k", type=int, default=1)
    ap.add_argument("--buckets", nargs="*", default=None)
    ap.add_argument("--out", default="scripts/smoke_out.json")
    args = ap.parse_args()

    reg = OperatorRegistry()
    reg.load_from_package("src.operators", strict=True)

    m = Mutator(reg)

    buckets = args.buckets or DEFAULT_BUCKETS
    results = {"cases": []}

    for b in buckets:
        outs = m.generate_children(
            seed_text=args.seed_text,
            bucket_id=b,
            surface=args.surface,
            n=args.n,
            k=args.k,
            seed_base=args.seed_base,
            strength=args.strength,
            risk_max=None,
            constraints={},
            metadata={"smoke": True},
            stats_by_bucket={},
        )
        results["cases"].append(
            {
                "bucket_id": b,
                "n": len(outs),
                "sample": [
                    {
                        "child_text": o.child_text,
                        "last_status": o.last_status,
                        "trace_len": len(o.mutation_trace) if isinstance(o.mutation_trace, list) else None,
                    }
                    for o in outs[: min(3, len(outs))]
                ],
            }
        )

    Path(args.out).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[smoke] wrote: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
