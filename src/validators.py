"""Validação estrutural dos arquivos de entrada."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

import pandas as pd

from src.config import REQUIRED_COLUMNS


class WorkbookValidationError(ValueError):
    """Erro esperado e apresentável ao usuário para planilhas inválidas."""


def validate_sheet_names(sheet_names: Iterable[str]) -> None:
    """Garante a presença de todas as abas obrigatórias."""
    available = set(sheet_names)
    missing = [sheet for sheet in REQUIRED_COLUMNS if sheet not in available]
    if missing:
        formatted = ", ".join(f"'{name}'" for name in missing)
        raise WorkbookValidationError(f"Abas obrigatórias ausentes: {formatted}.")


def missing_columns(frame: pd.DataFrame, sheet_name: str) -> list[str]:
    """Retorna colunas obrigatórias ausentes em uma aba."""
    expected = REQUIRED_COLUMNS.get(sheet_name, ())
    return [column for column in expected if column not in frame.columns]


def validate_columns(frames: Mapping[str, pd.DataFrame]) -> None:
    """Valida e relata todas as colunas ausentes em uma única mensagem."""
    errors: list[str] = []
    for sheet_name in REQUIRED_COLUMNS:
        if sheet_name not in frames:
            continue
        missing = missing_columns(frames[sheet_name], sheet_name)
        if missing:
            errors.append(f"aba '{sheet_name}': {', '.join(missing)}")
    if errors:
        raise WorkbookValidationError("Colunas obrigatórias ausentes — " + "; ".join(errors) + ".")

