"""Geração de arquivos para download sem dependência da interface."""

from __future__ import annotations

from io import BytesIO

import pandas as pd


def to_csv_bytes(data: pd.DataFrame) -> bytes:
    """Exporta CSV compatível com Excel brasileiro."""
    return data.to_csv(index=False, sep=";", decimal=",", encoding="utf-8-sig").encode("utf-8-sig")


def to_xlsx_bytes(data: pd.DataFrame, sheet_name: str = "dados") -> bytes:
    """Exporta DataFrame para XLSX em memória."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        data.to_excel(writer, index=False, sheet_name=sheet_name[:31])
    return buffer.getvalue()

