import argparse
import json
from pathlib import Path
from services.loader.backfill import run_backfill

def main() -> None:
    parser = argparse.ArgumentParser(description="Historical backfill loader")
    parser.add_argument("--file", required=True, help="Path to the cleaned Parquet file")
    parser.add_argument("--line", type=int, required=True, help="Line identifier")
    args = parser.parse_args()

    path = Path(args.file).resolve()
    if not path.exists():
        raise SystemExit(f"file not found: {path}")

    result = run_backfill(path, args.line)
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    main()