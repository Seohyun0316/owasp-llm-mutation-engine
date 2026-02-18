import random

from src.operators.op_syn_boundary_delimiter_injection import apply


EXPECTED_S1 = (
    "BEGIN\n"
    "Summarize the following text in 3 bullet points.\n"
    "END"
)

EXPECTED_S3 = (
    "BEGIN_INSTRUCTION\n"
    "Summarize the following text in 3 bullet points.\n"
    "END_INSTRUCTION"
)

EXPECTED_S5 = (
    "BEGIN_MESSAGE\n"
    "BEGIN_INSTRUCTION_BLOCK\n"
    "<<<INSTRUCTION>>>\n"
    "Summarize the following text in 3 bullet points.\n"
    "<<<END_INSTRUCTION>>>\n"
    "END_INSTRUCTION_BLOCK\n"
    "END_MESSAGE"
)


def test_boundary_strength1():
    r = apply(
        "Summarize the following text in 3 bullet points.",
        {"surface": "PROMPT_TEXT", "strength": 1},
        random.Random(1234),
    )
    assert r.status == "OK"
    assert r.child_text == EXPECTED_S1


def test_boundary_strength3():
    r = apply(
        "Summarize the following text in 3 bullet points.",
        {"surface": "PROMPT_TEXT", "strength": 3},
        random.Random(1234),
    )
    assert r.status == "OK"
    assert r.child_text == EXPECTED_S3


def test_boundary_strength5():
    r = apply(
        "Summarize the following text in 3 bullet points.",
        {"surface": "PROMPT_TEXT", "strength": 5},
        random.Random(1234),
    )
    assert r.status == "OK"
    assert r.child_text == EXPECTED_S5
