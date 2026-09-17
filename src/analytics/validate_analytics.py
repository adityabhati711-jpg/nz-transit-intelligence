from sqlalchemy import text

from src.database import engine


def main():

    print("DAY 3 ANALYTICS VALIDATION")
    print("--------------------------")

    with engine.connect() as connection:

        trip_records = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM analytics.trip_delay_features
            """)
        ).scalar()

        time_records = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM analytics.time_delay_features
            """)
        ).scalar()

        ml_records = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM analytics.ml_delay_features
            """)
        ).scalar()

        delayed_records = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM analytics.ml_delay_features
                WHERE is_delayed = TRUE
            """)
        ).scalar()

        not_delayed_records = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM analytics.ml_delay_features
                WHERE is_delayed = FALSE
            """)
        ).scalar()

        duplicate_records = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM (
                    SELECT record_key
                    FROM analytics.ml_delay_features
                    GROUP BY record_key
                    HAVING COUNT(*) > 1
                ) duplicates
            """)
        ).scalar()

        missing_required = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM analytics.ml_delay_features
                WHERE route_id IS NULL
                   OR stop_id IS NULL
                   OR delay_seconds IS NULL
            """)
        ).scalar()

        routes = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM analytics.route_insights
            """)
        ).scalar()

        stops = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM analytics.stop_insights
            """)
        ).scalar()

        print(f"Trip delay records: {trip_records:,}")
        print(f"Time feature records: {time_records:,}")
        print(f"ML-ready records: {ml_records:,}")

        print("\nTARGET CHECK")
        print("------------")

        print(f"Delayed: {delayed_records:,}")
        print(f"Not delayed: {not_delayed_records:,}")

        print("\nQUALITY CHECK")
        print("-------------")

        print(f"Duplicate ML records: {duplicate_records}")
        print(f"Missing required values: {missing_required}")

        print("\nANALYTICS COVERAGE")
        print("------------------")

        print(f"Routes analysed: {routes:,}")
        print(f"Stops analysed: {stops:,}")

        if delayed_records + not_delayed_records != ml_records:
            raise RuntimeError(
                "Target counts do not match ML record count."
            )

        if duplicate_records != 0:
            raise RuntimeError(
                "Duplicate ML records detected."
            )

        if missing_required != 0:
            raise RuntimeError(
                "Missing required ML feature values detected."
            )

    print(
        "\nDAY 3 ANALYTICS VALIDATION PASSED"
    )


if __name__ == "__main__":
    main()