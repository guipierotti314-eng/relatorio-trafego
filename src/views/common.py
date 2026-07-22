"""Componentes visuais, temas Plotly e tabelas compartilhadas."""

from __future__ import annotations

from collections.abc import Callable
import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

from src.comparisons import percentage_change
from src.config import THEME_COLORS
from src.exports import to_csv_bytes, to_xlsx_bytes
from src.formatters import (
    format_currency_br,
    format_integer_br,
    format_percentage_points_br,
)
from src.metrics import calculate_category_metrics, calculate_metrics, metric_is_available, results_by_category


FRIENDLY_COLUMNS = {
    "plataforma": "Plataforma", "marca_original": "Marca original", "marca": "Marca", "campanha": "Campanha",
    "categoria_resultado": "Tipo de resultado", "segmento_campanha": "Segmento da campanha",
    "tipo_acao": "Tipo de ação",
    "praca": "Praça", "resultados": "Resultados", "cliques": "Cliques",
    "alcance": "Alcance somado", "impressoes": "Impressões", "investimento": "Investimento",
    "custo_resultado": "Custo por resultado", "cpc": "CPC", "ctr": "CTR", "cpm": "CPM",
    "frequencia": "Frequência", "participacao_investimento": "Participação do investimento",
    "variacao_investimento": "Variação do investimento", "inicio": "Início", "fim": "Fim",
    "semana": "Semana", "periodo": "Período",
}


def current_theme() -> str:
    return str(st.session_state.get("theme_mode", "light"))


def theme_colors(theme: str | None = None) -> dict[str, str]:
    return THEME_COLORS[theme or current_theme()]


def plotly_config() -> dict[str, object]:
    return {"displayModeBar": False, "responsive": True}


def apply_chart_theme(figure: go.Figure, theme: str | None = None) -> go.Figure:
    """Aplica cores explícitas a fundo, eixos, legenda e tooltips."""
    colors = theme_colors(theme)
    figure.update_layout(
        paper_bgcolor=colors["surface"], plot_bgcolor=colors["surface"],
        font={"color": colors["text_primary"], "family": "Inter, Arial, sans-serif"},
        title_font={"color": colors["text_primary"], "size": 18},
        legend={"font": {"color": colors["text_primary"]}, "bgcolor": "rgba(0,0,0,0)"},
        hoverlabel={"bgcolor": colors["surface_secondary"], "font_color": colors["text_primary"], "bordercolor": colors["border"]},
        margin={"l": 30, "r": 30, "t": 65, "b": 35},
    )
    figure.update_xaxes(
        color=colors["text_secondary"], gridcolor=colors["grid"],
        linecolor=colors["border"], zerolinecolor=colors["border"],
    )
    figure.update_yaxes(
        color=colors["text_secondary"], gridcolor=colors["grid"],
        linecolor=colors["border"], zerolinecolor=colors["border"],
    )
    return figure


def _metric_delta(current: float, previous: float) -> tuple[str | None, str]:
    variation = percentage_change(current, previous)
    if variation is None:
        return "Sem comparação", "off"
    return format_percentage_points_br(variation), "normal"


def _render_card(container, label: str, current: float, previous: float, formatter: Callable[[float], str]) -> None:
    delta, color = _metric_delta(current, previous)
    container.metric(label, formatter(current), delta=delta, delta_color=color)


def render_metric_cards(data: pd.DataFrame, previous: pd.DataFrame, result_filter: str) -> None:
    """Renderiza apenas indicadores disponíveis e mantém resultados incompatíveis separados."""
    if result_filter == "Todos":
        current_metrics, previous_metrics = calculate_metrics(data), calculate_metrics(previous)
    else:
        current_metrics = calculate_category_metrics(data, result_filter)
        previous_metrics = calculate_category_metrics(previous, result_filter)
    items: list[tuple[str, float, float, Callable[[float], str]]] = []
    if metric_is_available(data, "investimento"):
        items.append(("Investimento", current_metrics.investimento, previous_metrics.investimento, format_currency_br))
    if result_filter != "Todos":
        result_labels = {
            "Engajamento": ("Mensagens", "Custo/Mensagem"),
            "Cliques": ("Cliques", "Custo/Clique"),
            "Cadastro": ("Cadastros", "Custo/Cadastro"),
        }
        if result_filter in result_labels and metric_is_available(data, "resultados"):
            result_label, cost_label = result_labels[result_filter]
            items.append((result_label, current_metrics.resultados, previous_metrics.resultados, format_integer_br))
            if math.isfinite(current_metrics.custo_resultado):
                items.append((cost_label, current_metrics.custo_resultado, previous_metrics.custo_resultado, format_currency_br))
        elif result_filter == "Alcance" and math.isfinite(current_metrics.custo_mil_alcancados):
            items.append((
                "Custo por mil alcançados",
                current_metrics.custo_mil_alcancados,
                previous_metrics.custo_mil_alcancados,
                format_currency_br,
            ))
    if metric_is_available(data, "alcance"):
        items.append(("Alcance somado", current_metrics.alcance, previous_metrics.alcance, format_integer_br))
    if metric_is_available(data, "impressoes"):
        items.append(("Impressões", current_metrics.impressoes, previous_metrics.impressoes, format_integer_br))
    for offset in range(0, len(items), 5):
        columns = st.columns(min(5, len(items) - offset))
        for container, item in zip(columns, items[offset:offset + 5]):
            _render_card(container, *item)

    if result_filter == "Todos":
        recognized = data.dropna(subset=["categoria_resultado"])
        if not metric_is_available(recognized, "resultados"):
            return
        current_categories = results_by_category(recognized)
        previous_categories = results_by_category(previous.dropna(subset=["categoria_resultado"]))
        if not current_categories.empty:
            st.markdown("<div class='section-label'>Resultados por tipo</div>", unsafe_allow_html=True)
            previous_lookup = previous_categories.set_index("categoria_resultado")
            columns = st.columns(min(4, len(current_categories)))
            for container, row in zip(columns, current_categories.itertuples(index=False)):
                prior_results = previous_lookup.at[row.categoria_resultado, "resultados"] if row.categoria_resultado in previous_lookup.index else float("nan")
                delta, color = _metric_delta(row.resultados, prior_results)
                container.metric(f"{row.categoria_resultado} · Resultados", format_integer_br(row.resultados), delta, delta_color=color)
                if pd.notna(row.custo_resultado):
                    container.caption(f"Custo por resultado: {format_currency_br(row.custo_resultado)}")


