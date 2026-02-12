from src.core.registry import OperatorRegistry


def test_registry_loads_ops_strict_no_load_errors():
    reg = OperatorRegistry()
    count = reg.load_from_package("src.operators", strict=True)

    assert count > 0, "no operators loaded"
    assert reg.load_errors == [], f"load_errors must be empty in strict mode: {reg.load_errors}"


def test_registry_list_ops_is_sorted_by_op_id():
    reg = OperatorRegistry()
    reg.load_from_package("src.operators", strict=True)

    op_ids = [h.op_id for h in reg.list_ops()]
    assert op_ids == sorted(op_ids)
