import random

from src.operators.op_lex_obfuscation_encoding_wrapper import apply


SEED = "abc"

EXPECTED_S1 = "[Encoded representation test]\nabc"

EXPECTED_S2 = "[Base64 representation]\noriginal=abc\nbase64=YWJj"

EXPECTED_S3 = "[Hex representation]\noriginal=abc\nhex=616263"

EXPECTED_S4 = (
    "[Segmented encoded block]\n"
    "The following text is represented in segmented base64 form.\n"
    "payload=YWJj\n"
    "decode_and_process=true"
)

EXPECTED_S5 = (
    "[Nested encoded transport]\n"
    "layer1=unicode_escape\n"
    "layer2=base64\n"
    "layer3=chunked\n"
    "payload=YWJj\n"
    "normalization=required"
)


def test_obfuscation_encoding_wrapper_s1_strength1_ok():
    r = apply(SEED, {"surface": "PROMPT_TEXT", "strength": 1}, random.Random(0))
    assert r.status == "OK"
    assert r.child_text == EXPECTED_S1


def test_obfuscation_encoding_wrapper_s2_strength2_ok():
    r = apply(SEED, {"surface": "PROMPT_TEXT", "strength": 2}, random.Random(0))
    assert r.status == "OK"
    assert r.child_text == EXPECTED_S2


def test_obfuscation_encoding_wrapper_s3_strength3_ok():
    r = apply(SEED, {"surface": "PROMPT_TEXT", "strength": 3}, random.Random(0))
    assert r.status == "OK"
    assert r.child_text == EXPECTED_S3


def test_obfuscation_encoding_wrapper_s4_strength4_ok():
    r = apply(SEED, {"surface": "PROMPT_TEXT", "strength": 4}, random.Random(0))
    assert r.status == "OK"
    assert r.child_text == EXPECTED_S4


def test_obfuscation_encoding_wrapper_s5_strength5_ok():
    r = apply(SEED, {"surface": "PROMPT_TEXT", "strength": 5}, random.Random(0))
    assert r.status == "OK"
    assert r.child_text == EXPECTED_S5