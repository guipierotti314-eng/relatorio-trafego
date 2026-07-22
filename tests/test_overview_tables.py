import pandas as pd

from src.views.overview import (
    RESULT_HEADERS,
    build_comparison_table_html,
    build_place_table_html,
    ordered_places,
    variation_css_class,
)


def table_frame() -> pd.DataFrame:
    return pd.DataFrame({
        "praca": ["Extra", "FLN", pd.NA],
        "investimento": [100.0, 200.0, 50.0],
        "resultados": [10.0, 20.0, 5.0],
        "cliques": [10.0, 20.0, 5.0],
        "alcance": [1000.0, 2000.0, 500.0],
        "impressoes": [2000.0, 4000.0, 1000.0],
        "categoria_resultado": ["Cadastro"] * 3,
    })


def test_place_order_is_fixed_then_alphabetical() -> None:
    assert ordered_places(["Zulu", "BRQ", "FLN", "Alpha"]) == ["FLN", "BRQ", "Alpha", "Zulu"]


def test_missing_place_does_not_appear_in_place_table() -> None:
    html = build_place_table_html(table_frame(), table_frame(), "Cadastro")
    assert "FLN" in html and "Extra" in html
    assert "Não identificada" not in html and ">nan<" not in html


def test_dynamic_result_headers() -> None:
    assert RESULT_HEADERS["Engajamento"] == ("Mensagens", "Custo/Mensagem")
    assert RESULT_HEADERS["Cadastro"] == ("Cadastros", "Custo/Cadastro")
    assert RESULT_HEADERS["Alcance"][1] == "Custo por mil alcançados"


def test_reach_table_does_not_duplicate_reach_column() -> None:
    current = table_frame()
    current["categoria_resultado"] = "Alcance"
    html = build_comparison_table_html(current, current, "Alcance", "01/05/2024 a 08/05/2024", "01/04/2024 a 08/04/2024")
    assert html.count("<th>Alcance</th>") == 1
    assert "Custo por mil alcançados" in html


def test_zero_previous_value_renders_dash() -> None:
    previous = table_frame()
    previous[["investimento", "resultados", "alcance", "impressoes"]] = 0
    html = build_comparison_table_html(table_frame(), previous, "Cadastro", "Atual", "Anterior")
    assert "<td>-</td>" in html


def test_comparison_table_uses_fixed_row_labels_and_auxiliary_date_ranges() -> None:
    html = build_comparison_table_html(
        table_frame(),
        table_frame(),
        "Cadastro",
        "09/06/2024 a 17/06/2024",
        "09/05/2024 a 17/05/2024",
    )
    assert "<th>Período</th>" in html
    assert "<td>Período atual</td>" in html
    assert "<td>Variação</td>" in html
    assert "<td>Período anterior</td>" in html
    assert "<strong>Período atual:</strong> 09/06/2024 a 17/06/2024" in html
    assert "<strong>Período anterior:</strong> 09/05/2024 a 17/05/2024" in html
    assert "<td>09/06/2024 a 17/06/2024</td>" not in html
    assert "<td>09/05/2024 a 17/05/2024</td>" not in html


def test_cost_variation_colors_are_inverted() -> None:
    assert variation_css_class("investimento", 10) == "variation-positive"
    assert variation_css_class("resultados", 10) == "variation-positive"
    assert variation_css_class("custo_resultado", 10) == "variation-negative"
    assert variation_css_class("custo_resultado", -10) == "variation-positive"
