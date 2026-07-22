from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pytest

from src.config import BASE_EXCEL_PATH, PROJECT_ROOT
from src.data_loader import get_file_signature, load_excel_base
from src.normalization import NormalizationResult
from src.validators import WorkbookValidationError


def write_workbook(path: Path, frames: dict[str, pd.DataFrame]) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, frame in frames.items():
            frame.to_excel(writer, sheet_name=sheet_name, index=False)


@pytest.fixture(autouse=True)
def clear_loader_cache():
    load_excel_base.clear()
    yield
    load_excel_base.clear()


def test_repository_path_is_absolute_and_independent_from_cwd(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert BASE_EXCEL_PATH.is_absolute()
    assert BASE_EXCEL_PATH == PROJECT_ROOT / "dados" / "base_atual.xlsx"


def test_valid_base_preserves_required_sheets_and_pipeline_contract(tmp_path, valid_frames) -> None:
    path = tmp_path / "base_atual.xlsx"
    write_workbook(path, valid_frames)
    result = load_excel_base(str(path), get_file_signature(path))
    assert isinstance(result, NormalizationResult)
    assert set(result.data["plataforma"]) == {"Meta Ads", "Google Ads"}


def test_loader_calls_pandas_with_openpyxl(tmp_path, valid_frames, monkeypatch) -> None:
    path = tmp_path / "base_atual.xlsx"
    write_workbook(path, valid_frames)
    original = pd.read_excel
    calls: list[dict[str, object]] = []

    def spy(*args, **kwargs):
        calls.append(kwargs.copy())
        return original(*args, **kwargs)

    monkeypatch.setattr(pd, "read_excel", spy)
    load_excel_base(str(path), get_file_signature(path))
    assert calls and calls[0]["engine"] == "openpyxl"
    assert calls[0]["sheet_name"] is None


def test_missing_file_raises_controlled_error(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="Arquivo base não encontrado"):
        get_file_signature(tmp_path / "base_atual.xlsx")


def test_empty_file_raises_controlled_error(tmp_path) -> None:
    path = tmp_path / "base_atual.xlsx"
    path.touch()
    with pytest.raises(WorkbookValidationError, match="arquivo Excel está vazio"):
        get_file_signature(path)


def test_corrupted_file_raises_controlled_error(tmp_path) -> None:
    path = tmp_path / "base_atual.xlsx"
    path.write_bytes(b"not-an-excel-file")
    with pytest.raises(WorkbookValidationError, match="Excel válido"):
        load_excel_base(str(path), get_file_signature(path))


def test_missing_required_sheet_raises_controlled_error(tmp_path, valid_frames) -> None:
    path = tmp_path / "base_atual.xlsx"
    write_workbook(path, {"dados-face": valid_frames["dados-face"]})
    with pytest.raises(WorkbookValidationError, match="dados-google"):
        load_excel_base(str(path), get_file_signature(path))


def test_missing_required_column_raises_controlled_error(tmp_path, valid_frames) -> None:
    path = tmp_path / "base_atual.xlsx"
    valid_frames["dados-face"] = valid_frames["dados-face"].drop(columns=["Nome da campanha"])
    write_workbook(path, valid_frames)
    with pytest.raises(WorkbookValidationError, match="Nome da campanha"):
        load_excel_base(str(path), get_file_signature(path))


def test_workbook_without_rows_raises_controlled_error(tmp_path, valid_frames) -> None:
    path = tmp_path / "base_atual.xlsx"
    empty = {name: frame.iloc[0:0] for name, frame in valid_frames.items()}
    write_workbook(path, empty)
    with pytest.raises(WorkbookValidationError, match="não possuem registros"):
        load_excel_base(str(path), get_file_signature(path))


def test_signature_changes_when_file_is_updated(tmp_path, valid_frames) -> None:
    path = tmp_path / "base_atual.xlsx"
    write_workbook(path, valid_frames)
    first = get_file_signature(path)
    with path.open("ab") as stream:
        stream.write(b"updated")
    os.utime(path, None)
    second = get_file_signature(path)
    assert second != first


def test_signature_participates_in_cache_key(tmp_path, valid_frames, monkeypatch) -> None:
    path = tmp_path / "base_atual.xlsx"
    write_workbook(path, valid_frames)
    original = pd.read_excel
    calls = 0

    def spy(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(pd, "read_excel", spy)
    first_signature = get_file_signature(path)
    load_excel_base(str(path), first_signature)
    load_excel_base(str(path), first_signature)
    assert calls == 1

    valid_frames["dados-face"] = pd.concat(
        [valid_frames["dados-face"], valid_frames["dados-face"]], ignore_index=True
    )
    write_workbook(path, valid_frames)
    load_excel_base(str(path), get_file_signature(path))
    assert calls == 2
