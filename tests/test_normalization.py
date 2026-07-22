import math

import pandas as pd
import pytest

from src.normalization import normalize_workbook, parse_br_date, parse_br_number, safe_divide
from src.metrics import calculate_metrics


def test_parse_integer_with_thousands_separator() -> None:
    assert parse_br_number("1.738") == 1738


def test_parse_decimal_with_thousands_separator() -> None:
    assert parse_br_number("2.472,58") == pytest.approx(2472.58)


def test_parse_currency() -> None:
    assert parse_br_number("R$ 241,99") == pytest.approx(241.99)


def test_parse_brazilian_date() -> None:
    assert parse_br_date("09/05/2024") == pd.Timestamp("2024-05-09")


def test_safe_divide_by_zero() -> None:
    assert math.isnan(safe_divide(100, 0))


def test_normalization_unites_platforms_and_keeps_google_reach_missing(valid_frames) -> None:
    result = normalize_workbook(valid_frames)
    assert set(result.data["plataforma"]) == {"Meta Ads", "Google Ads"}
    google = result.data.loc[result.data["plataforma"] == "Google Ads"].iloc[0]
    assert pd.isna(google["alcance"])
    assert google["resultados"] == google["cliques"] == 100
    assert google["custo_resultado"] == pytest.approx(2.0)


def test_invalid_nonempty_value_is_reported(valid_frames) -> None:
    valid_frames["dados-face"].loc[0, "Resultados"] = "inválido"
    result = normalize_workbook(valid_frames)
    assert result.invalid_count == 1
    assert "Resultados" in set(result.issues["coluna"])


def test_missing_brand_is_valid_and_preserved(valid_frames) -> None:
    valid_frames["dados-google"].loc[0, "Marca"] = pd.NA
    result = normalize_workbook(valid_frames)
    google = result.data.loc[result.data["plataforma"] == "Google Ads"].iloc[0]
    assert google["registro_valido"]
    assert pd.isna(google["marca"])


def test_original_brand_is_preserved_and_canonical_brand_is_used(valid_frames) -> None:
    valid_frames["dados-google"].loc[0, "Marca"] = "Geração Hyundai HMB"
    result = normalize_workbook(valid_frames)
    google = result.data.loc[result.data["plataforma"] == "Google Ads"].iloc[0]
    assert google["marca_original"] == "Geração Hyundai HMB"
    assert google["marca"] == "Hyundai HMB"


def test_engagement_metrics_use_conversations(valid_frames) -> None:
    valid_frames["dados-face"].loc[0, "Tipo de resultado"] = "Conversas por mensagem iniciadas"
    valid_frames["dados-face"].loc[0, "Resultados"] = "25"
    valid_frames["dados-face"].loc[0, "Valor usado (BRL)"] = "500,00"
    result = normalize_workbook(valid_frames)
    engagement = result.data.loc[result.data["categoria_resultado"] == "Engajamento"]
    metrics = calculate_metrics(engagement)
    assert metrics.resultados == 25
    assert metrics.custo_resultado == pytest.approx(20)


def test_event_normalizes_segment_and_action_independently(valid_frames) -> None:
    valid_frames["dados-face"].loc[0, "Nome da campanha"] = "[Evento] Feirão Hyundai FLN"
    valid_frames["dados-face"].loc[0, "Tipo de resultado"] = "Lead"
    result = normalize_workbook(valid_frames)
    event = result.data.loc[result.data["plataforma"] == "Meta Ads"].iloc[0]
    assert event["segmento_campanha"] == "0 km"
    assert event["tipo_acao"] == "Evento"
    assert event["categoria_resultado"] == "Cadastro"


def test_event_action_survives_platform_union(valid_frames) -> None:
    valid_frames["dados-face"].loc[0, "Nome da campanha"] = "[ Evento ] Cadastro Hyundai FLN"
    valid_frames["dados-google"].loc[0, "Campanha"] = "Pesquisa Evento Hyundai BRQ"

    result = normalize_workbook(valid_frames)

    assert result.data["tipo_acao"].tolist() == ["Evento", "Evento"]
