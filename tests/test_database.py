from database import ChoiceType


def test_choice_type_binds_keys_and_display_values():
    choice_type = ChoiceType({"in": "IN", "out": "OUT"})

    assert choice_type.process_bind_param("in", None) == "in"
    assert choice_type.process_bind_param("IN", None) == "in"
    assert choice_type.process_bind_param(None, None) is None


def test_choice_type_returns_display_values():
    choice_type = ChoiceType({"in": "IN", "out": "OUT"})

    assert choice_type.process_result_value("in", None) == "IN"
    assert choice_type.process_result_value("out", None) == "OUT"
    assert choice_type.process_result_value(None, None) is None
