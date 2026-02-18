import random
from src.operators.op_fmt_punctuation_resegmentation import apply

SEED = "Explain quantum computing briefly. It uses qubits. It is powerful."

EXPECTED = {
    1: "Explain quantum computing briefly; It uses qubits; It is powerful;",
    2: "Explain quantum computing briefly; It uses qubits; It is powerful;",
    3: "- Explain quantum computing briefly\n- It uses qubits\n- It is powerful",
    4: "- Explain quantum computing briefly\n- It uses qubits\n- It is powerful",
    5: "### Reformatted\n\n- Explain quantum computing briefly\n- It uses qubits\n- It is powerful",
}


def test_punctuation_all_strengths():
    for s in range(1, 6):
        r = apply(SEED, {"surface": "PROMPT_TEXT", "strength": s}, random.Random(1234))
        assert r.status == "OK"
        assert r.child_text == EXPECTED[s]
