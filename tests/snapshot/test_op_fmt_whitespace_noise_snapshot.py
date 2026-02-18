import random
from src.operators.op_fmt_whitespace_noise import apply

SEED = "Explain quantum computing briefly."

EXPECTED = {
    1: "Explain quantum computing briefly.",
    2: "Explain quantum computing briefly.",
    3: "Explain  quantum  computing  briefly.\n",
    4: "Explain  quantum  computing  briefly.\n",
    5: "Explain\n\nquantum\n\ncomputing\n\nbriefly.",
}


def test_whitespace_all_strengths():
    for s in range(1, 6):
        r = apply(SEED, {"surface": "PROMPT_TEXT", "strength": s}, random.Random(1234))
        assert r.status == "OK"
        assert r.child_text == EXPECTED[s]
