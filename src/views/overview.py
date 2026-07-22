"""Visão geral única, organizada por marca, plataforma, resultado e praça."""

from __future__ import annotations

from html import escape
import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.comparisons import percentage_change
from src.config import METRIC_BEHAVIOR, PLACE_ORDER, RESULT_CATEGORY_OPTIONS
from src.filters import dimension_options
from src.formatters import (
    format_currency_br,
    format_date_range_br,
    format_integer_br,
    format_percentage_points_br,
)
from src.metrics import calculate_category_metrics, metric_is_available
from src.views.common import apply_chart_theme, plotly_config, render_metric_cards, theme_colors


NO_DATA_MESSAGE = "Não há dados disponíveis nesse período"

RESULT_HEADERS: dict[str, tuple[str, str]] = {
    "Engajamento": ("Mensagens", "Custo/Mensagem"),
    "Cliques": ("Cliques", "Custo/Clique"),
    "Cadastro": ("Cadastros", "Custo/Cadastro"),
    "Alcance": ("Alcance", "Custo por mil alcançados"),
}


def build_budget_donut(data: pd.DataFrame, theme: str = "light") -> go.Figure:
    valid = data.dropna(subset=["segmento_campanha", "investimento"])
    summary = valid.groupby("segmento_campanha", as_index=False)["investimento"].sum()
    total = summary["investimento"].sum()
    summary["percentual"] = summary["investimento"] / total if total else 0.0
    customdata = [
        [row.segmento_campanha, format_currency_br(row.investimento), f"{row.percentual * 100:.1f}%".replace(".", ",")]
        for row in summary.itertuples(index=False)
    ]
    colors = theme_colors(theme)
    figure = go.Figure(go.Pie(
        labels=summary["segmento_campanha"], values=summary["investimento"], hole=.58,
        customdata=customdata,
        hovertemplate="%{customdata[0]} | %{customdata[1]} | %{customdata[2]}<extra></extra>",
        texttemplate="<b>%{label}</b><br>%{customdata[1]}<br>%{customdata[2]}",
        textposition="auto", textfont={"size": 13}, sort=False,
        marker={"colors": [colors["primary"], "#34373c", "#8d939b", "#ff9a58"],
                "line": {"color": colors["surface"], "width": 3}},
    ))
    figure.update_layout(title="Distribuição do orçamento", height=480, showlegend=True)
    return apply_chart_theme(figure, theme)


def ordered_places(values: list[str] | tuple[str, ...]) -> list[str]:
    configured = [place for place in PLACE_ORDER if place in values]
    extras = sorted((place for place in values if place not in PLACE_ORDER), key=str.casefold)
    return [*configured, *extras]


def variation_css_class(metric: str, variation: float | None) -> str:
    if variation is None or variation == 0:
        return "variation-neutral"
    lower_is_positive = METRIC_BEHAVIOR.get(metric) == "lower_is_positive"
    positive = variation < 0 if lower_is_positive else variation > 0
    return "variation-positive" if positive else "variation-negative"


def _finite(value: float) -> bool:
    return value is not None and math.isfinite(float(value))


def _formatted(value: float, metric: str) -> str:
    if not _finite(value):
        return "-"
    if metric in {"investimento", "custo_resultado", "custo_mil_alcancados"}:
        return format_currency_br(value)
    return format_integer_br(value)


def _metric_definitions(data: pd.DataFrame, category: str, include_impressions: bool = False) -> list[tuple[str, str]]:
    result_label, cost_label = RESULT_HEADERS[category]
    definitions: list[tuple[str, str]] = [("Investimento", "investimento")]
    if category == "Alcance":
        if metric_is_available(data, "alcance"):
            definitions.extend([("Alcance", "alcance"), (cost_label, "custo_mil_alcancados")])
    else:
        definitions.extend([(result_label, "resultados"), (cost_label, "custo_resultado")])
        if metric_is_available(data, "alcance"):
            definitions.append(("Alcance", "alcance"))
    if include_impressions and metric_is_available(data, "impressoes"):
        definitions.append(("Impressões", "impressoes"))
    return definitions


def build_comparison_table_html(
    current: pd.DataFrame,
    previous: pd.DataFrame,
    category: str,
    current_label: str,
    previous_label: str,
) -> str:
    current_metrics = calculate_category_metrics(current, category)
    previous_metrics = calculate_category_metrics(previous, category)
    definitions = _metric_definitions(current, category)
    headers = "".join(f"<th>{escape(label)}</th>" for label, _ in definitions)
    current_cells = "".join(
        f"<td>{escape(_formatted(getattr(current_metrics, metric), metric))}</td>"
        for _, metric in definitions
    )
    previous_cells_parts: list[str] = []
    for _, metric in definitions:
        previous_value = getattr(previous_metrics, metric)
        rendered = (
            "-"
            if previous.empty or not _finite(previous_value) or previous_value == 0
            else _formatted(previous_value, metric)
        )
        previous_cells_parts.append(f"<td>{escape(rendered)}</td>")
    previous_cells = "".join(previous_cells_parts)
    variation_cells = []
    for _, metric in definitions:
        change = percentage_change(getattr(current_metrics, metric), getattr(previous_metrics, metric))
        rendered = "-" if change is None else format_percentage_points_br(change)
        variation_cells.append(
            f"<td class='{variation_css_class(metric, change)}'>{escape(rendered)}</td>"
        )
    return (
        "<div class='comparison-period-context'>"
        f"<div><strong>Período atual:</strong> {escape(current_label)}</div>"
        f"<div><strong>Período anterior:</strong> {escape(previous_label)}</div>"
        "</div>"
        "<div class='comparison-table-wrapper'><table class='comparison-table'>"
        f"<thead><tr><th>Período</th>{headers}</tr></thead><tbody>"
        f"<tr><td>Período atual</td>{current_cells}</tr>"
        f"<tr class='variation-row'><td>Variação</td>{''.join(variation_cells)}</tr>"
        f"<tr><td>Período anterior</td>{previous_cells}</tr>"
        "</tbody></table></div>"
    )


