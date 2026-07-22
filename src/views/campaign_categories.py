"""Comparação das categorias comerciais de campanha."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.formatters import format_currency_br
from src.metrics import aggregate_dimension, metric_is_available
from src.views.common import apply_chart_theme, plotly_config, render_interactive_table, theme_colors
from src.views.overview import build_budget_donut


def render(data: pd.DataFrame) -> None:
    st.header("Segmentos de campanha")
    segmented = data.dropna(subset=["segmento_campanha"])
    summary = aggregate_dimension(segmented, "segmento_campanha")
    if not summary.empty:
        custom = [[row.segmento_campanha, format_currency_br(row.investimento)] for row in summary.itertuples(index=False)]
        figure = go.Figure(go.Bar(
            x=summary["segmento_campanha"], y=summary["investimento"], customdata=custom,
            marker_color=theme_colors()["primary"], text=[format_currency_br(value) for value in summary["investimento"]],
            textposition="outside", hovertemplate="%{customdata[0]} | %{customdata[1]}<extra></extra>",
        ))
        figure.update_layout(title="Investimento por categoria", xaxis_title=None, yaxis_title="Investimento")
        left, right = st.columns([1, 1.35])
        left.plotly_chart(apply_chart_theme(figure), use_container_width=True, config=plotly_config())
        right.plotly_chart(build_budget_donut(segmented, str(st.session_state.get("theme_mode", "light"))), use_container_width=True, config=plotly_config())
    unavailable_list = [column for column in ("alcance", "impressoes") if not metric_is_available(segmented, column)]
    if not metric_is_available(segmented.dropna(subset=["categoria_resultado"]), "resultados"):
        unavailable_list.extend(column for column in summary.columns if column.startswith(("resultados_", "custo_resultado_")))
    unavailable = tuple(unavailable_list)
    render_interactive_table(summary, "categorias_de_campanha", "Comparativo de categorias", unavailable)
