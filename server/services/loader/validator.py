from dataclasses import dataclass, field
from typing import List
import numpy as np
import pandas as pd

@dataclass
class ValidationResult:
    ok: bool
    errors: List[str] = field(default_factory=list)
    rejected_row_indices: List[int] = field(default_factory=list)
    rejected_reasons: List[str] = field(default_factory=list)

def _reject(result: ValidationResult, idx: int, reason: str) -> None:
    result.rejected_row_indices.append(int(idx))
    result.rejected_reasons.append(reason)

def validate_dataframe(df: pd.DataFrame, sensor_columns: List[str]) -> ValidationResult:
    result = ValidationResult(ok=True)

    if "ts" not in df.columns:
        result.ok = False
        result.errors.append("missing 'ts' column")
        return result

    missing_sensors = [c for c in sensor_columns if c not in df.columns]
    if missing_sensors:
        result.ok = False
        result.errors.append(f"missing sensor columns: {missing_sensors}")
        return result

    if df.empty:
        result.ok = False
        result.errors.append("dataframe is empty")
        return result

    ts_series = df["ts"]

    if ts_series.isna().any():
        for idx in df.index[ts_series.isna()].tolist():
            _reject(result, idx, "null ts")

    try:
        tz = ts_series.dt.tz
        if tz is None:
            result.ok = False
            result.errors.append("ts is not timezone-aware")
    except Exception as exc:
        result.ok = False
        result.errors.append(f"ts dtype is not datetime: {exc}")
        return result

    if ts_series.duplicated().any():
        dup_mask = ts_series.duplicated(keep=False)
        for idx in df.index[dup_mask].tolist():
            _reject(result, idx, "duplicate ts")

    non_null_ts = ts_series.dropna()
    if not non_null_ts.is_monotonic_increasing:
        result.ok = False
        result.errors.append("ts is not monotonic increasing")

    for col in sensor_columns:
        series = df[col]
        if series.dtype == object:
            coerced = pd.to_numeric(series, errors="coerce")
            bad_mask = coerced.isna() & series.notna()
            for idx in df.index[bad_mask].tolist():
                _reject(result, idx, f"non-numeric value in {col}")
            df[col] = coerced
        if df[col].dtype.kind in ("f", "i"):
            inf_mask = np.isinf(df[col].to_numpy(dtype=float, na_value=np.nan))
            for idx in df.index[np.where(inf_mask)[0]].tolist():
                _reject(result, idx, f"infinite value in {col}")

    if result.rejected_row_indices:
        result.errors.append(f"{len(result.rejected_row_indices)} rows rejected")

    return result