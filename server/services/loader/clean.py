import hashlib
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd

SOURCE_XLSX = Path(r"..\archive\backfill\Line_Speed_30.xlsx").resolve()
CLEAN_PARQUET = Path(r"..\archive\backfill\line_speed_30_clean.parquet").resolve()
SHEET_NAME = "Line_Speed_30"
TZ = "Asia/Kolkata"
EXCEL_HEADERS_TO_DROP = {"Millitm"}
EXCEL_HEADERS_TO_RENAME = {";Date": "Date"}

def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def clean() -> pd.DataFrame:
    if not SOURCE_XLSX.exists():
        raise SystemExit(f"source not found: {SOURCE_XLSX}")

    raw = pd.read_excel(SOURCE_XLSX, sheet_name=SHEET_NAME)
    print(f"raw shape: {raw.shape}")
    print(f"raw columns: {list(raw.columns)}")

    df = raw.rename(columns=EXCEL_HEADERS_TO_RENAME)
    df = df.drop(columns=[c for c in EXCEL_HEADERS_TO_DROP if c in df.columns])

    if "Date" not in df.columns or "Time" not in df.columns:
        raise SystemExit("missing Date/Time after rename")

    date_str = df["Date"].astype(str).str.strip()
    time_str = df["Time"].astype(str).str.strip()
    combined = date_str + " " + time_str

    naive = pd.to_datetime(combined, format="%m/%d/%Y %H:%M:%S", errors="coerce")
    bad_mask = naive.isna()
    bad_count = int(bad_mask.sum())
    if bad_count:
        print(f"rejecting {bad_count} rows with unparseable Date/Time")
        df = df.loc[~bad_mask].reset_index(drop=True)
        naive = naive.loc[~bad_mask].reset_index(drop=True)

    df["ts"] = naive.dt.tz_localize(ZoneInfo(TZ))

    df = df.drop(columns=["Date", "Time"])

    if df["ts"].is_monotonic_increasing:
        print("timestamps are strictly increasing")
    else:
        print("timestamps are NOT monotonic; sorting")
        df = df.sort_values("ts").reset_index(drop=True)

    sensor_cols = [c for c in df.columns if c != "ts"]
    numeric_df = df[sensor_cols].apply(pd.to_numeric, errors="coerce")
    converted = (df[sensor_cols].dtypes != numeric_df.dtypes).sum()
    df[sensor_cols] = numeric_df
    if converted:
        print(f"coerced {converted} non-numeric columns to numeric")

    nan_counts = df[sensor_cols].isna().sum()
    total_nan = int(nan_counts.sum())
    print(f"total NaN sensor cells: {total_nan}")
    if total_nan:
        top = nan_counts[nan_counts > 0].sort_values(ascending=False).head(10)
        print("NaN per column (top 10):")
        print(top.to_string())

    df = df[["ts"] + sensor_cols]

    if df["ts"].duplicated().any():
        dup_count = int(df["ts"].duplicated().sum())
        print(f"dropping {dup_count} rows with duplicate ts")
        df = df.drop_duplicates(subset="ts", keep="first").reset_index(drop=True)

    print(f"clean shape: {df.shape}")
    print(f"ts range: {df['ts'].min()} .. {df['ts'].max()}")
    print(f"row count: {len(df)}")
    return df

def main() -> None:
    df = clean()
    CLEAN_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CLEAN_PARQUET, index=False)
    print(f"wrote: {CLEAN_PARQUET}")
    print(f"parquet bytes: {CLEAN_PARQUET.stat().st_size}")
    print(f"source sha256: {sha256_of(SOURCE_XLSX)}")
    print(f"parquet sha256: {sha256_of(CLEAN_PARQUET)}")

if __name__ == "__main__":
    main()