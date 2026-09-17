import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from src.ingestion.at_client import (
    fetch_trip_updates,
    fetch_vehicle_positions,
    fetch_service_alerts,
)


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


def get_entity_count(data):
    feed = data.get("response", data)
    return len(feed.get("entity", []))


def save_json(data, filename):
    output_file = RAW_DATA_DIR / filename

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    return output_file


def collect_all_realtime_data():
    print("Collecting Auckland Transport live data...")
    print("-----------------------------------------")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    try:
        # 1. Trip updates
        trip_data = fetch_trip_updates()
        trip_count = get_entity_count(trip_data)

        trip_file = save_json(
            trip_data,
            f"tripupdates_{timestamp}.json",
        )

        print("Trip updates:", trip_count)

        # 2. Vehicle positions
        vehicle_data = fetch_vehicle_positions()
        vehicle_count = get_entity_count(vehicle_data)

        vehicle_file = save_json(
            vehicle_data,
            f"vehiclepositions_{timestamp}.json",
        )

        print("Vehicle positions:", vehicle_count)

        # 3. Service alerts
        alert_data = fetch_service_alerts()
        alert_count = get_entity_count(alert_data)

        alert_file = save_json(
            alert_data,
            f"servicealerts_{timestamp}.json",
        )

        print("Service alerts:", alert_count)

        logging.info(
            "Collection successful | trips=%s | vehicles=%s | alerts=%s",
            trip_count,
            vehicle_count,
            alert_count,
        )

        print("\nCollection successful.")
        print("Files saved:")
        print(trip_file)
        print(vehicle_file)
        print(alert_file)

    except Exception as error:
        logging.exception("Realtime collection failed")
        print("Collection failed:", error)
        raise


if __name__ == "__main__":
    collect_all_realtime_data()