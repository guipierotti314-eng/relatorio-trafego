import pandas as pd

from src.filters import (
    apply_action_type_filter,
    apply_brand_filter,
    apply_dimension_filters,
    apply_result_type_filter,
    apply_segment_filter,
    default_latest_month_range,
    dimension_options,
    filter_by_period,
)
from src.metrics import calculate_metrics
from src.classifiers import standardize_brand


def period_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "plataforma": ["Meta Ads", "Google Ads", "Meta Ads"],
            "marca": ["Geração Seminovos", "B", pd.NA],
            "praca": ["FLN", "BRQ", pd.NA],
            "segmento_campanha": ["Seminovos", "0 km", "0 km"],
            "tipo_acao": ["Regular", "Evento", "Regular"],
            "categoria_resultado": ["Cliques", "Cadastro", pd.NA],
            "inicio": pd.to_datetime(["2024-05-01", "2024-06-01", "2024-06-25"]),
            "fim": pd.to_datetime(["2024-05-08", "2024-06-08", "2024-07-02"]),
            "investimento": [100.0, 200.0, 300.0],
            "resultados": [10.0, 20.0, 30.0],
            "cliques": [10.0, 20.0, 30.0],
            "alcance": [100.0, 200.0, 300.0],
            "impressoes": [1000.0, 2000.0, 3000.0],
        }
    )


def test_period_filter_uses_interval_intersection() -> None:
    filtered = filter_by_period(period_frame(), pd.Timestamp("2024-06-30"), pd.Timestamp("2024-07-05"))
    assert len(filtered) == 1
    assert filtered.iloc[0]["investimento"] == 300


def test_latest_month_is_default_and_limited_to_latest_date() -> None:
    selected = default_latest_month_range(period_frame())
    assert selected is not None
    assert selected.start == pd.Timestamp("2024-07-01")
    assert selected.end == pd.Timestamp("2024-07-02")


def test_unidentified_place_is_not_filter_option() -> None:
    assert dimension_options(period_frame(), "praca") == ["BRQ", "FLN"]


def test_unidentified_place_remains_in_general_total() -> None:
    assert calculate_metrics(period_frame()).investimento == 600


def test_missing_brand_is_not_filter_option_but_remains_in_total() -> None:
    data = period_frame()
    assert dimension_options(data, "marca") == ["B", "Geração Seminovos"]
    assert calculate_metrics(data).investimento == 600


def test_geracao_seminovos_is_valid_brand() -> None:
    assert "Geração Seminovos" in dimension_options(period_frame(), "marca")


def test_selecting_brand_excludes_missing_brand() -> None:
    filtered = apply_dimension_filters(period_frame(), brands=("B",))
    assert len(filtered) == 1
    assert filtered.iloc[0]["marca"] == "B"


def test_multiple_values_are_inclusive_inside_each_group() -> None:
    filtered = apply_dimension_filters(
        period_frame(),
        platforms=("Meta Ads",),
        campaign_segments=("0 km", "Seminovos"),
        action_types=("Regular",),
    )
    assert len(filtered) == 2
    assert set(filtered["segmento_campanha"]) == {"0 km", "Seminovos"}


def test_brand_aliases_are_not_duplicated_in_filter_and_filter_together() -> None:
    raw = ["Hyundai Geração", "Geração Hyundai", "Hyundai HMB", "Geração Hyundai HMB"]
    data = pd.DataFrame({"marca": [standardize_brand(value) for value in raw]})
    assert dimension_options(data, "marca") == ["Hyundai HMB"]
    filtered = apply_brand_filter(data, ("Hyundai HMB",))
    assert len(filtered) == 4


def test_s2_bike_shop_aliases_share_one_filter_option() -> None:
    raw = ["S2 Bike Shop", "S2 Bike Shop Floripa"]
    data = pd.DataFrame({"marca": [standardize_brand(value) for value in raw]})
    assert dimension_options(data, "marca") == ["S2 Bike Shop"]
    assert len(apply_brand_filter(data, ("S2 Bike Shop",))) == 2


def event_registration_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "campanha": ["Evento 0", "Regular 0", "Evento SN", "Evento Clique"],
            "segmento_campanha": ["0 km", "0 km", "Seminovos", "0 km"],
            "tipo_acao": ["Evento", "Regular", "Evento", "Evento"],
            "categoria_resultado": ["Cadastro", "Cadastro", "Cadastro", "Cliques"],
        }
    )


def test_cadastro_filter_does_not_exclude_events() -> None:
    filtered = apply_result_type_filter(event_registration_frame(), "Cadastro")
    assert set(filtered["campanha"]) == {"Evento 0", "Regular 0", "Evento SN"}


def test_zero_km_and_cadastro_include_zero_km_events() -> None:
    filtered = apply_segment_filter(event_registration_frame(), "0 km")
    filtered = apply_result_type_filter(filtered, "Cadastro")
    assert set(filtered["campanha"]) == {"Evento 0", "Regular 0"}


def test_event_and_cadastro_return_only_registration_events() -> None:
    filtered = apply_action_type_filter(event_registration_frame(), "Evento")
    filtered = apply_result_type_filter(filtered, "Cadastro")
    assert set(filtered["campanha"]) == {"Evento 0", "Evento SN"}


def test_regular_and_cadastro_exclude_events() -> None:
    filtered = apply_action_type_filter(event_registration_frame(), "Regular")
    filtered = apply_result_type_filter(filtered, "Cadastro")
    assert filtered["campanha"].tolist() == ["Regular 0"]


def test_result_filter_does_not_mutate_or_apply_segment() -> None:
    original = event_registration_frame()
    filtered = apply_result_type_filter(original, "Cadastro")
    assert set(filtered["segmento_campanha"]) == {"0 km", "Seminovos"}
    assert len(original) == 4
