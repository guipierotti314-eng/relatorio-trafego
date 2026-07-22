import pandas as pd

from src.formatters import format_currency_br, format_percentage_br
from src.views.overview import build_budget_donut


def test_brazilian_formatters() -> None:
    assert format_currency_br(1234.56) == "R$ 1.234,56"
    assert format_percentage_br(0.324) == "32,4%"


def test_donut_tooltip_has_no_technical_column_name() -> None:
    data = pd.DataFrame({"segmento_campanha": ["Seminovos", "0 km"], "investimento": [1234.56, 100.0]})
    trace = build_budget_donut(data, "light").data[0]
    assert "segmento_campanha=" not in trace.hovertemplate
    assert trace.hovertemplate == "%{customdata[0]} | %{customdata[1]} | %{customdata[2]}<extra></extra>"


def test_donut_customdata_uses_br_currency_and_percentage() -> None:
    data = pd.DataFrame({"segmento_campanha": ["Seminovos", "0 km"], "investimento": [1234.56, 100.0]})
    customdata = build_budget_donut(data, "dark").data[0].customdata
    assert customdata[0][1] == "R$ 100,00" or customdata[0][1] == "R$ 1.234,56"
    assert str(customdata[0][2]).endswith("%")
