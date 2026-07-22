"""Cálculo de intervalos comparativos e variações percentuais."""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ComparisonPeriod:
    """Intervalo anterior equivalente e indicação de ajuste de calendário."""

    start: pd.Timestamp
    end: pd.Timestamp
    adjusted: bool = False


def _previous_month_date(value: pd.Timestamp) -> tuple[pd.Timestamp, bool]:
    year, month = value.year, value.month - 1
    if month == 0:
        year, month = year - 1, 12
    last_day = monthrange(year, month)[1]
    day = min(value.day, last_day)
    return pd.Timestamp(year=year, month=month, day=day), day != value.day


def previous_period(start: pd.Timestamp, end: pd.Timestamp, period_type: str) -> ComparisonPeriod:
    """Calcula o mês anterior inteiro ou os mesmos dias do mês anterior."""
    start, end = pd.Timestamp(start).normalize(), pd.Timestamp(end).normalize()
    if start > end:
        raise ValueError("A data inicial não pode ser posterior à data final.")
    if period_type.casefold() == "mês":
        previous_start, _ = _previous_month_date(start.replace(day=1))
        previous_end = previous_start + pd.offsets.MonthEnd(0)
        return ComparisonPeriod(previous_start, pd.Timestamp(previous_end), False)
    if period_type.casefold() != "semana":
        raise ValueError("Tipo de período deve ser 'Semana' ou 'Mês'.")
    previous_start, adjusted_start = _previous_month_date(start)
    previous_end, adjusted_end = _previous_month_date(end)
    return ComparisonPeriod(previous_start, previous_end, adjusted_start or adjusted_end)


def percentage_change(current: float, previous: float) -> float | None:
    """Calcula variação percentual; zero ou ausência anterior não são comparáveis."""
    if pd.isna(current) or pd.isna(previous) or previous == 0:
        return None
    return ((float(current) - float(previous)) / float(previous)) * 100

