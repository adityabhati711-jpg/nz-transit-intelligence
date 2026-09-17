from sqlalchemy import text

from src.database import engine


SCHEMA_STATEMENTS = [

    # =========================================================
    # GTFS STATIC TABLES
    # =========================================================

    """
    CREATE TABLE IF NOT EXISTS gtfs_routes (
        route_id TEXT PRIMARY KEY,
        agency_id TEXT,
        route_short_name TEXT,
        route_long_name TEXT,
        route_type INTEGER,
        route_color TEXT,
        route_text_color TEXT
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS gtfs_stops (
        stop_id TEXT PRIMARY KEY,
        stop_name TEXT,
        stop_lat DOUBLE PRECISION,
        stop_lon DOUBLE PRECISION,
        location_type INTEGER,
        parent_station TEXT
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS gtfs_trips (
        trip_id TEXT PRIMARY KEY,
        route_id TEXT,
        service_id TEXT,
        trip_headsign TEXT,
        direction_id INTEGER,
        shape_id TEXT
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS gtfs_stop_times (
        trip_id TEXT NOT NULL,
        arrival_time TEXT,
        departure_time TEXT,
        stop_id TEXT,
        stop_sequence INTEGER NOT NULL,
        stop_headsign TEXT,
        pickup_type INTEGER,
        drop_off_type INTEGER,
        shape_dist_traveled DOUBLE PRECISION,
        timepoint INTEGER,
        PRIMARY KEY (trip_id, stop_sequence)
    )
    """,

    # =========================================================
    # REALTIME TRIP UPDATES
    # =========================================================

    """
    CREATE TABLE IF NOT EXISTS realtime_trip_updates (
        record_key TEXT PRIMARY KEY,
        source_file TEXT NOT NULL,
        entity_id TEXT,
        feed_timestamp BIGINT,

        trip_id TEXT,
        route_id TEXT,
        direction_id INTEGER,
        start_date TEXT,

        vehicle_id TEXT,

        stop_id TEXT,
        stop_sequence INTEGER,

        arrival_delay INTEGER,
        arrival_time BIGINT,

        departure_delay INTEGER,
        departure_time BIGINT,

        schedule_relationship TEXT,

        raw_json JSONB,

        created_at TIMESTAMPTZ
            DEFAULT CURRENT_TIMESTAMP
    )
    """,

    # =========================================================
    # REALTIME VEHICLE POSITIONS
    # =========================================================

    """
    CREATE TABLE IF NOT EXISTS realtime_vehicle_positions (
        record_key TEXT PRIMARY KEY,
        source_file TEXT NOT NULL,
        entity_id TEXT,
        feed_timestamp BIGINT,

        trip_id TEXT,
        route_id TEXT,

        vehicle_id TEXT,

        latitude DOUBLE PRECISION,
        longitude DOUBLE PRECISION,
        bearing DOUBLE PRECISION,
        speed DOUBLE PRECISION,

        current_stop_sequence INTEGER,
        stop_id TEXT,
        current_status TEXT,

        event_timestamp BIGINT,

        raw_json JSONB,

        created_at TIMESTAMPTZ
            DEFAULT CURRENT_TIMESTAMP
    )
    """,

    # =========================================================
    # REALTIME SERVICE ALERTS
    # =========================================================

    """
    CREATE TABLE IF NOT EXISTS realtime_service_alerts (
        record_key TEXT PRIMARY KEY,
        source_file TEXT NOT NULL,
        entity_id TEXT,
        feed_timestamp BIGINT,

        cause TEXT,
        effect TEXT,

        active_start BIGINT,
        active_end BIGINT,

        header_text TEXT,
        description_text TEXT,

        raw_json JSONB,

        created_at TIMESTAMPTZ
            DEFAULT CURRENT_TIMESTAMP
    )
    """,

    # =========================================================
    # INDEXES
    # =========================================================

    """
    CREATE INDEX IF NOT EXISTS idx_gtfs_trips_route_id
    ON gtfs_trips(route_id)
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_gtfs_stops_parent_station
    ON gtfs_stops(parent_station)
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_gtfs_stop_times_stop_id
    ON gtfs_stop_times(stop_id)
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_gtfs_stop_times_trip_id
    ON gtfs_stop_times(trip_id)
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_rt_trip_updates_trip_id
    ON realtime_trip_updates(trip_id)
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_rt_trip_updates_route_id
    ON realtime_trip_updates(route_id)
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_rt_trip_updates_stop_id
    ON realtime_trip_updates(stop_id)
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_rt_vehicle_trip_id
    ON realtime_vehicle_positions(trip_id)
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_rt_vehicle_route_id
    ON realtime_vehicle_positions(route_id)
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_rt_vehicle_vehicle_id
    ON realtime_vehicle_positions(vehicle_id)
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_rt_vehicle_timestamp
    ON realtime_vehicle_positions(event_timestamp)
    """
]


def create_schema():
    print("Creating PostgreSQL schema...")

    with engine.begin() as connection:

        for statement in SCHEMA_STATEMENTS:
            connection.execute(
                text(statement)
            )

    print(
        "DATABASE SCHEMA CREATED SUCCESSFULLY"
    )


if __name__ == "__main__":
    create_schema()