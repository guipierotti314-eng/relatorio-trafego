"""Carregamento centralizado da base Excel versionada no repositório."""

from __future__ import annotations

from pathlib import Path
from zipfile import BadZipFile

from openpyxl.utils.exceptions import InvalidFileException
import pandas as pd
import streamlit as st

from src.config import REQUIRED_COLUMNS
from src.normalization import NormalizationResult, normalize_workbook
from src.validators import WorkbookValidationError, validate_columns, validate_sheet_names


def _validate_base_path(path: Path) -> None:
    """Valida o arquivo físico antes de acessar ou armazenar seu conteúdo em cache."""
    try:
        if not path.exists():
            raise FileNotFoundError("Arquivo base não encontrado.")
        if not path.is_file():
            raise WorkbookValidationError("O caminho configurado não aponta para um arquivo.")
        if path.suffix.lower() != ".xlsx":
            raise WorkbookValidationError("Formato de arquivo incompatível; utilize um arquivo XLSX.")
        size = path.stat().st_size
    except PermissionError as exc:
        raise WorkbookValidationError("Sem permissão para acessar o arquivo base.") from exc
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise WorkbookValidationError("Não foi possível consultar o arquivo base.") from exc
    if size == 0:
        raise WorkbookValidationError("O arquivo Excel está vazio.")


def get_file_signature(path: Path) -> tuple[int, int]:
    """Retorna modificação em nanossegundos e tamanho para invalidar o cache."""
    _validate_base_path(path)
    try:
        stat = path.stat()
    except PermissionError as exc:
        raise WorkbookValidationError("Sem permissão para acessar o arquivo base.") from exc
    except OSError as exc:
        raise WorkbookValidationError("Não foi possível consultar o arquivo base.") from exc
    return stat.st_mtime_ns, stat.st_size


@st.cache_data(show_spinner="Carregando dados...")
def load_excel_base(
    path_as_string: str,
    file_signature: tuple[int, int],
) -> NormalizationResult:
    """Lê, valida e normaliza as abas da base, preservando o contrato do dashboard.

    ``file_signature`` participa da chave do cache. O conteúdo não é usado pela
    função porque sua finalidade é invalidar a leitura quando o arquivo físico
    for substituído mantendo o mesmo caminho.
    """
    del file_signature
    path = Path(path_as_string)
    _validate_base_path(path)
    try:
        frames = pd.read_excel(path, sheet_name=None, engine="openpyxl")
    except PermissionError as exc:
        raise WorkbookValidationError("Sem permissão para ler o arquivo base.") from exc
    except (BadZipFile, InvalidFileException, ValueError) as exc:
        raise WorkbookValidationError("Não foi possível abrir o arquivo como Excel válido.") from exc
    except OSError as exc:
        raise WorkbookValidationError("Não foi possível ler o arquivo base.") from exc
    except Exception as exc:
        raise WorkbookValidationError("Falha inesperada ao abrir o arquivo Excel.") from exc

    validate_sheet_names(frames.keys())
    required_frames = {sheet: frames[sheet] for sheet in REQUIRED_COLUMNS}
    validate_columns(required_frames)
    if all(frame.empty for frame in required_frames.values()):
        raise WorkbookValidationError("As abas obrigatórias não possuem registros.")

    result = normalize_workbook(required_frames)
    if result.data.empty or result.valid_count == 0:
        raise WorkbookValidationError("A base não possui registros válidos após a normalização.")
    return result
