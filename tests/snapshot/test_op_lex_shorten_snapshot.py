import random

from src.operators.op_lex_shorten import apply


SEED = "Line A\nLine B\nLine C\nLine D\nLine E\nLine F\nLine G\nLine H"

EXPECTED_S1 = "Line A\nLine B\nLine C\nLine D\nLine E\nLine F\nLine H"
EXPECTED_S2 = "Line A\nLine B\nLine C\nLine E\nLine F"
EXPECTED_S3 = "Line B\nLine E"


def test_shorten_s1_strength1_seed0_ok():
    r = apply(SEED, {"surface": "PROMPT_TEXT", "strength": 1}, random.Random(0))
    assert r.status == "OK"
    assert r.child_text == EXPECTED_S1


def test_shorten_s2_strength3_seed0_ok():
    r = apply(SEED, {"surface": "PROMPT_TEXT", "strength": 3}, random.Random(0))
    assert r.status == "OK"
    assert r.child_text == EXPECTED_S2


def test_shorten_s3_strength5_seed0_ok():
    r = apply(SEED, {"surface": "PROMPT_TEXT", "strength": 5}, random.Random(0))
    assert r.status == "OK"
    assert r.child_text == EXPECTED_S3


def test_shorten_s4_surface_mismatch_skipped():
    r = apply(SEED, {"surface": "SYSTEM_MESSAGE", "strength": 3}, random.Random(0))
    assert r.status == "SKIPPED"
    assert r.child_text == SEED


def test_shorten_s5_max_chars_skipped():
    r = apply(
        SEED,
        {"surface": "PROMPT_TEXT", "strength": 3, "constraints": {"max_chars": 10}},
        random.Random(0),
    )
    assert r.status == "SKIPPED"
    assert r.child_text == SEED
