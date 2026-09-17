from sqlalchemy import text

from src.database import engine


SQL_STATEMENTS = [

    # =========================================================
    # TIME FEATURES
    # =========================================================

    """
    CREATE OR REPLACE VIEW analytics.time_delay_features AS

    SELECT
        tdf.record_key,
        tdf.source_file,
        tdf.entity_id,

        tdf.trip_id,
        tdf.route_id,
        tdf.route_short_name,
        tdf.route_long_name,

        tdf.stop_id,
        tdf.stop_name,
        tdf.stop_sequence,

        tdf.feed_timestamp,
        tdf.event_time,

        tdf.arrival_delay,
        tdf.departure_delay,

        tdf.delay_seconds,
        tdf.delay_minutes,

        tdf.delay_category,
        tdf.is_delayed,

        tdf.vehicle_id,
        tdf.schedule_relationship,

        (
            tdf.event_time AT TIME ZONE 'Pacific/Auckland'
        )::date AS local_date,

        EXTRACT(
            HOUR FROM
            tdf.event_time AT TIME ZONE 'Pacific/Auckland'
        )::integer AS local_hour,

        TRIM(
            TO_CHAR(
                tdf.event_time AT TIME ZONE 'Pacific/Auckland',
                'Day'
            )
        ) AS day_name,

        EXTRACT(
            ISODOW FROM
            tdf.event_time AT TIME ZONE 'Pacific/Auckland'
        )::integer AS day_number,

        CASE

            WHEN EXTRACT(
                HOUR FROM
                tdf.event_time AT TIME ZONE 'Pacific/Auckland'
            ) BETWEEN 5 AND 9
                THEN 'Morning Peak'

            WHEN EXTRACT(
                HOUR FROM
                tdf.event_time AT TIME ZONE 'Pacific/Auckland'
            ) BETWEEN 10 AND 15
                THEN 'Midday'

            WHEN EXTRACT(
                HOUR FROM
                tdf.event_time AT TIME ZONE 'Pacific/Auckland'
            ) BETWEEN 16 AND 19
                THEN 'Evening Peak'

            ELSE
                'Off Peak'

        END AS time_period,

        tdf.direction_id

    FROM analytics.trip_delay_features tdf

    WHERE tdf.event_time IS NOT NULL
    """,

    # =========================================================
    # HOURLY PERFORMANCE
    # =========================================================

    """
    CREATE OR REPLACE VIEW analytics.hourly_performance AS

    SELECT
        local_hour,

        COUNT(*) AS observations,

        COUNT(delay_seconds)
            AS delay_observations,

        ROUND(
            AVG(delay_minutes)::numeric,
            2
        ) AS average_delay_minutes,

        ROUND(
            (
                100.0
                * COUNT(*) FILTER (
                    WHERE is_delayed = TRUE
                )
                / NULLIF(
                    COUNT(delay_seconds),
                    0
                )
            )::numeric,
            2
        ) AS delayed_percentage

    FROM analytics.time_delay_features

    GROUP BY local_hour

    ORDER BY local_hour
    """,

    # =========================================================
    # TIME PERIOD PERFORMANCE
    # =========================================================

    """
    CREATE OR REPLACE VIEW analytics.time_period_performance AS

    SELECT
        time_period,

        COUNT(*) AS observations,

        COUNT(delay_seconds)
            AS delay_observations,

        ROUND(
            AVG(delay_minutes)::numeric,
            2
        ) AS average_delay_minutes,

        ROUND(
            (
                100.0
                * COUNT(*) FILTER (
                    WHERE is_delayed = TRUE
                )
                / NULLIF(
                    COUNT(delay_seconds),
                    0
                )
            )::numeric,
            2
        ) AS delayed_percentage

    FROM analytics.time_delay_features

    GROUP BY time_period
    """,

    # =========================================================
    # ROUTE + HOUR PERFORMANCE
    # IMPORTANT:
    # Existing column structure preserved.
    # =========================================================

    """
    CREATE OR REPLACE VIEW analytics.route_hour_performance AS

    SELECT
        route_id,

        MAX(route_short_name)
            AS route_short_name,

        local_hour,

        COUNT(*)
            AS observations,

        ROUND(
            AVG(delay_minutes)::numeric,
            2
        ) AS average_delay_minutes,

        ROUND(
            (
                100.0
                * COUNT(*) FILTER (
                    WHERE is_delayed = TRUE
                )
                / NULLIF(
                    COUNT(delay_seconds),
                    0
                )
            )::numeric,
            2
        ) AS delayed_percentage

    FROM analytics.time_delay_features

    WHERE route_id IS NOT NULL

    GROUP BY
        route_id,
        local_hour
    """
]


def build_time_features():

    print("BUILDING TIME INTELLIGENCE")
    print("--------------------------")

    with engine.begin() as connection:

        for statement in SQL_STATEMENTS:
            connection.execute(
                text(statement)
            )

    print(
        "TIME INTELLIGENCE CREATED SUCCESSFULLY"
    )


def validate():

    print("\nTIME INTELLIGENCE VALIDATION")
    print("----------------------------")

    with engine.connect() as connection:

        total_records = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM analytics.time_delay_features
            """)
        ).scalar()

        direction_records = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM analytics.time_delay_features
                WHERE direction_id IS NOT NULL
            """)
        ).scalar()

        print(
            f"Time-feature records: {total_records:,}"
        )

        print(
            f"Records with direction ID: {direction_records:,}"
        )

        print("\nTIME PERIOD PERFORMANCE")
        print("-----------------------")

        rows = connection.execute(
            text("""
                SELECT
                    time_period,
                    observations,
                    average_delay_minutes,
                    delayed_percentage

                FROM analytics.time_period_performance

                ORDER BY observations DESC
            """)
        ).fetchall()

        for row in rows:

            print(
                f"{row.time_period}: "
                f"{row.observations:,} observations | "
                f"Avg delay {row.average_delay_minutes} min | "
                f"Delayed {row.delayed_percentage}%"
            )


def main():

    build_time_features()
    validate()


if __name__ == "__main__":
    main()