def build_place_table_html(current: pd.DataFrame, previous: pd.DataFrame, category: str) -> str:
    places = ordered_places(dimension_options(current, "praca"))
    definitions = _metric_definitions(current, category, include_impressions=True)
    headers = ["Praça"]
    for label, _ in definitions:
        headers.extend([label, f"Δ {label}"])
    rows: list[str] = []
    for place in places:
        current_place = current.loc[current["praca"].eq(place)]
        previous_place = previous.loc[previous["praca"].eq(place)]
        current_metrics = calculate_category_metrics(current_place, category)
        previous_metrics = calculate_category_metrics(previous_place, category)
        cells = [f"<td>{escape(place)}</td>"]
        for _, metric in definitions:
            value = getattr(current_metrics, metric)
            change = percentage_change(value, getattr(previous_metrics, metric))
            rendered_change = "-" if change is None else format_percentage_points_br(change)
            cells.extend([
                f"<td>{escape(_formatted(value, metric))}</td>",
                f"<td class='{variation_css_class(metric, change)}'>{escape(rendered_change)}</td>",
            ])
        rows.append(f"<tr>{''.join(cells)}</tr>")
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    return (
        "<div class='comparison-table-wrapper place-table-wrapper'><table class='comparison-table place-table'>"
        f"<thead><tr>{header_html}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
    )


def _result_categories(data: pd.DataFrame, selected: str) -> list[str]:
    if selected != "Todos":
        return [selected] if data["categoria_resultado"].eq(selected).any() else []
    available = set(data["categoria_resultado"].dropna().astype(str))
    return [category for category in RESULT_CATEGORY_OPTIONS if category in available]


def _render_brand(
    brand: str,
    current: pd.DataFrame,
    previous: pd.DataFrame,
    result_filter: str,
    current_label: str,
    previous_label: str,
) -> None:
    current_brand = current.loc[current["marca"].eq(brand)]
    previous_brand = previous.loc[previous["marca"].eq(brand)]
    if current_brand.empty:
        st.info(NO_DATA_MESSAGE)
        return
    platforms = [
        platform for platform in ("Meta Ads", "Google Ads")
        if current_brand["plataforma"].eq(platform).any()
    ]
    for platform in platforms:
        st.subheader(platform)
        current_platform = current_brand.loc[current_brand["plataforma"].eq(platform)]
        previous_platform = previous_brand.loc[previous_brand["plataforma"].eq(platform)]
        for category in _result_categories(current_platform, result_filter):
            current_result = current_platform.loc[current_platform["categoria_resultado"].eq(category)]
            previous_result = previous_platform.loc[previous_platform["categoria_resultado"].eq(category)]
            if current_result.empty or (category == "Alcance" and not metric_is_available(current_result, "alcance")):
                continue
            st.markdown(f"<div class='section-label'>{escape(category)}</div>", unsafe_allow_html=True)
            st.markdown(
                build_comparison_table_html(
                    current_result, previous_result, category, current_label, previous_label
                ),
                unsafe_allow_html=True,
            )
            places = current_result.dropna(subset=["praca"])
            if not places.empty:
                st.markdown("##### Desempenho por praça")
                st.markdown(
                    build_place_table_html(current_result, previous_result, category),
                    unsafe_allow_html=True,
                )


def render(
    data: pd.DataFrame,
    previous: pd.DataFrame,
    result_filter: str,
    selected_brands: tuple[str, ...],
    current_start: pd.Timestamp,
    current_end: pd.Timestamp,
    previous_start: pd.Timestamp,
    previous_end: pd.Timestamp,
) -> None:
    st.header("Visão geral")
    if data.empty and not selected_brands:
        st.info(NO_DATA_MESSAGE)
        return

    if not data.empty:
        render_metric_cards(data, previous, result_filter)
        budget = data.dropna(subset=["segmento_campanha"])
        if not budget.empty and metric_is_available(budget, "investimento"):
            st.plotly_chart(
                build_budget_donut(budget, str(st.session_state.get("theme_mode", "light"))),
                use_container_width=True,
                config=plotly_config(),
            )

    brands = list(selected_brands) if selected_brands else dimension_options(data, "marca")
    if not brands:
        st.info(NO_DATA_MESSAGE)
        return
    st.subheader("Análise por marca")
    tabs = st.tabs(brands)
    current_label = format_date_range_br(current_start, current_end)
    previous_label = format_date_range_br(previous_start, previous_end)
    for tab, brand in zip(tabs, brands):
        with tab:
            _render_brand(brand, data, previous, result_filter, current_label, previous_label)
