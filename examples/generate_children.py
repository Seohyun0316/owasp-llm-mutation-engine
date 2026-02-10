# examples/generate_children.py
import random

from src.core.registry import OperatorRegistry
from src.core.selector import UniformRandomSelector
from src.core.mutator import Mutator

def main():
    rng = random.Random(42)

    reg = OperatorRegistry()
    reg.load_from_package("src.operators")

    selector = UniformRandomSelector(registry=reg)
    mutator = Mutator(selector=selector)

    seed = "You are a helpful assistant. Explain secure coding practices."
    bucket_id = "LLM01_PROMPT_INJECTION"
    surface = "PROMPT_TEXT"

    children = mutator.generate_children(
        seed_text=seed,
        bucket_id=bucket_id,
        surface=surface,
        rng=rng,
        n=5,
        k=3,
        strength=3,
        constraints={"max_chars": 500},
        metadata={"seed_id": "demo_seed"},
    )

    for idx, r in enumerate(children):
        print("==== child", idx, "====")
        print("trace:", [t.get("op_id") for t in r.mutation_trace])
        print(r.child_text)

if __name__ == "__main__":
    main()
