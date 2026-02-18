import random
from src.operators.op_fmt_structured_wrapper_json_yaml import apply

SEED = "Explain quantum computing briefly."

EXPECTED = {
    1: '{"prompt": "Explain quantum computing briefly."}',
    2: '{"goal": "answer_user", "input": "Explain quantum computing briefly.", "format": "plain_text"}',
    3: """{
  "goal": "answer_user",
  "input": "Explain quantum computing briefly.",
  "format": "plain_text"
}""",
    4: """{
  "meta": {
    "version": "v1"
  },
  "task": {
    "goal": "answer_user",
    "input": "Explain quantum computing briefly."
  },
  "output": {
    "format": "plain_text",
    "hint": "structured"
  }
}""",
    5: """{
  "meta": {
    "version": "v1"
  },
  "task": {
    "goal": "answer_user",
    "input": "Explain quantum computing briefly."
  },
  "output": {
    "format": "plain_text",
    "hint": "structured"
  }
}""",
}


def test_structured_wrapper_all_strengths():
    for s in range(1, 6):
        r = apply(SEED, {"surface": "PROMPT_TEXT", "strength": s}, random.Random(1234))
        assert r.status == "OK"
        assert r.child_text == EXPECTED[s]
