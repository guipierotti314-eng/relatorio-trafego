"""Evolução usando as semanas informadas na planilha e ordem por data."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.formatters import format_currency_br, format_date_br, format_integer_br
from src.metrics import metric_is_available
from src.normalization import safe_divide
from src.views.common import apply_chart_theme, plotly_config, render_interactive_table, theme_colors


METRICS = {
    "Investimento": "investimento", "Resultados": "resultados",
    "Custo por resultado": "custo_resultado", "Alcance": "alcance",
    "Impressões": "impressoes",
}


def available_weekly_metrics(data: pd.DataFrame) -> list[str]:
    """Retorna somente métricas realmente presentes no recorte."""
    available = ["Investimento"] if metric_is_available(data, "investimento") else []
    recognized_results = data.dropna(subset=["categoria_resultado"])
    if metric_is_available(recognized_results, "resultados"):
        available.extend(["Resultados", "Custo por resultado"])
    if metric_is_available(data, "alcance"):
        available.append("Alcance")
    if metric_is_available(data, "impressoes"):
        available.append("Impressões")
    return available


def prepare_weekly_series(data: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Agrupa por semanas originais e ordena por início, sem calendário recalculado."""
    if data.empty:
        return pd.DataFrame()
    keys = ["inicio", "fim", "semana"]
    if metric in {"resultados", "custo_resultado"}:
        source = data.dropna(subset=["categoria_resultado"])
        grouped = source.groupby(keys + ["categoria_resultado"], as_index=False).agg(
            resultados=("resultados", "sum"), investimento=("investimento", "sum")
        )
        grouped["custo_resultado"] = [safe_divide(i, r) for i, r in zip(grouped.investimento, grouped.resultados)]
    else:
        grouped = data.groupby(keys, as_index=False).agg(
            investimento=("investimento", "sum"), alcance=("alcance", lambda values: values.sum(min_count=1)),
            impressoes=("impressoes", lambda values: values.sum(min_count=1)),
        )
        grouped["categoria_resultado"] = "Total"
    grouped = grouped.sort_values(["inicio", "fim", "categoria_resultado"], kind="stable")
    grouped["semana_id"] = grouped["inicio"].dt.strftime("%Y-%m-%d") + "_" + grouped["semana"].fillna("").astype(str)
    grouped["periodo"] = grouped.apply(
        lambda row: f"Semana {row.semana} | {format_date_br(row.inicio)} a {format_date_br(row.fim)}", axis=1
    )
    return grouped


def _format_metric(metric: str, value: float) -> str:
    return format_currency_br(value) if metric in {"investimento", "custo_resultado"} else format_integer_br(value)


def render(data: pd.DataFrame) -> None:
    st.header("Evolução semanal")
    options = available_weekly_metrics(data)
    if not options:
        st.info("Sem métricas disponíveis no período selecionado.")
        return
    if st.session_state.get("weekly_metric") not in options:
        st.session_state["weekly_metric"] = "Investimento" if "Investimento" in options else options[0]
    metric_label = st.selectbox("Métrica", options, key="weekly_metric")
    metric = METRICS[metric_label]
    weekly = prepare_weekly_series(data, metric)
    if weekly.empty:
        st.info("Sem dados para esta métrica.")
        return
    colors = [theme_colors()["primary"], "#8d939b", "#ff9a58", "#4f78a8", "#6c4b3b"]
    figure = go.Figure()
    for index, (category, group) in enumerate(weekly.groupby("categoria_resultado", sort=False)):
        custom = [[row.periodo, _format_metric(metric, getattr(row, metric))] for row in group.itertuples(index=False)]
        name = metric_label if category == "Total" else str(category)
        figure.add_trace(go.Scatter(
            x=group["semana_id"], y=group[metric], name=name, mode="lines+markers+text",
            line={"color": colors[index % len(colors)], "width": 3}, marker={"size": 8},
            text=[_format_metric(metric, value) for value in group[metric]], textposition="top center",
            customdata=custom, hovertemplate="%{customdata[0]} | %{customdata[1]}<extra></extra>",
        ))
    ticks = weekly.drop_duplicates("semana_id")
    figure.update_xaxes(
        title=None, tickmode="array", tickvals=ticks["semana_id"],
        ticktext=ticks["semana"].fillna("").astype(str),
    )
    figure.update_yaxes(title=metric_label)
    figure.update_layout(title=f"{metric_label} por semana", hovermode="closest")
    st.plotly_chart(apply_chart_theme(figure), use_container_width=True, config=plotly_config())
    unavailable = tuple(column for column in ("alcance", "impressoes") if not metric_is_available(data, column))
    render_interactive_table(weekly.drop(columns=["semana_id", "categoria_resultado"], errors="ignore"), "evolucao_semanal", "Semanas do período", unavailable)

