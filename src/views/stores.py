"""Desempenho por praça, excluindo ausências apenas da segmentação."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.comparisons import percentage_change
from src.formatters import format_currency_br
from src.metrics import aggregate_dimension, metric_is_available
from src.views.common import apply_chart_theme, plotly_config, render_interactive_table, theme_colors


def render(data: pd.DataFrame, previous: pd.DataFrame) -> None:
    st.header("Desempenho por praça")
    segmented = data.dropna(subset=["praca"])
    prior_segmented = previous.dropna(subset=["praca"])
    current = aggregate_dimension(segmented, "praca")
    prior = aggregate_dimension(prior_segmented, "praca")
    if not current.empty:
        prior_values = prior.set_index("praca") if not prior.empty else pd.DataFrame()
        current["variacao_investimento"] = current.apply(
            lambda row: percentage_change(row.investimento, prior_values.at[row.praca, "investimento"])
            if not prior_values.empty and row.praca in prior_values.index else None, axis=1
        )
        for column in [name for name in current.columns if name.startswith("resultados_")]:
            current[f"variacao_{column}"] = current.apply(
                lambda row: percentage_change(row[column], prior_values.at[row.praca, column])
                if not prior_values.empty and row.praca in prior_values.index and column in prior_values else None,
                axis=1,
            )
        ordered = current.sort_values("investimento")
        custom = [[row.praca, format_currency_br(row.investimento)] for row in ordered.itertuples(index=False)]
        figure = go.Figure(go.Bar(
            x=ordered["investimento"], y=ordered["praca"], orientation="h", customdata=custom,
            marker_color=theme_colors()["primary"], text=[format_currency_br(value) for value in ordered["investimento"]],
            textposition="outside", hovertemplate="%{customdata[0]} | %{customdata[1]}<extra></extra>",
        ))
        figure.update_layout(title="Investimento por praça", xaxis_title="Investimento", yaxis_title=None)
        st.plotly_chart(apply_chart_theme(figure), use_container_width=True, config=plotly_config())
    unavailable_list = [column for column in ("alcance", "impressoes") if not metric_is_available(segmented, column)]
    if not metric_is_available(segmented.dropna(subset=["categoria_resultado"]), "resultados"):
        unavailable_list.extend(column for column in current.columns if column.startswith(("resultados_", "custo_resultado_", "variacao_resultados_")))
    unavailable = tuple(unavailable_list)
    render_interactive_table(current, "desempenho_por_praca", "Indicadores por praça", unavailable)
    if metric_is_available(segmented, "alcance"):
        st.caption("O alcance é somado e pode conter sobreposição entre campanhas.")
