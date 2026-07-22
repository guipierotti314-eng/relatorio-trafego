"""Tipos reconhecidos de resultado, sempre apresentados separadamente."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.formatters import format_integer_br
from src.metrics import metric_is_available, results_by_category
from src.views.common import apply_chart_theme, plotly_config, render_interactive_table, theme_colors


def render(data: pd.DataFrame) -> None:
    st.header("Tipos de resultado")
    recognized = data.dropna(subset=["categoria_resultado"])
    if not metric_is_available(recognized, "resultados"):
        st.info("Sem resultados classificados disponíveis no período.")
        return
    summary = results_by_category(recognized)
    if not summary.empty:
        custom = [[row.categoria_resultado, format_integer_br(row.resultados)] for row in summary.itertuples(index=False)]
        figure = go.Figure(go.Bar(
            x=summary["categoria_resultado"], y=summary["resultados"], customdata=custom,
            marker_color=theme_colors()["primary"], text=[format_integer_br(value) for value in summary["resultados"]],
            textposition="outside", hovertemplate="%{customdata[0]} | %{customdata[1]} resultados<extra></extra>",
        ))
        figure.update_layout(title="Resultados por tipo", xaxis_title=None, yaxis_title="Resultados")
        st.plotly_chart(apply_chart_theme(figure), use_container_width=True, config=plotly_config())
    render_interactive_table(summary, "tipos_de_resultado", "Resultados e custos por tipo")