def friendly_column_name(column: str) -> str:
    if column in FRIENDLY_COLUMNS:
        return FRIENDLY_COLUMNS[column]
    for prefix, label in (("resultados_", "Resultados — "), ("custo_resultado_", "Custo por resultado — "), ("variacao_resultados_", "Variação — ")):
        if column.startswith(prefix):
            return label + column.removeprefix(prefix).replace("_", " ").title()
    return column.replace("_", " ").capitalize()


def render_interactive_table(
    data: pd.DataFrame,
    key: str,
    title: str | None = None,
    unavailable_columns: tuple[str, ...] = (),
) -> None:
    """Renderiza tabela sem nomes técnicos, com busca, paginação e downloads."""
    if title:
        st.subheader(title)
    table = data.drop(columns=[column for column in unavailable_columns if column in data], errors="ignore")
    table = table.dropna(axis=1, how="all")
    if table.empty:
        st.info("Sem dados para esta tabela.")
        return
    table = table.rename(columns={column: friendly_column_name(column) for column in table.columns})
    grid = GridOptionsBuilder.from_dataframe(table)
    grid.configure_default_column(sortable=True, filter=True, resizable=True, floatingFilter=True)
    number_formatter = JsCode("function(p){if(p.value==null||Number.isNaN(p.value))return '—';return Number(p.value).toLocaleString('pt-BR',{maximumFractionDigits:2});}")
    currency_formatter = JsCode("function(p){if(p.value==null||Number.isNaN(p.value))return '—';return Number(p.value).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});}")
    percent_formatter = JsCode("function(p){if(p.value==null||Number.isNaN(p.value))return '—';return Number(p.value).toLocaleString('pt-BR',{maximumFractionDigits:1})+'%';}")
    for column in table.columns:
        lowered = column.casefold()
        if "investimento" in lowered or "custo" in lowered or lowered in {"cpc", "cpm"}:
            grid.configure_column(column, valueFormatter=currency_formatter)
        elif "participação" in lowered or "variação" in lowered or lowered == "ctr":
            grid.configure_column(column, valueFormatter=percent_formatter)
        elif pd.api.types.is_numeric_dtype(table[column]):
            grid.configure_column(column, valueFormatter=number_formatter)
    grid.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=15)
    grid.configure_grid_options(quickFilterText=st.text_input("Buscar", key=f"search_{key}", placeholder="Digite para filtrar a tabela"))
    colors = theme_colors()
    custom_css = {
        ".ag-root-wrapper": {"background-color": colors["surface"], "border-color": colors["border"]},
        ".ag-header": {"background-color": colors["surface_secondary"], "color": colors["text_primary"]},
        ".ag-row": {"background-color": colors["surface"], "color": colors["text_primary"], "border-color": colors["border"]},
        ".ag-row-hover": {"background-color": colors["surface_secondary"] + " !important"},
    }
    AgGrid(table, gridOptions=grid.build(), height=430, allow_unsafe_jscode=True, theme="streamlit", custom_css=custom_css, key=f"grid_{key}")
    csv_col, xlsx_col, _ = st.columns([1, 1, 3])
    csv_col.download_button("Baixar CSV", to_csv_bytes(table), f"{key}.csv", "text/csv", key=f"csv_{key}")
    xlsx_col.download_button("Baixar XLSX", to_xlsx_bytes(table), f"{key}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"xlsx_{key}")
