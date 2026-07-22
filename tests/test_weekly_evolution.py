import pandas as pd

from src.filters import filter_by_period
from src.views.weekly_evolution import available_weekly_metrics, prepare_weekly_series


def weekly_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "inicio": pd.to_datetime(["2024-06-01", "2024-05-09", "2024-05-01"]),
            "fim": pd.to_datetime(["2024-06-08", "2024-05-16", "2024-05-08"]),
            "semana": ["1 a 8", "9 a 16", "1 a 8"],
            "categoria_resultado": ["Cliques", "Cliques", "Cadastro"],
            "investimento": [300.0, 200.0, 100.0], "resultados": [30.0, 20.0, 10.0],
            "alcance": [pd.NA, pd.NA, pd.NA], "impressoes": [3000.0, 2000.0, 1000.0],
        }
    )


def test_weekly_evolution_is_sorted_by_dates() -> None:
    weekly = prepare_weekly_series(weekly_frame(), "investimento")
    assert weekly["inicio"].tolist() == sorted(weekly["inicio"].tolist())


def test_single_month_does_not_show_other_months() -> None:
    filtered = filter_by_period(weekly_frame(), pd.Timestamp("2024-05-01"), pd.Timestamp("2024-05-31"))
    weekly = prepare_weekly_series(filtered, "investimento")
    assert set(weekly["inicio"].dt.month) == {5}


def test_cross_month_range_shows_all_intersecting_weeks() -> None:
    filtered = filter_by_period(weekly_frame(), pd.Timestamp("2024-05-09"), pd.Timestamp("2024-06-05"))
    weekly = prepare_weekly_series(filtered, "investimento")
    assert weekly["semana"].tolist() == ["9 a 16", "1 a 8"]
    assert weekly["semana_id"].nunique() == 2


def test_null_metric_is_not_offered() -> None:
    assert "Alcance" not in available_weekly_metrics(weekly_frame())
    assert available_weekly_metrics(weekly_frame())[0] == "Investimento"

