import random
from src.operators.op_fmt_markdown_wrapper import apply

SEED = "Explain quantum computing briefly."

EXPECTED = {
    1: "> Explain quantum computing briefly.",
    2: """```text
Explain quantum computing briefly.
```""",
    3: """```text
Explain quantum computing briefly.
```""",
    4: """# Instruction

## Task
Explain quantum computing briefly.

## Output
Provide a structured answer.""",
    5: """# Instruction

## Task
Explain quantum computing briefly.

## Output
Provide a structured answer.""",
}


def test_markdown_all_strengths():
    for s in range(1, 6):
        r = apply(SEED, {"surface": "PROMPT_TEXT", "strength": s}, random.Random(1234))
        assert r.status == "OK"
        assert r.child_text == EXPECTED[s]
