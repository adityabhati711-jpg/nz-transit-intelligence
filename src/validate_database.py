from sqlalchemy import text

from src.database import engine


CHECKS = {
    "GTFS routes": "SELECT COUNT(*) FROM gtfs_routes",
    "GTFS stops": "SELECT COUNT(*) FROM gtfs_stops",
    "GTFS trips": "SELECT COUNT(*) FROM gtfs_trips",
    "GTFS stop times": "SELECT COUNT(*) FROM gtfs_stop_times",
    "Realtime trip updates": """
        SELECT COUNT(*)
        FROM realtime_trip_updates
    """,
    "Realtime vehicle positions": """
        SELECT COUNT(*)
        FROM realtime_vehicle_positions
    """,
    "Realtime service alerts": """
        SELECT COUNT(*)
        FROM realtime_service_alerts
    """,
}


def main():
    print("NZ TRANSIT DATABASE VALIDATION")
    print("------------------------------")

    with engine.connect() as connection:

        for name, query in CHECKS.items():
            count = connection.execute(
                text(query)
            ).scalar()

            print(
                f"{name}: {count:,}"
            )

        duplicate_trip_updates = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM (
                    SELECT record_key
                    FROM realtime_trip_updates
                    GROUP BY record_key
                    HAVING COUNT(*) > 1
                ) duplicates
            """)
        ).scalar()

        duplicate_vehicles = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM (
                    SELECT record_key
                    FROM realtime_vehicle_positions
                    GROUP BY record_key
                    HAVING COUNT(*) > 1
                ) duplicates
            """)
        ).scalar()

        duplicate_alerts = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM (
                    SELECT record_key
                    FROM realtime_service_alerts
                    GROUP BY record_key
                    HAVING COUNT(*) > 1
                ) duplicates
            """)
        ).scalar()

        print("\nDUPLICATE CHECK")
        print("---------------")

        print(
            "Trip update duplicate keys:",
            duplicate_trip_updates,
        )

        print(
            "Vehicle duplicate keys:",
            duplicate_vehicles,
        )

        print(
            "Alert duplicate keys:",
            duplicate_alerts,
        )

        null_stop_coordinates = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM gtfs_stops
                WHERE stop_lat IS NULL
                   OR stop_lon IS NULL
            """)
        ).scalar()

        print("\nQUALITY CHECK")
        print("-------------")

        print(
            "Stops missing coordinates:",
            null_stop_coordinates,
        )

    print(
        "\nDATABASE VALIDATION COMPLETED"
    )


if __name__ == "__main__":
    main()