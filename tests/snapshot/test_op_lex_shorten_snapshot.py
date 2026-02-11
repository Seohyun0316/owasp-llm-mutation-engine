import random

from src.operators.op_lex_shorten import apply


SEED_TEXT = "\n".join(
    ["Line A", "Line B", "Line C", "Line D", "Line E", "Line F", "Line G", "Line H"]
)


def test_shorten_s1_strength1_seed0():
    r = apply(SEED_TEXT, {"surface": "PROMPT_TEXT", "strength": 1}, random.Random(0))
    assert r.status == "OK"
    assert r.child_text == "\n".join(
        ["Line A", "Line B", "Line C", "Line D", "Line E", "Line F", "Line H"]
    )


def test_shorten_s2_strength3_seed42():
    r = apply(SEED_TEXT, {"surface": "PROMPT_TEXT", "strength": 3}, random.Random(42))
    assert r.status == "OK"
    assert r.child_text == "\n".join(["Line C", "Line D", "Line E", "Line G", "Line H"])


def test_shorten_s3_strength5_seed1():
    r = apply(SEED_TEXT, {"surface": "PROMPT_TEXT", "strength": 5}, random.Random(1))
    assert r.status == "OK"
    assert r.child_text == "\n".join(["Line D", "Line G"])


def test_shorten_s4_surface_mismatch_skipped():
    r = apply(SEED_TEXT, {"surface": "SYSTEM_MESSAGE", "strength": 4}, random.Random(0))
    assert r.status == "SKIPPED"
    assert r.child_text == SEED_TEXT
