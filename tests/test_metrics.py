import math

import pandas as pd
import pytest

from src.metrics import calculate_category_metrics, calculate_metrics, metric_is_available, results_by_category


def metric_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "investimento": [100.0, 300.0], "resultados": [10.0, 30.0],
            "cliques": [20.0, 100.0], "alcance": [100.0, 300.0],
            "impressoes": [200.0, 800.0], "categoria_resultado": ["Cliques", "Cadastro"],
        }
    )


def test_weighted_cpc() -> None:
    assert calculate_metrics(metric_frame()).cpc == pytest.approx(400 / 120)


def test_weighted_cost_per_result() -> None:
    assert calculate_metrics(metric_frame()).custo_resultado == pytest.approx(10)


def test_reach_cost_uses_thousand_multiplier() -> None:
    assert calculate_metrics(metric_frame()).custo_mil_alcancados == pytest.approx(1000)


def test_reach_cost_is_missing_when_reach_is_zero() -> None:
    data = metric_frame()
    data["alcance"] = 0
    assert math.isnan(calculate_metrics(data).custo_mil_alcancados)


def test_click_category_uses_click_column() -> None:
    data = metric_frame().iloc[[0]].copy()
    data["resultados"] = 999
    metrics = calculate_category_metrics(data, "Cliques")
    assert metrics.resultados == 20
    assert metrics.custo_resultado == pytest.approx(5)


def test_derived_metrics() -> None:
    metrics = calculate_metrics(metric_frame())
    assert metrics.ctr == pytest.approx(12)
    assert metrics.cpm == pytest.approx(400)
    assert metrics.frequencia == pytest.approx(2.5)


def test_result_categories_are_not_combined() -> None:
    summary = results_by_category(metric_frame())
    assert len(summary) == 2
    assert set(summary["categoria_resultado"]) == {"Cliques", "Cadastro"}


def test_empty_metrics_do_not_raise() -> None:
    empty = metric_frame().iloc[0:0]
    metrics = calculate_metrics(empty)
    assert metrics.investimento == 0
    assert math.isnan(metrics.cpc)


def test_completely_null_metric_is_unavailable() -> None:
    data = metric_frame()
    data["alcance"] = float("nan")
    assert not metric_is_available(data, "alcance")


def test_valid_zero_metric_is_available() -> None:
    data = metric_frame()
    data["alcance"] = 0.0
    assert metric_is_available(data, "alcance")
