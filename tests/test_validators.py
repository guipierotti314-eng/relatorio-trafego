import pandas as pd
import pytest

from src.validators import WorkbookValidationError, validate_columns, validate_sheet_names


def test_missing_required_sheet() -> None:
    with pytest.raises(WorkbookValidationError, match="dados-google"):
        validate_sheet_names(["dados-face"])


def test_missing_required_column(valid_frames) -> None:
    frames = dict(valid_frames)
    frames["dados-google"] = frames["dados-google"].drop(columns=["CPC"])
    with pytest.raises(WorkbookValidationError, match="CPC"):
        validate_columns(frames)


def test_valid_columns_pass(valid_frames) -> None:
    validate_columns(valid_frames)

