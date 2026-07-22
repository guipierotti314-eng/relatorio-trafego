"""Configurações centralizadas de colunas e regras de negócio."""

from __future__ import annotations

from pathlib import Path


# config.py fica em src/; portanto o diretório pai de src é a raiz do projeto.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE_EXCEL_PATH = PROJECT_ROOT / "dados" / "base_atual.xlsx"
SHOW_TECHNICAL_DETAILS = False

SHEET_META = "dados-face"
SHEET_GOOGLE = "dados-google"

REQUIRED_COLUMNS: dict[str, tuple[str, ...]] = {
    SHEET_META: (
        "Nome da Página",
        "Nome da campanha",
        "Tipo de resultado",
        "Resultados",
        "Alcance",
        "Impressões",
        "Custo por resultado",
        "Cliques (todos)",
        "Valor usado (BRL)",
        "Início dos relatórios",
        "Término dos relatórios",
        "Semana",
    ),
    SHEET_GOOGLE: (
        "Marca",
        "Campanha",
        "Tipo de campanha",
        "Cliques",
        "Impr.",
        "Custo",
        "CPC",
        "Início",
        "Fim",
        "Semana",
    ),
}

NORMALIZED_COLUMNS: tuple[str, ...] = (
    "plataforma",
    "marca_original",
    "marca",
    "campanha",
    "tipo_campanha_origem",
    "tipo_resultado_origem",
    "categoria_resultado",
    "segmento_campanha",
    "tipo_acao",
    "praca",
    "resultados",
    "cliques",
    "alcance",
    "impressoes",
    "investimento",
    "custo_resultado",
    "cpc",
    "inicio",
    "fim",
    "semana",
)

# A ordem é relevante: ILHA/SN > SJ/ILHA > ILHA > FLN.
PLACE_ALIASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("ILHA/SN", ("ILHA/SN",)),
    ("SJ/ILHA", ("SJ/ILHA", "ILHA")),
    ("FLN", ("FLN",)),
    ("Palhoça", ("PALHOÇA", "PALHOCA")),
    ("LGS", ("LGS", "LAG")),
    ("BRQ", ("BRQ", "BRU")),
    ("RDS", ("RDS",)),
    ("CRI", ("CRI",)),
    ("TUB", ("TUB",)),
    ("ING", ("ING",)),
)

THEME_COLORS: dict[str, dict[str, str]] = {
    "light": {
        "background": "#f5f6f8", "surface": "#ffffff", "surface_secondary": "#eef0f3",
        "text_primary": "#17181a", "text_secondary": "#626870", "border": "#dfe2e6",
        "primary": "#ff6600", "primary_hover": "#dc5800", "positive": "#18864b",
        "negative": "#c9362b", "neutral": "#6b7280", "grid": "#e8eaed",
    },
    "dark": {
        "background": "#111214", "surface": "#1b1d20", "surface_secondary": "#25282c",
        "text_primary": "#f4f5f6", "text_secondary": "#b8bdc4", "border": "#3a3e44",
        "primary": "#ff6600", "primary_hover": "#ff7a24", "positive": "#42c77a",
        "negative": "#ff6b62", "neutral": "#a7adb5", "grid": "#33373c",
    },
}

HIDDEN_DIMENSION_VALUES = {"Não identificada", "Desconhecida", "Indefinida", "Geral"}

# Comparações são feitas contra o texto completo normalizado, nunca por substituição parcial.
BRAND_ALIASES: dict[str, tuple[str, ...]] = {
    "Chery": ("geracao caoa chery", "caoa chery", "chery"),
    "Geração Omoda Jaecoo": (
        "geracao omoda e jaecoo", "geracao omoda jaecoo",
        "omoda e jaecoo", "omoda jaecoo",
    ),
    "Hyundai HMB": (
        "hyundai geracao", "geracao hyundai", "hyundai hmb", "geracao hyundai hmb",
    ),
    "Yamaha": ("geracao yamaha", "yamaha", "yamaha ymh"),
    "Geração Seminovos": ("geracao seminovos",),
    "S2 Bike Shop": ("s2 bike shop", "s2 bike shop floripa"),
    "Geração Motos Multimarcas": (
        "geracao motos multimarcas",
        "geracao motos seminovas",
        "motos multimarcas",
    ),
}

RESULT_CATEGORY_OPTIONS: tuple[str, ...] = (
    "Engajamento", "Cliques", "Cadastro", "Alcance",
)

PLACE_ORDER: tuple[str, ...] = (
    "FLN", "SJ/ILHA", "ILHA/SN", "LGS", "BRQ",
    "RDS", "CRI", "TUB", "Palhoça", "ING",
)

METRIC_BEHAVIOR: dict[str, str] = {
    "investimento": "higher_is_positive",
    "resultados": "higher_is_positive",
    "alcance": "higher_is_positive",
    "impressoes": "higher_is_positive",
    "custo_resultado": "lower_is_positive",
    "custo_mil_alcancados": "lower_is_positive",
}
