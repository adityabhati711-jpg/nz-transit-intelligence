import csv
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent

STATIC_DIR = BASE_DIR / "data" / "static" / "latest"
RAW_DIR = BASE_DIR / "data" / "raw"


def load_ids(filename, column_name):
    file_path = STATIC_DIR / filename

    with open(
        file_path,
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        return {
            str(row[column_name]).strip()
            for row in reader
            if row.get(column_name)
        }


def get_latest_trip_update_file():
    files = list(RAW_DIR.glob("tripupdates_*.json"))

    if not files:
        raise FileNotFoundError(
            "No trip update JSON files found in data/raw."
        )

    return max(files, key=lambda path: path.stat().st_mtime)


def percentage(matched, total):
    if total == 0:
        return 0.0

    return (matched / total) * 100


def main():
    print("Loading GTFS Static IDs...")

    static_trip_ids = load_ids(
        "trips.txt",
        "trip_id",
    )

    static_route_ids = load_ids(
        "routes.txt",
        "route_id",
    )

    static_stop_ids = load_ids(
        "stops.txt",
        "stop_id",
    )

    latest_file = get_latest_trip_update_file()

    print("Using realtime file:")
    print(latest_file.name)

    with open(
        latest_file,
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    feed = data.get("response", data)
    entities = feed.get("entity", [])

    realtime_trip_ids = set()
    realtime_route_ids = set()
    realtime_stop_ids = set()

    for entity in entities:
        if not isinstance(entity, dict):
            continue

        trip_update = entity.get("trip_update", {})

        if not isinstance(trip_update, dict):
            continue

        trip = trip_update.get("trip", {})

        if isinstance(trip, dict):
            trip_id = trip.get("trip_id")
            route_id = trip.get("route_id")

            if trip_id:
                realtime_trip_ids.add(
                    str(trip_id).strip()
                )

            if route_id:
                realtime_route_ids.add(
                    str(route_id).strip()
                )

        stop_updates = trip_update.get(
            "stop_time_update"
        )

        if isinstance(stop_updates, dict):
            stop_updates = [stop_updates]

        elif not isinstance(stop_updates, list):
            stop_updates = []

        for stop_update in stop_updates:
            if not isinstance(stop_update, dict):
                continue

            stop_id = stop_update.get("stop_id")

            if stop_id:
                realtime_stop_ids.add(
                    str(stop_id).strip()
                )

    matched_trips = len(
        realtime_trip_ids & static_trip_ids
    )

    matched_routes = len(
        realtime_route_ids & static_route_ids
    )

    matched_stops = len(
        realtime_stop_ids & static_stop_ids
    )

    print("\nREALTIME <-> STATIC MATCH TEST")
    print("------------------------------")

    print(
        f"Trips: {matched_trips}/{len(realtime_trip_ids)} "
        f"({percentage(matched_trips, len(realtime_trip_ids)):.2f}%)"
    )

    print(
        f"Routes: {matched_routes}/{len(realtime_route_ids)} "
        f"({percentage(matched_routes, len(realtime_route_ids)):.2f}%)"
    )

    print(
        f"Stops: {matched_stops}/{len(realtime_stop_ids)} "
        f"({percentage(matched_stops, len(realtime_stop_ids)):.2f}%)"
    )

    unmatched_routes = sorted(
        realtime_route_ids - static_route_ids
    )

    unmatched_trips = sorted(
        realtime_trip_ids - static_trip_ids
    )

    unmatched_stops = sorted(
        realtime_stop_ids - static_stop_ids
    )

    print("\nUNMATCHED SUMMARY")
    print("-----------------")

    print(
        "Unmatched routes:",
        len(unmatched_routes),
    )

    print(
        "Unmatched trips:",
        len(unmatched_trips),
    )

    print(
        "Unmatched stops:",
        len(unmatched_stops),
    )

    print("\nSample unmatched realtime route IDs:")
    print("------------------------------------")

    for route_id in unmatched_routes[:20]:
        print(route_id)

    print("\nSample unmatched realtime trip IDs:")
    print("-----------------------------------")

    for trip_id in unmatched_trips[:10]:
        print(trip_id)

    if not unmatched_routes:
        print("No unmatched route IDs found.")

    if not unmatched_trips:
        print("No unmatched trip IDs found.")


if __name__ == "__main__":
    main()