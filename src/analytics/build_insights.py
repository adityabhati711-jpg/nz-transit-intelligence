from sqlalchemy import text

from src.database import engine


SQL_STATEMENTS = [

    """
    CREATE OR REPLACE VIEW analytics.route_insights AS

    SELECT
        route_id,
        MAX(route_short_name) AS route_short_name,
        MAX(route_long_name) AS route_long_name,

        COUNT(*) AS observations,

        COUNT(delay_seconds)
            AS delay_observations,

        ROUND(
            AVG(delay_minutes)::numeric,
            2
        ) AS average_delay_minutes,

        ROUND(
            PERCENTILE_CONT(0.5)
            WITHIN GROUP (
                ORDER BY delay_minutes
            )::numeric,
            2
        ) AS median_delay_minutes,

        ROUND(
            MAX(delay_minutes)::numeric,
            2
        ) AS maximum_delay_minutes,

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

    FROM analytics.trip_delay_features

    WHERE route_id IS NOT NULL

    GROUP BY route_id
    """,

    """
    CREATE OR REPLACE VIEW analytics.stop_insights AS

    SELECT
        stop_id,
        MAX(stop_name) AS stop_name,

        COUNT(*) AS observations,

        COUNT(delay_seconds)
            AS delay_observations,

        ROUND(
            AVG(delay_minutes)::numeric,
            2
        ) AS average_delay_minutes,

        ROUND(
            MAX(delay_minutes)::numeric,
            2
        ) AS maximum_delay_minutes,

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

    FROM analytics.trip_delay_features

    WHERE stop_id IS NOT NULL

    GROUP BY stop_id
    """
]


def build_insights():

    print("BUILDING ROUTE AND STOP INSIGHTS")
    print("--------------------------------")

    with engine.begin() as connection:

        for statement in SQL_STATEMENTS:
            connection.execute(
                text(statement)
            )

    print(
        "ROUTE AND STOP INSIGHTS CREATED SUCCESSFULLY"
    )


def validate():

    with engine.connect() as connection:

        print("\nROUTES WITH HIGHEST DELAY RATE")
        print("------------------------------")

        routes = connection.execute(
            text("""
                SELECT
                    route_id,
                    route_short_name,
                    observations,
                    average_delay_minutes,
                    delayed_percentage

                FROM analytics.route_insights

                WHERE delay_observations >= 10

                ORDER BY delayed_percentage DESC

                LIMIT 10
            """)
        ).fetchall()

        for row in routes:

            print(
                f"Route {row.route_short_name or row.route_id}: "
                f"{row.observations} obs | "
                f"Avg {row.average_delay_minutes} min | "
                f"Delayed {row.delayed_percentage}%"
            )


        print("\nSTOPS WITH HIGHEST DELAY RATE")
        print("-----------------------------")

        stops = connection.execute(
            text("""
                SELECT
                    stop_id,
                    stop_name,
                    observations,
                    average_delay_minutes,
                    delayed_percentage

                FROM analytics.stop_insights

                WHERE delay_observations >= 10

                ORDER BY delayed_percentage DESC

                LIMIT 10
            """)
        ).fetchall()

        for row in stops:

            print(
                f"{row.stop_name or row.stop_id}: "
                f"{row.observations} obs | "
                f"Avg {row.average_delay_minutes} min | "
                f"Delayed {row.delayed_percentage}%"
            )


def main():
    build_insights()
    validate()


if __name__ == "__main__":
    main()