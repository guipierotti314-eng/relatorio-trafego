"""Métricas consolidadas, sempre recalculadas após os filtros."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace

import pandas as pd

from src.normalization import safe_divide


def metric_is_available(data: pd.DataFrame, column: str) -> bool:
    """Indica se há ao menos um valor não nulo, mesmo que o total seja zero."""
    return not data.empty and column in data.columns and data[column].notna().any()


@dataclass(frozen=True)
class Metrics:
    """Totais e razões ponderadas de um conjunto filtrado."""

    investimento: float
    resultados: float
    cliques: float
    alcance: float
    impressoes: float
    custo_resultado: float
    custo_mil_alcancados: float
    cpc: float
    ctr: float
    cpm: float
    frequencia: float

    def as_dict(self) -> dict[str, float]:
        return asdict(self)


def _sum(data: pd.DataFrame, column: str) -> float:
    return float(pd.to_numeric(data[column], errors="coerce").sum(min_count=1)) if not data.empty else 0.0


def calculate_metrics(data: pd.DataFrame) -> Metrics:
    """Calcula totais e indicadores ponderados para o recorte recebido."""
    investment = _sum(data, "investimento")
    results = _sum(data, "resultados")
    clicks = _sum(data, "cliques")
    reach = _sum(data, "alcance")
    impressions = _sum(data, "impressoes")
    return Metrics(
        investimento=investment,
        resultados=results,
        cliques=clicks,
        alcance=reach,
        impressoes=impressions,
        custo_resultado=safe_divide(investment, results),
        custo_mil_alcancados=safe_divide(investment, reach, 1000.0),
        cpc=safe_divide(investment, clicks),
        ctr=safe_divide(clicks * 100, impressions),
        cpm=safe_divide(investment * 1000, impressions),
        frequencia=safe_divide(impressions, reach),
    )


def calculate_category_metrics(data: pd.DataFrame, category: str) -> Metrics:
    """Aplica a definição de resultado própria de cada categoria comercial."""
    metrics = calculate_metrics(data)
    if category == "Cliques":
        result = metrics.cliques
        return replace(
            metrics,
            resultados=result,
            custo_resultado=safe_divide(metrics.investimento, result),
        )
    if category == "Alcance":
        return replace(metrics, resultados=metrics.alcance)
    return metrics


def results_by_category(data: pd.DataFrame) -> pd.DataFrame:
    """Resume resultados incompatíveis separadamente por categoria."""
    columns = ["categoria_resultado", "resultados", "investimento", "custo_resultado"]
    if data.empty:
        return pd.DataFrame(columns=columns)
    rows = []
    for category, group in data.dropna(subset=["categoria_resultado"]).groupby("categoria_resultado"):
        metrics = calculate_category_metrics(group, str(category))
        cost = metrics.custo_mil_alcancados if category == "Alcance" else metrics.custo_resultado
        rows.append({
            "categoria_resultado": category,
            "resultados": metrics.resultados,
            "investimento": metrics.investimento,
            "custo_resultado": cost,
        })
    return pd.DataFrame(rows, columns=columns)


def aggregate_dimension(data: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """Agrega métricas e abre cada categoria de resultado em colunas."""
    base_columns = [dimension, "investimento", "alcance", "impressoes", "participacao_investimento"]
    if data.empty:
        return pd.DataFrame(columns=base_columns)
    totals = data.groupby(dimension, dropna=False).agg(
        investimento=("investimento", "sum"),
        alcance=("alcance", "sum"), impressoes=("impressoes", "sum"),
    ).reset_index()
    investment_total = totals["investimento"].sum()
    totals["participacao_investimento"] = totals["investimento"].map(lambda value: safe_divide(value * 100, investment_total))
    grouped = data.groupby([dimension, "categoria_resultado"], dropna=False).agg(
        resultados=("resultados", "sum"), investimento_categoria=("investimento", "sum")
    ).reset_index()
    grouped["custo_categoria"] = [
        safe_divide(investment, results)
        for investment, results in zip(grouped["investimento_categoria"], grouped["resultados"])
    ]
    result_pivot = grouped.pivot(index=dimension, columns="categoria_resultado", values="resultados")
    result_pivot.columns = [f"resultados_{str(column).lower()}" for column in result_pivot.columns]
    cost_pivot = grouped.pivot(index=dimension, columns="categoria_resultado", values="custo_categoria")
    cost_pivot.columns = [f"custo_resultado_{str(column).lower()}" for column in cost_pivot.columns]
    separated = result_pivot.join(cost_pivot).reset_index()
    return totals.merge(separated, on=dimension, how="left")
