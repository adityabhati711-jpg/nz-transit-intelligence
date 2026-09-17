import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from src.ingestion.at_client import fetch_trip_updates


BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
LOG_DIR = BASE_DIR / "logs"

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


logging.basicConfig(
    filename=LOG_DIR / "collector.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def collect_trip_updates():
    print("Collecting live Auckland Transport trip updates...")

    try:
        data = fetch_trip_updates()

        feed = data.get("response", data)
        entities = feed.get("entity", [])

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        output_file = RAW_DATA_DIR / f"tripupdates_{timestamp}.json"

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

        logging.info(
            "Trip updates collected successfully | entities=%s | file=%s",
            len(entities),
            output_file.name,
        )

        print("Collection successful.")
        print("Entities:", len(entities))
        print("Saved to:", output_file)

    except Exception as error:
        logging.exception("Trip update collection failed")
        print("Collection failed:", error)
        raise


if __name__ == "__main__":
    collect_trip_updates()