from src.core.validity_guard import GuardConfig, guard_text, is_text_valid


def test_guard_removes_control_chars_and_truncates():
    cfg = GuardConfig(max_len=5, schema_mode=False)

    s = "A\x00B\x01CDEFG"  # 제어문자 포함 + 길이 초과
    out = guard_text(s, cfg)

    # 제어문자 제거 후 "ABCDEFG"가 되고, max_len=5로 "ABCDE"
    assert out == "ABCDE"
    assert is_text_valid(out, cfg)


def test_guard_schema_mode_placeholder():
    cfg = GuardConfig(max_len=100, schema_mode=True, placeholder="N/A")

    out = guard_text("", cfg)
    assert out == "N/A"
    assert is_text_valid(out, cfg)


def test_guard_rejects_non_str():
    cfg = GuardConfig(max_len=10, schema_mode=False)

    try:
        guard_text(None, cfg)  # type: ignore[arg-type]
        assert False, "guard_text must raise TypeError for non-str"
    except TypeError:
        pass
