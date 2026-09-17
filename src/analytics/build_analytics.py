from sqlalchemy import text

from src.database import engine


SQL_STATEMENTS = [

    # =========================================================
    # ANALYTICS SCHEMA
    # =========================================================

    """
    CREATE SCHEMA IF NOT EXISTS analytics
    """,

    # =========================================================
    # TRIP / STOP DELAY FEATURE VIEW
    # =========================================================

    """
    CREATE OR REPLACE VIEW analytics.trip_delay_features AS

    SELECT
        rtu.record_key,
        rtu.source_file,
        rtu.entity_id,

        rtu.trip_id,

        COALESCE(
            gt.route_id,
            rtu.route_id
        ) AS route_id,

        gr.route_short_name,
        gr.route_long_name,

        rtu.stop_id,
        gs.stop_name,

        rtu.stop_sequence,

        rtu.feed_timestamp,

        TO_TIMESTAMP(
            COALESCE(
                rtu.departure_time,
                rtu.arrival_time,
                rtu.feed_timestamp
            )
        ) AS event_time,

        rtu.arrival_delay,
        rtu.departure_delay,

        COALESCE(
            rtu.departure_delay,
            rtu.arrival_delay
        ) AS delay_seconds,

        ROUND(
            (
                COALESCE(
                    rtu.departure_delay,
                    rtu.arrival_delay
                ) / 60.0
            )::numeric,
            2
        ) AS delay_minutes,

        CASE

            WHEN COALESCE(
                rtu.departure_delay,
                rtu.arrival_delay
            ) IS NULL
                THEN 'Unknown'

            WHEN COALESCE(
                rtu.departure_delay,
                rtu.arrival_delay
            ) < -60
                THEN 'Early'

            WHEN COALESCE(
                rtu.departure_delay,
                rtu.arrival_delay
            ) <= 300
                THEN 'On Time'

            WHEN COALESCE(
                rtu.departure_delay,
                rtu.arrival_delay
            ) <= 600
                THEN '5-10 min late'

            WHEN COALESCE(
                rtu.departure_delay,
                rtu.arrival_delay
            ) <= 1200
                THEN '10-20 min late'

            ELSE
                '20+ min late'

        END AS delay_category,

        CASE
            WHEN COALESCE(
                rtu.departure_delay,
                rtu.arrival_delay
            ) > 300
            THEN TRUE

            ELSE FALSE
        END AS is_delayed,

        rtu.vehicle_id,
        rtu.schedule_relationship,
        rtu.direction_id

    FROM realtime_trip_updates rtu

    LEFT JOIN gtfs_trips gt
        ON rtu.trip_id = gt.trip_id

    LEFT JOIN gtfs_routes gr
        ON COALESCE(
            gt.route_id,
            rtu.route_id
        ) = gr.route_id

    LEFT JOIN gtfs_stops gs
        ON rtu.stop_id = gs.stop_id
    """,

    # =========================================================
    # ROUTE PERFORMANCE VIEW
    # =========================================================

    """
    CREATE OR REPLACE VIEW analytics.route_performance AS

    SELECT

        route_id,

        MAX(route_short_name)
            AS route_short_name,

        MAX(route_long_name)
            AS route_long_name,

        COUNT(*)
            AS observations,

        COUNT(delay_seconds)
            AS delay_observations,

        ROUND(
            AVG(delay_seconds)::numeric,
            2
        ) AS average_delay_seconds,

        ROUND(
            (
                AVG(delay_seconds) / 60.0
            )::numeric,
            2
        ) AS average_delay_minutes,

        ROUND(
            PERCENTILE_CONT(0.5)
            WITHIN GROUP (
                ORDER BY delay_seconds
            )::numeric,
            2
        ) AS median_delay_seconds,

        ROUND(
            (
                100.0
                * COUNT(*) FILTER (
                    WHERE delay_seconds > 300
                )
                / NULLIF(
                    COUNT(delay_seconds),
                    0
                )
            )::numeric,
            2
        ) AS delayed_percentage,

        ROUND(
            (
                100.0
                * COUNT(*) FILTER (
                    WHERE delay_seconds
                    BETWEEN -60 AND 300
                )
                / NULLIF(
                    COUNT(delay_seconds),
                    0
                )
            )::numeric,
            2
        ) AS on_time_percentage

    FROM analytics.trip_delay_features

    WHERE route_id IS NOT NULL

    GROUP BY route_id
    """,

    # =========================================================
    # STOP PERFORMANCE VIEW
    # =========================================================

    """
    CREATE OR REPLACE VIEW analytics.stop_performance AS

    SELECT

        stop_id,

        MAX(stop_name)
            AS stop_name,

        COUNT(*)
            AS observations,

        COUNT(delay_seconds)
            AS delay_observations,

        ROUND(
            AVG(delay_seconds)::numeric,
            2
        ) AS average_delay_seconds,

        ROUND(
            (
                AVG(delay_seconds) / 60.0
            )::numeric,
            2
        ) AS average_delay_minutes,

        ROUND(
            (
                100.0
                * COUNT(*) FILTER (
                    WHERE delay_seconds > 300
                )
                / NULLIF(
                    COUNT(delay_seconds),
                    0
                )
            )::numeric,
            2
        ) AS delayed_percentage

    FROM analytics.trip_delay_features

    WHERE stop_id IS NOT NULL

    GROUP BY stop_id
    """
]


def build_analytics():
    print("BUILDING ANALYTICS LAYER")
    print("------------------------")

    with engine.begin() as connection:

        for statement in SQL_STATEMENTS:
            connection.execute(
                text(statement)
            )

    print(
        "ANALYTICS LAYER CREATED SUCCESSFULLY"
    )


def validate_analytics():
    print("\nANALYTICS VALIDATION")
    print("--------------------")

    with engine.connect() as connection:

        trip_count = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM analytics.trip_delay_features
            """)
        ).scalar()

        route_count = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM analytics.route_performance
            """)
        ).scalar()

        stop_count = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM analytics.stop_performance
            """)
        ).scalar()

        delayed_count = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM analytics.trip_delay_features
                WHERE is_delayed = TRUE
            """)
        ).scalar()

        print(
            f"Trip delay records: {trip_count:,}"
        )

        print(
            f"Routes analysed: {route_count:,}"
        )

        print(
            f"Stops analysed: {stop_count:,}"
        )

        print(
            f"Delayed observations: {delayed_count:,}"
        )


def main():
    build_analytics()
    validate_analytics()


if __name__ == "__main__":
    main()