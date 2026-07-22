"""Funções puras para classificação de campanhas, resultados e praças."""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

from src.config import BRAND_ALIASES, PLACE_ALIASES


def normalize_for_match(value: object) -> str:
    """Normaliza texto para comparações sem caixa ou acentos."""
    if value is None or pd.isna(value):
        return ""
    text = " ".join(str(value).strip().split())
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char)).upper()


def classify_result_type(value: object) -> str | None:
    """Agrupa o tipo de resultado do Meta em uma categoria comercial."""
    text = normalize_for_match(value)
    if any(term in text for term in ("CADASTR", "LEAD", "FORMULARIO", "PREENCHIMENTO", "CONVERSAO DE CADASTRO")):
        return "Cadastro"
    if "CLIQUE" in text:
        return "Cliques"
    if "CONVERSA" in text or "MENSAG" in text:
        return "Engajamento"
    if "ALCANCE" in text:
        return "Alcance"
    return None


def standardize_brand(value: object) -> str | None:
    """Consolida aliases exatos de marca e preserva nomes não configurados."""
    if value is None or pd.isna(value):
        return None
    cleaned = " ".join(str(value).strip().split())
    if not cleaned:
        return None
    normalized = normalize_for_match(cleaned).casefold()
    for canonical, aliases in BRAND_ALIASES.items():
        if normalized in aliases:
            return canonical
    return cleaned


def classify_campaign_segment(campaign: object, brand: object) -> str:
    """Classifica o segmento independentemente de a campanha ser um evento."""
    campaign_text = normalize_for_match(campaign)
    brand_text = normalize_for_match(brand)
    if "/SN" in campaign_text or "ILHA/SN" in campaign_text or "SEMINOVOS" in campaign_text or brand_text == "GERACAO SEMINOVOS":
        return "Seminovos"
    return "0 km"


def is_event_campaign(campaign: object) -> bool:
    """Reconhece a palavra completa ``evento`` em qualquer posição do nome."""
    text = normalize_for_match(campaign)
    if not text:
        return False
    return re.search(r"(?<![A-Z0-9])EVENTO(?![A-Z0-9])", text) is not None


def classify_action_type(campaign: object) -> str:
    """Indica se a ação é Evento sem alterar o segmento comercial."""
    return "Evento" if is_event_campaign(campaign) else "Regular"


def classify_campaign(campaign: object, brand: object) -> str:
    """Alias compatível para a classificação de segmento."""
    return classify_campaign_segment(campaign, brand)


def _contains_alias(text: str, alias: str) -> bool:
    """Localiza um alias completo, aceitando separadores comuns nas bordas."""
    normalized_alias = normalize_for_match(alias)
    pattern = rf"(?<![A-Z0-9]){re.escape(normalized_alias)}(?![A-Z0-9])"
    return re.search(pattern, text) is not None


def identify_place(campaign: object) -> str | None:
    """Identifica a praça pelo nome da campanha usando aliases configuráveis."""
    text = normalize_for_match(campaign)
    for place, aliases in PLACE_ALIASES:
        for alias in aliases:
            if _contains_alias(text, alias):
                return place
    return None
