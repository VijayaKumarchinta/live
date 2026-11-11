from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from services.loader.validator import validate_dataframe


def _base_df(n: int = 3, tz: str = "Asia/Kolkata") -> pd.DataFrame:
    ts = pd.date_range("2026-04-17 12:00:00", periods=n, freq="10s", tz=tz)
    return pd.DataFrame(
        {
            "ts": ts,
            "s1": [1.0, 2.0, 3.0][:n],
            "s2": [10.0, 20.0, 30.0][:n],
        }
    )


def test_valid_frame_passes():
    df = _base_df()
    r = validate_dataframe(df, ["s1", "s2"])
    assert r.ok
    assert r.rejected_row_indices == []


def test_missing_ts_column():
    df = _base_df().drop(columns=["ts"])
    r = validate_dataframe(df, ["s1", "s2"])
    assert not r.ok
    assert any("missing 'ts'" in e for e in r.errors)


def test_missing_sensor_column():
    df = _base_df()
    r = validate_dataframe(df, ["s1", "s2", "s_missing"])
    assert not r.ok
    assert any("missing sensor columns" in e for e in r.errors)


def test_empty_dataframe():
    df = _base_df().iloc[0:0]
    r = validate_dataframe(df, ["s1", "s2"])
    assert not r.ok
    assert any("empty" in e for e in r.errors)


def test_naive_timestamp_rejected():
    df = _base_df()
    df["ts"] = df["ts"].dt.tz_localize(None)
    r = validate_dataframe(df, ["s1", "s2"])
    assert not r.ok
    assert any("timezone-aware" in e for e in r.errors)


def test_null_ts_row_rejected():
    df = _base_df()
    df.loc[1, "ts"] = pd.NaT
    r = validate_dataframe(df, ["s1", "s2"])
    assert 1 in r.rejected_row_indices
    assert any("null ts" in reason for reason in r.rejected_reasons)


def test_duplicate_ts_rejected():
    df = _base_df()
    df.loc[2, "ts"] = df.loc[1, "ts"]
    r = validate_dataframe(df, ["s1", "s2"])
    assert 1 in r.rejected_row_indices
    assert 2 in r.rejected_row_indices
    assert any("duplicate ts" in reason for reason in r.rejected_reasons)


def test_non_numeric_sensor_value_rejected():
    df = _base_df()
    df["s1"] = df["s1"].astype(object)
    df.loc[1, "s1"] = "not_a_number"
    r = validate_dataframe(df, ["s1", "s2"])
    assert 1 in r.rejected_row_indices
    assert any("non-numeric" in reason for reason in r.rejected_reasons)


def test_infinite_sensor_value_rejected():
    df = _base_df()
    df.loc[1, "s1"] = np.inf
    r = validate_dataframe(df, ["s1", "s2"])
    assert 1 in r.rejected_row_indices
    assert any("infinite" in reason for reason in r.rejected_reasons)


def test_non_monotonic_ts_rejected():
    df = _base_df()
    df = df.iloc[[0, 2, 1]].reset_index(drop=True)
    r = validate_dataframe(df, ["s1", "s2"])
    assert not r.ok
    assert any("monotonic" in e for e in r.errors)