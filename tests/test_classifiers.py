import pytest

from src.classifiers import (
    classify_action_type,
    classify_campaign,
    classify_campaign_segment,
    classify_result_type,
    identify_place,
    is_event_campaign,
    standardize_brand,
)


def test_sn_is_seminovos() -> None:
    assert classify_campaign("Campanha FLN/SN", "Marca") == "Seminovos"


def test_seminovos_has_priority_over_event() -> None:
    assert classify_campaign("[Evento] Campanha /SN", "Marca") == "Seminovos"


def test_event_and_default_campaign_are_zero_km_segment() -> None:
    assert classify_campaign("[EVENTO] Feirão", "Marca") == "0 km"
    assert classify_campaign("Institucional", "Marca") == "0 km"


def test_event_has_independent_segment_and_action_type() -> None:
    assert classify_campaign_segment("[Evento] Feirão Hyundai", "Hyundai HMB") == "0 km"
    assert classify_action_type("[Evento] Feirão Hyundai") == "Evento"


def test_used_event_is_both_seminovos_and_event() -> None:
    campaign = "[Evento] Feirão Seminovos /SN"
    assert classify_campaign_segment(campaign, "Marca") == "Seminovos"
    assert classify_action_type(campaign) == "Evento"


def test_regular_action_type() -> None:
    assert classify_action_type("[Tráfego] WhatsApp Hyundai BRQ") == "Regular"


@pytest.mark.parametrize(
    "campaign",
    [
        "[Evento] Cadastro Hyundai",
        "[EVENTO] Cadastro Hyundai",
        "[ Evento ] Cadastro Hyundai",
        "[Tráfego] [Evento] Cadastro",
        "Campanha Evento Hyundai",
        "Cadastro Hyundai - evento FLN",
    ],
)
def test_event_is_recognized_as_a_complete_word_anywhere(campaign: str) -> None:
    assert is_event_campaign(campaign)
    assert classify_action_type(campaign) == "Evento"


@pytest.mark.parametrize("campaign", ["Campanha regular", "Eventual Hyundai", "Pré-eventoide", ""])
def test_non_event_campaign_does_not_match_partial_word(campaign: str) -> None:
    assert not is_event_campaign(campaign)
    assert classify_action_type(campaign) == "Regular"


@pytest.mark.parametrize(
    ("campaign", "expected"),
    [
        ("Ação SJ/ILHA", "SJ/ILHA"), ("Ação FLN", "FLN"),
        ("Ação ILHA", "SJ/ILHA"), ("Ação ILHA/SN", "ILHA/SN"),
        ("Ação LGS", "LGS"), ("Ação LAG", "LGS"),
        ("Ação BRQ", "BRQ"), ("Ação BRU", "BRQ"),
        ("Ação Palhoca", "Palhoça"),
    ],
)
def test_place_aliases(campaign: str, expected: str) -> None:
    assert identify_place(campaign) == expected


def test_ilha_sn_has_priority_over_ilha() -> None:
    assert identify_place("Campanha ILHA/SN especial") == "ILHA/SN"


def test_alias_does_not_match_part_of_word() -> None:
    assert identify_place("Campanha CRIATIVA") is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Cliques no link", "Cliques"), ("Conversas por mensagem", "Engajamento"),
        ("Alcance", "Alcance"), ("Cadastro (lead)", "Cadastro"),
        ("Visualização", None),
    ],
)
def test_result_type_classification(raw: str, expected: str | None) -> None:
    assert classify_result_type(raw) == expected


@pytest.mark.parametrize(
    "raw",
    ["Conversas por mensagem iniciadas", "conversas por mensagem iniciadas", "MENSAGENS", "Mensagem iniciada"],
)
def test_message_variations_are_engagement(raw: str) -> None:
    assert classify_result_type(raw) == "Engajamento"


@pytest.mark.parametrize(
    "raw",
    ["Cadastro concluído", "Cadastros", "Lead", "Leads", "Formulário enviado", "formulario", "Preenchimento", "Conversão de cadastro"],
)
def test_registration_variations_are_cadastro(raw: str) -> None:
    assert classify_result_type(raw) == "Cadastro"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Geração CAOA Chery", "Chery"), ("Chery", "Chery"),
        ("Geração Omoda e Jaecoo", "Geração Omoda Jaecoo"),
        ("Geração omoda jaecoo", "Geração Omoda Jaecoo"),
        ("Hyundai Geração", "Hyundai HMB"),
        ("Geração Hyundai HMB", "Hyundai HMB"),
        ("Geração Yamaha", "Yamaha"), ("Yamaha YMH", "Yamaha"),
        ("Geração Seminovos", "Geração Seminovos"),
        ("S2 Bike Shop", "S2 Bike Shop"),
        ("S2 Bike Shop Floripa", "S2 Bike Shop"),
        ("  Marca   Regional  ", "Marca Regional"),
    ],
)
def test_brand_standardization(raw: str, expected: str) -> None:
    assert standardize_brand(raw) == expected


def test_brand_alias_matching_is_not_partial() -> None:
    assert standardize_brand("Chery Especial") == "Chery Especial"
