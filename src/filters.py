"""Filtros temporais e dimensionais independentes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from src.config import HIDDEN_DIMENSION_VALUES


@dataclass(frozen=True)
class DateRange:
    start: pd.Timestamp
    end: pd.Timestamp


def available_date_range(data: pd.DataFrame) -> DateRange | None:
    if data.empty or "inicio" not in data or "fim" not in data:
        return None
    starts, ends = data["inicio"].dropna(), data["fim"].dropna()
    if starts.empty and ends.empty:
        return None
    candidates_min = [value for value in (starts.min() if not starts.empty else None, ends.min() if not ends.empty else None) if value is not None]
    candidates_max = [value for value in (starts.max() if not starts.empty else None, ends.max() if not ends.empty else None) if value is not None]
    return DateRange(pd.Timestamp(min(candidates_min)).normalize(), pd.Timestamp(max(candidates_max)).normalize())


def default_latest_month_range(data: pd.DataFrame) -> DateRange | None:
    bounds = available_date_range(data)
    if bounds is None:
        return None
    return DateRange(max(bounds.end.replace(day=1), bounds.start), bounds.end)


def filter_by_period(data: pd.DataFrame, start: date | pd.Timestamp, end: date | pd.Timestamp) -> pd.DataFrame:
    """Inclui integralmente intervalos que intersectem a seleção, sem rateio."""
    start_ts, end_ts = pd.Timestamp(start).normalize(), pd.Timestamp(end).normalize()
    if start_ts > end_ts:
        raise ValueError("A data inicial não pode ser posterior à data final.")
    return data.loc[data["inicio"].le(end_ts) & data["fim"].ge(start_ts)].copy()


def dimension_options(data: pd.DataFrame, column: str) -> list[str]:
    if data.empty or column not in data:
        return []
    values = data[column].dropna().astype(str).str.strip()
    values = values.loc[values.ne("") & ~values.isin(HIDDEN_DIMENSION_VALUES)]
    return sorted(values.unique().tolist(), key=str.casefold)


def _selected_values(selected: str | tuple[str, ...] | list[str]) -> tuple[str, ...]:
    if isinstance(selected, str):
        return () if selected == "Todos" else (selected,)
    return tuple(value for value in selected if value != "Todos")


def _filter_in(data: pd.DataFrame, column: str, selected: str | tuple[str, ...] | list[str]) -> pd.DataFrame:
    values = _selected_values(selected)
    return data.copy() if not values else data.loc[data[column].isin(values)].copy()


def apply_platform_filter(data: pd.DataFrame, selected: str | tuple[str, ...] | list[str]) -> pd.DataFrame:
    return _filter_in(data, "plataforma", selected)


def apply_brand_filter(data: pd.DataFrame, selected: tuple[str, ...] | list[str]) -> pd.DataFrame:
    return _filter_in(data, "marca", selected)


def apply_segment_filter(data: pd.DataFrame, selected: str | tuple[str, ...] | list[str]) -> pd.DataFrame:
    return _filter_in(data, "segmento_campanha", selected)


def apply_action_type_filter(data: pd.DataFrame, selected: str | tuple[str, ...] | list[str]) -> pd.DataFrame:
    return _filter_in(data, "tipo_acao", selected)


def apply_result_type_filter(data: pd.DataFrame, selected: str) -> pd.DataFrame:
    return _filter_in(data, "categoria_resultado", selected)


def apply_dimension_filters(
    data: pd.DataFrame,
    platforms: tuple[str, ...] = (),
    brands: tuple[str, ...] = (),
    campaign_segments: tuple[str, ...] = (),
    action_types: tuple[str, ...] = (),
    result_category: str = "Todos",
) -> pd.DataFrame:
    """Aplica cada dimensão somente à própria coluna, na ordem documentada."""
    filtered = apply_platform_filter(data, platforms)
    filtered = apply_brand_filter(filtered, brands)
    filtered = apply_segment_filter(filtered, campaign_segments)
    filtered = apply_action_type_filter(filtered, action_types)
    return apply_result_type_filter(filtered, result_category)
