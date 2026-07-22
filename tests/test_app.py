from datetime import date
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest

from src.data_loader import load_excel_base


APP_PATH = Path(__file__).parents[1] / "app.py"


def write_workbook(
    path: Path,
    frames: dict[str, pd.DataFrame],
    include_second_month: bool = False,
) -> None:
    prepared = {name: frame.copy() for name, frame in frames.items()}
    if include_second_month:
        meta_second = prepared["dados-face"].copy()
        meta_second["Início dos relatórios"] = "01/06/2024"
        meta_second["Término dos relatórios"] = "08/06/2024"
        google_second = prepared["dados-google"].copy()
        google_second["Início"] = "01/06/2024"
        google_second["Fim"] = "08/06/2024"
        prepared["dados-face"] = pd.concat([prepared["dados-face"], meta_second], ignore_index=True)
        prepared["dados-google"] = pd.concat([prepared["dados-google"], google_second], ignore_index=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, frame in prepared.items():
            frame.to_excel(writer, sheet_name=sheet_name, index=False)


def run_app_with_base(path: Path) -> AppTest:
    load_excel_base.clear()
    with patch("src.config.BASE_EXCEL_PATH", path):
        return AppTest.from_file(str(APP_PATH), default_timeout=15).run()


def checkbox(app: AppTest, label: str):
    return next(item for item in app.checkbox if item.label == label)


def test_app_starts_when_repository_base_is_missing(tmp_path) -> None:
    app = run_app_with_base(tmp_path / "missing.xlsx")
    assert not app.exception
    assert app.title[0].value == "Dashboard de Tráfego pago"
    assert app.warning[0].value == "Não há dados disponíveis nesse período."
    assert not app.file_uploader


def test_theme_toggle_persists_in_session_when_base_is_missing(tmp_path) -> None:
    app = run_app_with_base(tmp_path / "missing.xlsx")
    app.button[0].click().run()
    assert not app.exception
    assert app.button[0].label == "☀️ Modo claro"


def test_repository_workbook_renders_checkbox_filters(tmp_path, valid_frames) -> None:
    path = tmp_path / "base_atual.xlsx"
    write_workbook(path, valid_frames)
    app = run_app_with_base(path)
    labels = [item.label for item in app.checkbox]
    assert not app.exception
    assert app.date_input[0].label == "Período"
    assert "Marca A" in labels and "Meta Ads" in labels
    assert "0 km" in labels and "Evento" in labels and "Cadastro" in labels
    assert not app.file_uploader and not app.selectbox and not app.multiselect and not app.radio


def test_period_change_preserves_every_advanced_filter(tmp_path, valid_frames) -> None:
    path = tmp_path / "base_atual.xlsx"
    write_workbook(path, valid_frames, include_second_month=True)
    with patch("src.config.BASE_EXCEL_PATH", path):
        app = run_app_with_base(path)
        for label in ("Marca A", "Meta Ads", "0 km", "Regular", "Engajamento"):
            checkbox(app, label).set_value(True).run()
        app.date_input[0].set_value((date(2024, 5, 1), date(2024, 5, 8))).run()
    assert not app.exception
    for label in ("Marca A", "Meta Ads", "0 km", "Regular", "Engajamento"):
        assert checkbox(app, label).value is True


def test_no_data_selection_is_preserved_and_message_is_rendered(tmp_path, valid_frames) -> None:
    path = tmp_path / "base_atual.xlsx"
    write_workbook(path, valid_frames)
    with patch("src.config.BASE_EXCEL_PATH", path):
        app = run_app_with_base(path)
        checkbox(app, "Marca A").set_value(True).run()
        checkbox(app, "Google Ads").set_value(True).run()
    assert checkbox(app, "Marca A").value is True
    assert checkbox(app, "Google Ads").value is True
    assert any(item.value == "Não há dados disponíveis nesse período" for item in app.info)


def test_result_type_is_mutually_exclusive(tmp_path, valid_frames) -> None:
    path = tmp_path / "base_atual.xlsx"
    write_workbook(path, valid_frames)
    with patch("src.config.BASE_EXCEL_PATH", path):
        app = run_app_with_base(path)
        checkbox(app, "Cadastro").set_value(True).run()
        checkbox(app, "Engajamento").set_value(True).run()
    assert checkbox(app, "Engajamento").value is True
    assert checkbox(app, "Cadastro").value is False


def test_only_overview_is_rendered_and_platform_chart_is_absent(tmp_path, valid_frames) -> None:
    path = tmp_path / "base_atual.xlsx"
    write_workbook(path, valid_frames)
    app = run_app_with_base(path)
    assert [header.value for header in app.header] == ["Visão geral"]
    assert not app.radio
    assert "Investimento por plataforma" not in APP_PATH.read_text(encoding="utf-8")
