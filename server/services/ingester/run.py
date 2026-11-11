import argparse
import logging
from services.ingester.processor import Ingester

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="MQTT ingester")
    parser.add_argument("--line", type=int, default=30)
    args = parser.parse_args()
    Ingester(line_id=args.line).run()

if __name__ == "__main__":
    main()