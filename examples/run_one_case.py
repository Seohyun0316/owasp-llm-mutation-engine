# examples/run_one_case.py
from __future__ import annotations

from src.core.registry import OperatorRegistry
from src.core.mutator import Mutator


def main() -> None:
    registry = OperatorRegistry()
    loaded = registry.load_from_package("src.operators")

    seed_text = "You are a helpful assistant. Explain secure coding practices."
    bucket_id = "LLM01_PROMPT_INJECTION"
    surface = "PROMPT_TEXT"

    print(f"Loaded ops: {loaded}, filtered ops: {len(registry.filter(bucket_id=bucket_id, surface=surface))}")

    mutator = Mutator(registry)
    outs = mutator.generate_children(
        seed_text=seed_text,
        bucket_id=bucket_id,
        surface=surface,
        n=5,
        k=2,
        seed_base=1337,
        strength=3,
        constraints={"max_chars": 4000},
        metadata={"seed_id": "demo_seed"},
    )
    mutator.pretty_print(outs)


if __name__ == "__main__":
    main()
