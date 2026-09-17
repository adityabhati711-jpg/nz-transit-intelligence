import csv
from pathlib import Path

import psycopg

from src.config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
)


BASE_DIR = Path(__file__).resolve().parent.parent.parent
STOP_TIMES_FILE = (
    BASE_DIR
    / "data"
    / "static"
    / "latest"
    / "stop_times.txt"
)


def to_int(value):
    if value is None or value == "":
        return None

    return int(value)


def to_float(value):
    if value is None or value == "":
        return None

    return float(value)


def load_stop_times():
    print("Loading GTFS stop_times...")
    print("This file contains about 1.5 million rows.")

    connection = psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                "TRUNCATE TABLE gtfs_stop_times"
            )

            copy_sql = """
                COPY gtfs_stop_times (
                    trip_id,
                    arrival_time,
                    departure_time,
                    stop_id,
                    stop_sequence,
                    stop_headsign,
                    pickup_type,
                    drop_off_type,
                    shape_dist_traveled,
                    timepoint
                )
                FROM STDIN
            """

            row_count = 0

            with open(
                STOP_TIMES_FILE,
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as file:

                reader = csv.DictReader(file)

                with cursor.copy(copy_sql) as copy:

                    for row in reader:

                        copy.write_row(
                            (
                                row.get("trip_id"),
                                row.get("arrival_time") or None,
                                row.get("departure_time") or None,
                                row.get("stop_id") or None,
                                to_int(
                                    row.get("stop_sequence")
                                ),
                                row.get("stop_headsign") or None,
                                to_int(
                                    row.get("pickup_type")
                                ),
                                to_int(
                                    row.get("drop_off_type")
                                ),
                                to_float(
                                    row.get(
                                        "shape_dist_traveled"
                                    )
                                ),
                                to_int(
                                    row.get("timepoint")
                                ),
                            )
                        )

                        row_count += 1

                        if row_count % 250000 == 0:
                            print(
                                f"{row_count:,} rows loaded..."
                            )

        connection.commit()

        print("\nSTOP TIMES LOAD SUCCESSFUL")
        print("--------------------------")
        print(
            f"Rows loaded: {row_count:,}"
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    load_stop_times()