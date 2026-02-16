from __future__ import annotations

from src.core.operator_stats import OperatorStatsByBucket


def test_report_result_minimal_updates_counts():
    stats = OperatorStatsByBucket()

    stats.report_result("LLM01_PROMPT_INJECTION", "op_x", "PASS", 0.9)
    st = stats.get("LLM01_PROMPT_INJECTION", "op_x")
    assert st is not None
    assert st.n == 1
    assert st.n_pass == 1
    assert st.n_fail == 0
    assert st.n_unknown == 0
    assert st.n_score == 1
    assert abs(st.avg_oracle_score - 0.9) < 1e-9

    stats.report_result("LLM01_PROMPT_INJECTION", "op_x", "FAIL", 0.1)
    st = stats.get("LLM01_PROMPT_INJECTION", "op_x")
    assert st is not None
    assert st.n == 2
    assert st.n_pass == 1
    assert st.n_fail == 1
    assert st.n_score == 2
    assert 0.0 <= st.avg_oracle_score <= 1.0


def test_report_result_is_robust_to_bad_inputs():
    stats = OperatorStatsByBucket()

    # verdict weird + score non-float: should not raise
    stats.report_result("B", "op_y", verdict={"x": 1}, oracle_score="not-a-number")
    st = stats.get("B", "op_y")
    assert st is not None
    assert st.n == 1
    assert st.n_unknown == 1
    assert st.n_score == 0  # score ignored


def test_snapshot_shape():
    stats = OperatorStatsByBucket()
    stats.report_result("B", "op_a", "OK", 1)
    snap = stats.snapshot()
    assert "B" in snap
    assert "op_a" in snap["B"]
    row = snap["B"]["op_a"]
    for k in ("n", "n_pass", "n_fail", "n_unknown", "pass_rate", "n_score", "avg_oracle_score", "last_updated_ts"):
        assert k in row
