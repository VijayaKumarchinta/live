from dataclasses import dataclass, field
from typing import List
import pandas as pd

@dataclass
class ValidationResult:
    ok: bool
    errors: List[str] = field(default_factory=list)
    rejected_row_indices: List[int] = field(default_factory=list)
    rejected_reasons: List[str] = field(default_factory=list)

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

    if df["ts"].isna().any():
        bad = df.index[df["ts"].isna()].tolist()
        result.rejected_row_indices.extend(int(i) for i in bad)
        result.rejected_reasons.extend(["null ts"] * len(bad))
        result.errors.append(f"{len(bad)} rows have null ts")
    return result