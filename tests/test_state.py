from src.state import (
    clear_advanced_filters,
    initialize_filter_state,
    option_widget_key,
    persist_filter_state,
    sync_multi_group,
    sync_single_group,
)


def test_multi_group_specific_unchecks_all_and_accepts_multiple() -> None:
    options = ("Hyundai HMB", "Yamaha")
    all_key = "filter_brands_all"
    first = option_widget_key("filter_brands", options[0])
    second = option_widget_key("filter_brands", options[1])
    state = {all_key: True, first: True, second: True}
    sync_multi_group(state, "filter_brands", all_key, options, second)
    assert state[all_key] is False
    assert state["filter_brands"] == ["Hyundai HMB", "Yamaha"]


def test_multi_group_all_clears_only_its_specific_options() -> None:
    options = ("Meta Ads", "Google Ads")
    all_key = "filter_platforms_all"
    keys = [option_widget_key("filter_platforms", option) for option in options]
    state = {all_key: True, keys[0]: True, keys[1]: True, "filter_brands": ["Yamaha"]}
    sync_multi_group(state, "filter_platforms", all_key, options, all_key)
    assert state["filter_platforms"] == []
    assert not any(state[key] for key in keys)
    assert state["filter_brands"] == ["Yamaha"]


def test_multi_group_falls_back_to_all_when_last_specific_is_unchecked() -> None:
    option = "Evento"
    key = option_widget_key("filter_actions", option)
    state = {"filter_actions_all": False, key: False}
    sync_multi_group(state, "filter_actions", "filter_actions_all", (option,), key)
    assert state["filter_actions_all"] is True
    assert state["filter_actions"] == []


def test_single_group_always_keeps_exactly_one_selection() -> None:
    options = ("Engajamento", "Cadastro")
    cadastro_key = option_widget_key("filter_result", "Cadastro")
    engagement_key = option_widget_key("filter_result", "Engajamento")
    state = {"filter_result_all": True, cadastro_key: True, engagement_key: False}
    sync_single_group(state, "filter_result", "filter_result_all", options, cadastro_key)
    assert state["filter_result"] == "Cadastro"
    assert state["filter_result_all"] is False
    state[cadastro_key] = False
    sync_single_group(state, "filter_result", "filter_result_all", options, cadastro_key)
    assert state["filter_result"] == "Todos"
    assert state["filter_result_all"] is True


def test_clear_filters_preserves_period_and_theme() -> None:
    state = {
        "selected_period": ("2024-05-01", "2024-05-08"),
        "theme_mode": "dark",
        "filter_brands": ["Yamaha"],
        "filter_result": "Cadastro",
    }
    clear_advanced_filters(state)
    assert state["filter_brands"] == []
    assert state["filter_result"] == "Todos"
    assert state["selected_period"] == ("2024-05-01", "2024-05-08")
    assert state["theme_mode"] == "dark"


def test_query_params_restore_only_missing_session_values() -> None:
    state = {"filter_result": "Cadastro"}
    params = {
        "filter_result": '"Engajamento"',
        "filter_brands": '["Hyundai HMB", "Yamaha"]',
    }
    initialize_filter_state(state, params)
    assert state["filter_result"] == "Cadastro"
    assert state["filter_brands"] == ["Hyundai HMB", "Yamaha"]


def test_filter_state_is_serialized_without_period_or_theme() -> None:
    state = {
        "filter_brands": ["Yamaha"],
        "filter_platforms": [],
        "filter_segments": ["0 km"],
        "filter_actions": ["Evento"],
        "filter_result": "Cadastro",
        "selected_period": "sensitive-period",
        "theme_mode": "dark",
    }
    params: dict[str, str] = {}
    persist_filter_state(state, params)
    assert params["filter_brands"] == '["Yamaha"]'
    assert "selected_period" not in params and "theme_mode" not in params
