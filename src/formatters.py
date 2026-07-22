"""Formatação brasileira centralizada para interface e tooltips."""

from __future__ import annotations

from datetime import date, datetime
import math

import pandas as pd


def _number_br(value: float, decimals: int) -> str:
    if value is None or not math.isfinite(float(value)):
        return "—"
    rendered = f"{float(value):,.{decimals}f}"
    return rendered.translate(str.maketrans({",": ".", ".": ","}))


def format_currency_br(value: float) -> str:
    formatted = _number_br(value, 2)
    return "—" if formatted == "—" else f"R$ {formatted}"


def format_integer_br(value: float) -> str:
    return _number_br(value, 0)


def format_decimal_br(value: float, decimals: int = 2) -> str:
    return _number_br(value, decimals)


def format_percentage_br(value: float, decimals: int = 1) -> str:
    """Formata uma razão (0,324) como percentual (32,4%)."""
    formatted = _number_br(float(value) * 100, decimals)
    return "—" if formatted == "—" else f"{formatted}%"


def format_percentage_points_br(value: float | None, decimals: int = 1) -> str:
    """Formata um valor já expresso em pontos percentuais."""
    if value is None:
        return "—"
    formatted = _number_br(value, decimals)
    return "—" if formatted == "—" else f"{formatted}%"


def format_date_br(value: date | datetime | pd.Timestamp) -> str:
    return pd.Timestamp(value).strftime("%d/%m/%Y")


def format_date_range_br(
    start: date | datetime | pd.Timestamp,
    end: date | datetime | pd.Timestamp,
) -> str:
    return f"{format_date_br(start)} a {format_date_br(end)}"


# Compatibilidade interna com chamadas existentes.
format_currency = format_currency_br
format_integer = format_integer_br
format_decimal = format_decimal_br
format_percent = format_percentage_points_br
