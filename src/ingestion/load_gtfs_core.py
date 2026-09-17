import csv
from pathlib import Path

from sqlalchemy import text

from src.database import engine


BASE_DIR = Path(__file__).resolve().parent.parent.parent
GTFS_DIR = BASE_DIR / "data" / "static" / "latest"

BATCH_SIZE = 5000


def to_int(value):
    if value is None or value == "":
        return None

    try:
        return int(value)
    except ValueError:
        return None


def to_float(value):
    if value is None or value == "":
        return None

    try:
        return float(value)
    except ValueError:
        return None


def execute_batches(connection, statement, rows):
    batch = []

    for row in rows:
        batch.append(row)

        if len(batch) >= BATCH_SIZE:
            connection.execute(
                text(statement),
                batch,
            )
            batch.clear()

    if batch:
        connection.execute(
            text(statement),
            batch,
        )


def read_csv(filename):
    file_path = GTFS_DIR / filename

    with open(
        file_path,
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        yield from csv.DictReader(file)


def load_routes(connection):
    print("Loading routes...")

    rows = []

    for row in read_csv("routes.txt"):
        rows.append({
            "route_id": row.get("route_id"),
            "agency_id": row.get("agency_id"),
            "route_short_name": row.get("route_short_name"),
            "route_long_name": row.get("route_long_name"),
            "route_type": to_int(row.get("route_type")),
            "route_color": row.get("route_color"),
            "route_text_color": row.get("route_text_color"),
        })

    statement = """
        INSERT INTO gtfs_routes (
            route_id,
            agency_id,
            route_short_name,
            route_long_name,
            route_type,
            route_color,
            route_text_color
        )
        VALUES (
            :route_id,
            :agency_id,
            :route_short_name,
            :route_long_name,
            :route_type,
            :route_color,
            :route_text_color
        )
        ON CONFLICT (route_id)
        DO UPDATE SET
            agency_id = EXCLUDED.agency_id,
            route_short_name = EXCLUDED.route_short_name,
            route_long_name = EXCLUDED.route_long_name,
            route_type = EXCLUDED.route_type,
            route_color = EXCLUDED.route_color,
            route_text_color = EXCLUDED.route_text_color
    """

    execute_batches(
        connection,
        statement,
        rows,
    )


def load_stops(connection):
    print("Loading stops...")

    rows = []

    for row in read_csv("stops.txt"):
        rows.append({
            "stop_id": row.get("stop_id"),
            "stop_name": row.get("stop_name"),
            "stop_lat": to_float(row.get("stop_lat")),
            "stop_lon": to_float(row.get("stop_lon")),
            "location_type": to_int(row.get("location_type")),
            "parent_station": row.get("parent_station") or None,
        })

    statement = """
        INSERT INTO gtfs_stops (
            stop_id,
            stop_name,
            stop_lat,
            stop_lon,
            location_type,
            parent_station
        )
        VALUES (
            :stop_id,
            :stop_name,
            :stop_lat,
            :stop_lon,
            :location_type,
            :parent_station
        )
        ON CONFLICT (stop_id)
        DO UPDATE SET
            stop_name = EXCLUDED.stop_name,
            stop_lat = EXCLUDED.stop_lat,
            stop_lon = EXCLUDED.stop_lon,
            location_type = EXCLUDED.location_type,
            parent_station = EXCLUDED.parent_station
    """

    execute_batches(
        connection,
        statement,
        rows,
    )


def load_trips(connection):
    print("Loading trips...")

    rows = []

    for row in read_csv("trips.txt"):
        rows.append({
            "trip_id": row.get("trip_id"),
            "route_id": row.get("route_id"),
            "service_id": row.get("service_id"),
            "trip_headsign": row.get("trip_headsign"),
            "direction_id": to_int(row.get("direction_id")),
            "shape_id": row.get("shape_id"),
        })

    statement = """
        INSERT INTO gtfs_trips (
            trip_id,
            route_id,
            service_id,
            trip_headsign,
            direction_id,
            shape_id
        )
        VALUES (
            :trip_id,
            :route_id,
            :service_id,
            :trip_headsign,
            :direction_id,
            :shape_id
        )
        ON CONFLICT (trip_id)
        DO UPDATE SET
            route_id = EXCLUDED.route_id,
            service_id = EXCLUDED.service_id,
            trip_headsign = EXCLUDED.trip_headsign,
            direction_id = EXCLUDED.direction_id,
            shape_id = EXCLUDED.shape_id
    """

    execute_batches(
        connection,
        statement,
        rows,
    )


def print_counts(connection):
    print("\nDATABASE ROW COUNTS")
    print("-------------------")

    tables = [
        "gtfs_routes",
        "gtfs_stops",
        "gtfs_trips",
    ]

    for table in tables:
        count = connection.execute(
            text(f"SELECT COUNT(*) FROM {table}")
        ).scalar()

        print(f"{table}: {count:,}")


def main():
    print("GTFS CORE DATABASE LOAD")
    print("-----------------------")

    with engine.begin() as connection:
        load_routes(connection)
        load_stops(connection)
        load_trips(connection)

        print_counts(connection)

    print("\nGTFS CORE LOAD COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()