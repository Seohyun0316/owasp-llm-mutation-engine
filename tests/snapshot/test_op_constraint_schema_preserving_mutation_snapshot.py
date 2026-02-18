import random
import json
from src.operators.op_constraint_schema_preserving_mutation import apply

SEED_OBJ = {"a": 1, "b": "text", "c": 3}
SEED = json.dumps(SEED_OBJ)

EXPECTED = {
    1: '{"a": 2, "b": "text", "c": 3}',
    2: '{"a": 3, "b": "text (modified)", "c": 3}',
    3: '{"a": 4, "b": "text (modified)", "c": 6}',
    4: '{"a": 5, "b": "text (modified)", "c": 7}',
    5: '{"a": 6, "b": "text (modified)", "c": 8}',
}


def test_schema_preserving_all_strengths():
    for s in range(1, 6):
        r = apply(SEED, {"strength": s}, random.Random(1234))
        assert r.status == "OK"
        assert r.child_text == EXPECTED[s]
