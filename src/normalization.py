"""Conversão e normalização das fontes Meta Ads e Google Ads."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

import pandas as pd

from src.classifiers import (
    classify_action_type,
    classify_campaign_segment,
    classify_result_type,
    identify_place,
    standardize_brand,
)
from src.config import NORMALIZED_COLUMNS, SHEET_GOOGLE, SHEET_META
from src.validators import validate_columns


@dataclass(frozen=True)
class NormalizationResult:
    """Dados normalizados e inconsistências encontradas no processamento."""

    data: pd.DataFrame
    issues: pd.DataFrame

    @property
    def valid_count(self) -> int:
        return int(self.data["registro_valido"].sum())

    @property
    def invalid_count(self) -> int:
        return int((~self.data["registro_valido"]).sum())

    @property
    def unidentified_place_count(self) -> int:
        return int(self.data["praca"].isna().sum())


def parse_br_number(value: Any) -> float:
    """Converte número brasileiro, moeda e percentuais; inválidos viram NaN."""
    if value is None or pd.isna(value):
        return float("nan")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    text = str(value).strip()
    if not text:
        return float("nan")
    text = re.sub(r"[^0-9,.-]", "", text)
    if not text or text in {"-", ".", ","}:
        return float("nan")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"-?\d{1,3}(?:\.\d{3})+", text):
        text = text.replace(".", "")
    try:
        return float(text)
    except ValueError:
        return float("nan")


def parse_br_date(value: Any) -> pd.Timestamp | pd.NaT:
    """Converte uma data com prioridade para dia/mês/ano."""
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return pd.NaT
    parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
    return pd.NaT if pd.isna(parsed) else pd.Timestamp(parsed).normalize()


def clean_text(value: Any) -> str | pd.NA:
    """Remove espaços externos e duplicados, preservando ausências."""
    if value is None or pd.isna(value):
        return pd.NA
    cleaned = " ".join(str(value).strip().split())
    return cleaned if cleaned else pd.NA


def safe_divide(numerator: float, denominator: float, multiplier: float = 1.0) -> float:
    """Divide valores sem gerar infinito ou erro para zero/ausência."""
    if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
        return float("nan")
    return (float(numerator) / float(denominator)) * multiplier


def _issue(
    issues: list[dict[str, Any]], sheet: str, row_index: Any, column: str, value: Any, message: str
) -> None:
    issues.append(
        {
            "aba": sheet,
            "linha_excel": int(row_index) + 2 if isinstance(row_index, int) else str(row_index),
            "coluna": column,
            "valor_original": value,
            "problema": message,
        }
    )


def _convert_column(
    source: pd.DataFrame,
    column: str,
    parser: Any,
    issues: list[dict[str, Any]],
    sheet: str,
) -> pd.Series:
    converted = source[column].map(parser)
    for index in source.index:
        original = source.at[index, column]
        non_empty = not pd.isna(original) and str(original).strip() != ""
        if non_empty and pd.isna(converted.at[index]):
            _issue(issues, sheet, index, column, original, "Valor não pôde ser convertido")
    return converted


def _check_required_values(
    source: pd.DataFrame, columns: tuple[str, ...], issues: list[dict[str, Any]], sheet: str
) -> None:
    for column in columns:
        for index, value in source[column].items():
            if pd.isna(value) or str(value).strip() == "":
                _issue(issues, sheet, index, column, value, "Valor obrigatório vazio")


def _normalize_meta(source: pd.DataFrame, issues: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(index=source.index)
    frame["plataforma"] = "Meta Ads"
    frame["marca_original"] = source["Nome da Página"]
    frame["marca"] = source["Nome da Página"].map(standardize_brand)
    frame["campanha"] = source["Nome da campanha"].map(clean_text)
    frame["tipo_campanha_origem"] = pd.NA
    frame["tipo_resultado_origem"] = source["Tipo de resultado"].map(clean_text)
    frame["categoria_resultado"] = source["Tipo de resultado"].map(classify_result_type)
    numeric_map = {
        "resultados": "Resultados",
        "cliques": "Cliques (todos)",
        "alcance": "Alcance",
        "impressoes": "Impressões",
        "investimento": "Valor usado (BRL)",
        "custo_resultado": "Custo por resultado",
    }
    for target, origin in numeric_map.items():
        frame[target] = _convert_column(source, origin, parse_br_number, issues, SHEET_META)
    frame["cpc"] = [safe_divide(cost, clicks) for cost, clicks in zip(frame["investimento"], frame["cliques"])]
    frame["inicio"] = _convert_column(source, "Início dos relatórios", parse_br_date, issues, SHEET_META)
    frame["fim"] = _convert_column(source, "Término dos relatórios", parse_br_date, issues, SHEET_META)
    frame["semana"] = source["Semana"].map(clean_text)
    frame["segmento_campanha"] = [
        classify_campaign_segment(campaign, brand) for campaign, brand in zip(frame["campanha"], frame["marca"])
    ]
    frame["tipo_acao"] = frame["campanha"].map(classify_action_type)
    frame["praca"] = frame["campanha"].map(identify_place)
    _check_required_values(
        source,
        ("Nome da campanha", "Início dos relatórios", "Término dos relatórios"),
        issues,
        SHEET_META,
    )
    frame["aba_origem"] = SHEET_META
    frame["linha_excel"] = [int(index) + 2 if isinstance(index, int) else str(index) for index in source.index]
    return frame


def _normalize_google(source: pd.DataFrame, issues: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(index=source.index)
    frame["plataforma"] = "Google Ads"
    frame["marca_original"] = source["Marca"]
    frame["marca"] = source["Marca"].map(standardize_brand)
    frame["campanha"] = source["Campanha"].map(clean_text)
    frame["tipo_campanha_origem"] = source["Tipo de campanha"].map(clean_text)
    frame["tipo_resultado_origem"] = "Cliques"
    frame["categoria_resultado"] = "Cliques"
    frame["cliques"] = _convert_column(source, "Cliques", parse_br_number, issues, SHEET_GOOGLE)
    frame["resultados"] = frame["cliques"]
    frame["alcance"] = float("nan")
    for target, origin in {"impressoes": "Impr.", "investimento": "Custo", "cpc": "CPC"}.items():
        frame[target] = _convert_column(source, origin, parse_br_number, issues, SHEET_GOOGLE)
    frame["custo_resultado"] = [
        safe_divide(cost, clicks) for cost, clicks in zip(frame["investimento"], frame["cliques"])
    ]
    frame["inicio"] = _convert_column(source, "Início", parse_br_date, issues, SHEET_GOOGLE)
    frame["fim"] = _convert_column(source, "Fim", parse_br_date, issues, SHEET_GOOGLE)
    frame["semana"] = source["Semana"].map(clean_text)
    frame["segmento_campanha"] = [
        classify_campaign_segment(campaign, brand) for campaign, brand in zip(frame["campanha"], frame["marca"])
    ]
    frame["tipo_acao"] = frame["campanha"].map(classify_action_type)
    frame["praca"] = frame["campanha"].map(identify_place)
    _check_required_values(source, ("Campanha", "Início", "Fim"), issues, SHEET_GOOGLE)
    frame["aba_origem"] = SHEET_GOOGLE
    frame["linha_excel"] = [int(index) + 2 if isinstance(index, int) else str(index) for index in source.index]
    return frame


def normalize_workbook(frames: dict[str, pd.DataFrame]) -> NormalizationResult:
    """Valida, normaliza e une as duas plataformas em uma estrutura comum."""
    validate_columns(frames)
    issues: list[dict[str, Any]] = []
    meta = _normalize_meta(frames[SHEET_META].copy(), issues)
    google = _normalize_google(frames[SHEET_GOOGLE].copy(), issues)
    data = pd.concat([meta, google], ignore_index=True)
    issue_frame = pd.DataFrame(
        issues, columns=["aba", "linha_excel", "coluna", "valor_original", "problema"]
    )
    invalid_keys = {
        (str(row.aba), str(row.linha_excel)) for row in issue_frame.itertuples(index=False)
    }
    data["registro_valido"] = [
        (str(sheet), str(row)) not in invalid_keys
        for sheet, row in zip(data["aba_origem"], data["linha_excel"])
    ]
    issue_messages: dict[tuple[str, str], list[str]] = {}
    for row in issue_frame.itertuples(index=False):
        key = (str(row.aba), str(row.linha_excel))
        issue_messages.setdefault(key, []).append(f"{row.coluna}: {row.problema}")
    data["problemas"] = [
        "; ".join(issue_messages.get((str(sheet), str(row)), []))
        for sheet, row in zip(data["aba_origem"], data["linha_excel"])
    ]
    ordered = list(NORMALIZED_COLUMNS) + [
        "aba_origem",
        "linha_excel",
        "registro_valido",
        "problemas",
    ]
    return NormalizationResult(data=data[ordered], issues=issue_frame)
