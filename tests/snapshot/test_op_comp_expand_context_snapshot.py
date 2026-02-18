import random
from src.operators.op_comp_expand_context import apply

SEED = "Explain quantum computing briefly."

PARA = (
    "This topic has been widely discussed in academic literature. "
    "Researchers have explored theoretical foundations, practical applications, "
    "and interdisciplinary implications."
)

EXPECTED = {
    1: f"{SEED}\n\n{PARA}",
    2: f"{SEED}\n\n{PARA}\n\n{PARA}",
    3: f"{SEED}\n\n{PARA}\n\n{PARA}",
    4: f"{SEED}\n\n{PARA}\n\n{PARA}\n\n{PARA}\n\n{PARA}",
    5: f"{SEED}\n\n{PARA}\n\n{PARA}\n\n{PARA}\n\n{PARA}",
}


def test_expand_context_all_strengths():
    for s in range(1, 6):
        r = apply(SEED, {"surface": "PROMPT_TEXT", "strength": s}, random.Random(1234))
        assert r.status == "OK"
        assert r.child_text == EXPECTED[s]
