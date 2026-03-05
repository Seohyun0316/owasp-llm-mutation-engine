import random

from src.operators.op_fmt_punctuation_resegmentation import apply


SEED = "Explain quantum computing briefly."

EXPECTED_P1 = "Explain quantum computing briefly;"
EXPECTED_P2 = "Explain quantum computing briefly;"
EXPECTED_P3 = "- Explain quantum computing briefly"
EXPECTED_P4 = "- Explain quantum computing briefly"
EXPECTED_P5 = "### Reformatted\n\n- Explain quantum computing briefly"


def test_punct_p1_strength1_prompt_text_ok():
    r = apply(SEED, {"surface": "PROMPT_TEXT", "strength": 1}, random.Random(1234))
    assert r.status == "OK"
    assert r.child_text == EXPECTED_P1


def test_punct_p2_strength2_prompt_text_ok():
    r = apply(SEED, {"surface": "PROMPT_TEXT", "strength": 2}, random.Random(1234))
    assert r.status == "OK"
    assert r.child_text == EXPECTED_P2


def test_punct_p3_strength3_prompt_text_ok():
    r = apply(SEED, {"surface": "PROMPT_TEXT", "strength": 3}, random.Random(1234))
    assert r.status == "OK"
    assert r.child_text == EXPECTED_P3


def test_punct_p4_strength4_prompt_text_ok():
    r = apply(SEED, {"surface": "PROMPT_TEXT", "strength": 4}, random.Random(1234))
    assert r.status == "OK"
    assert r.child_text == EXPECTED_P4


def test_punct_p5_strength5_prompt_text_ok():
    r = apply(SEED, {"surface": "PROMPT_TEXT", "strength": 5}, random.Random(1234))
    assert r.status == "OK"
    assert r.child_text == EXPECTED_P5


def test_punct_p6_surface_mismatch_skipped():
    r = apply(SEED, {"surface": "SYSTEM_MESSAGE", "strength": 3}, random.Random(1234))
    assert r.status == "SKIPPED"
    assert r.child_text == SEED


def test_punct_p7_max_chars_skipped():
    r = apply(
        SEED,
        {"surface": "PROMPT_TEXT", "strength": 5, "constraints": {"max_chars": 10}},
        random.Random(1234),
    )
    assert r.status == "SKIPPED"
    assert r.child_text == SEED