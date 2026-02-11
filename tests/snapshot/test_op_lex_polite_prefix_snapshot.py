import random

from src.operators.op_lex_polite_prefix import apply


def test_polite_prefix_p1_strength2_seed0():
    r = apply("hello", {"surface": "PROMPT_TEXT", "strength": 2}, random.Random(0))
    assert r.status == "OK"
    assert r.child_text == "Absolutely. Here is the response:\nhello"


def test_polite_prefix_p2_strength2_seed1():
    r = apply("hello", {"surface": "PROMPT_TEXT", "strength": 2}, random.Random(1))
    assert r.status == "OK"
    assert r.child_text == "Sure — here is the answer you requested:\nhello"


def test_polite_prefix_p3_surface_mismatch_skipped():
    r = apply("hello", {"surface": "SYSTEM_MESSAGE", "strength": 2}, random.Random(0))
    assert r.status == "SKIPPED"
    assert r.child_text == "hello"


def test_polite_prefix_p4_max_chars_skipped():
    r = apply(
        "hello",
        {"surface": "PROMPT_TEXT", "strength": 2, "constraints": {"max_chars": 10}},
        random.Random(0),
    )
    assert r.status == "SKIPPED"
    assert r.child_text == "hello"
