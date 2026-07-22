import pandas as pd
import pytest

from src.comparisons import percentage_change, previous_period


def test_same_interval_previous_month() -> None:
    period = previous_period(pd.Timestamp("2024-05-09"), pd.Timestamp("2024-05-17"), "Semana")
    assert period.start == pd.Timestamp("2024-04-09")
    assert period.end == pd.Timestamp("2024-04-17")
    assert not period.adjusted


def test_january_moves_to_previous_year() -> None:
    period = previous_period(pd.Timestamp("2024-01-05"), pd.Timestamp("2024-01-12"), "Semana")
    assert period.start == pd.Timestamp("2023-12-05")
    assert period.end == pd.Timestamp("2023-12-12")


def test_invalid_day_is_adjusted_to_last_day() -> None:
    period = previous_period(pd.Timestamp("2024-03-31"), pd.Timestamp("2024-03-31"), "Semana")
    assert period.start == pd.Timestamp("2024-02-29")
    assert period.adjusted


def test_full_month_comparison() -> None:
    period = previous_period(pd.Timestamp("2024-05-01"), pd.Timestamp("2024-05-31"), "Mês")
    assert period.start == pd.Timestamp("2024-04-01")
    assert period.end == pd.Timestamp("2024-04-30")


def test_percentage_change_has_no_infinity_for_zero() -> None:
    assert percentage_change(10, 0) is None
    assert percentage_change(120, 100) == pytest.approx(20)

