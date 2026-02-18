import random
import json

from src.operators.op_syn_tool_call_argument_perturbation import apply


EXPECTED_S1 = (
    '{"name": "web.search_query", '
    '"arguments": {"q": "hello world", "recency": 30, "limit": 11}}'
)

EXPECTED_S3 = (
    '{"name": "web.search_query", '
    '"arguments": {"q": 15, "recency": 30, "limit": "hello world (full)"}}'
)

EXPECTED_S5 = (
    '{"name": "web.search_query", '
    '"arguments": {"q": "hello world x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x", '
    '"recency": -70, "limit": 110}}'
)


def test_tool_strength1():
    tool = {"name": "web.search_query", "arguments": {"q": "hello world", "recency": 30, "limit": 10}}
    r = apply(
        json.dumps(tool),
        {"surface": "TOOL_CALL", "strength": 1},
        random.Random(1234),
    )
    assert r.status == "OK"
    assert r.child_text == EXPECTED_S1


def test_tool_strength3():
    tool = {"name": "web.search_query", "arguments": {"q": "hello world", "recency": 30, "limit": 10}}
    r = apply(
        json.dumps(tool),
        {"surface": "TOOL_CALL", "strength": 3},
        random.Random(1234),
    )
    assert r.status == "OK"
    assert r.child_text == EXPECTED_S3


def test_tool_strength5():
    tool = {"name": "web.search_query", "arguments": {"q": "hello world", "recency": 30, "limit": 10}}
    r = apply(
        json.dumps(tool),
        {"surface": "TOOL_CALL", "strength": 5},
        random.Random(1234),
    )
    assert r.status == "OK"
    assert r.child_text == EXPECTED_S5
