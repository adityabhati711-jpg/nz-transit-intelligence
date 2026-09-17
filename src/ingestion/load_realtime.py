import hashlib
import json
from pathlib import Path

from sqlalchemy import text

from src.database import engine


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    .parent
)

RAW_DIR = BASE_DIR / "data" / "raw"

BATCH_SIZE = 2000


def make_key(*parts):
    value = "|".join(
        str(part)
        for part in parts
    )

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def get_feed(data):
    return data.get(
        "response",
        data,
    )


def get_entities(feed):
    entities = feed.get(
        "entity",
        [],
    )

    if isinstance(entities, dict):
        return [entities]

    if not isinstance(entities, list):
        return []

    return entities


def get_feed_timestamp(feed):
    header = feed.get(
        "header",
        {},
    )

    if not isinstance(header, dict):
        return None

    return header.get(
        "timestamp"
    )


def get_translation_text(value):
    if not isinstance(value, dict):
        return None

    translations = value.get(
        "translation",
        [],
    )

    if isinstance(translations, dict):
        translations = [translations]

    if not isinstance(translations, list):
        return None

    for translation in translations:

        if not isinstance(
            translation,
            dict,
        ):
            continue

        text_value = translation.get(
            "text"
        )

        if text_value:
            return text_value

    return None


def execute_batches(
    connection,
    statement,
    rows,
):
    if not rows:
        return

    for start in range(
        0,
        len(rows),
        BATCH_SIZE,
    ):
        batch = rows[
            start:
            start + BATCH_SIZE
        ]

        connection.execute(
            text(statement),
            batch,
        )


# =========================================================
# TRIP UPDATES
# =========================================================

def parse_trip_update_file(
    file_path
):
    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    feed = get_feed(data)

    feed_timestamp = (
        get_feed_timestamp(feed)
    )

    entities = get_entities(feed)

    rows = []

    for entity in entities:

        if not isinstance(
            entity,
            dict,
        ):
            continue

        entity_id = entity.get(
            "id"
        )

        trip_update = entity.get(
            "trip_update",
            {},
        )

        if not isinstance(
            trip_update,
            dict,
        ):
            continue

        trip = trip_update.get(
            "trip",
            {},
        )

        if not isinstance(
            trip,
            dict,
        ):
            trip = {}

        trip_id = trip.get(
            "trip_id"
        )

        route_id = trip.get(
            "route_id"
        )

        direction_id = trip.get(
            "direction_id"
        )

        start_date = trip.get(
            "start_date"
        )

        schedule_relationship = (
            trip.get(
                "schedule_relationship"
            )
        )

        vehicle = trip_update.get(
            "vehicle",
            {},
        )

        if not isinstance(
            vehicle,
            dict,
        ):
            vehicle = {}

        vehicle_id = (
            vehicle.get("id")
            or vehicle.get(
                "vehicle_id"
            )
        )

        stop_updates = (
            trip_update.get(
                "stop_time_update",
                [],
            )
        )

        if isinstance(
            stop_updates,
            dict,
        ):
            stop_updates = [
                stop_updates
            ]

        if not isinstance(
            stop_updates,
            list,
        ):
            stop_updates = []

        if not stop_updates:

            record_key = make_key(
                file_path.name,
                entity_id,
                trip_id,
                "no_stop"
            )

            rows.append({
                "record_key":
                    record_key,

                "source_file":
                    file_path.name,

                "entity_id":
                    entity_id,

                "feed_timestamp":
                    feed_timestamp,

                "trip_id":
                    trip_id,

                "route_id":
                    route_id,

                "direction_id":
                    direction_id,

                "start_date":
                    start_date,

                "vehicle_id":
                    vehicle_id,

                "stop_id":
                    None,

                "stop_sequence":
                    None,

                "arrival_delay":
                    None,

                "arrival_time":
                    None,

                "departure_delay":
                    None,

                "departure_time":
                    None,

                "schedule_relationship":
                    schedule_relationship,

                "raw_json":
                    json.dumps(
                        entity
                    ),
            })

            continue

        for index, stop_update in enumerate(
            stop_updates
        ):

            if not isinstance(
                stop_update,
                dict,
            ):
                continue

            arrival = (
                stop_update.get(
                    "arrival",
                    {},
                )
            )

            departure = (
                stop_update.get(
                    "departure",
                    {},
                )
            )

            if not isinstance(
                arrival,
                dict,
            ):
                arrival = {}

            if not isinstance(
                departure,
                dict,
            ):
                departure = {}

            stop_sequence = (
                stop_update.get(
                    "stop_sequence"
                )
            )

            stop_id = (
                stop_update.get(
                    "stop_id"
                )
            )

            record_key = make_key(
                file_path.name,
                entity_id,
                trip_id,
                stop_sequence,
                stop_id,
                index,
            )

            rows.append({

                "record_key":
                    record_key,

                "source_file":
                    file_path.name,

                "entity_id":
                    entity_id,

                "feed_timestamp":
                    feed_timestamp,

                "trip_id":
                    trip_id,

                "route_id":
                    route_id,

                "direction_id":
                    direction_id,

                "start_date":
                    start_date,

                "vehicle_id":
                    vehicle_id,

                "stop_id":
                    stop_id,

                "stop_sequence":
                    stop_sequence,

                "arrival_delay":
                    arrival.get(
                        "delay"
                    ),

                "arrival_time":
                    arrival.get(
                        "time"
                    ),

                "departure_delay":
                    departure.get(
                        "delay"
                    ),

                "departure_time":
                    departure.get(
                        "time"
                    ),

                "schedule_relationship":
                    stop_update.get(
                        "schedule_relationship"
                    )
                    or schedule_relationship,

                "raw_json":
                    json.dumps(
                        entity
                    ),
            })

    return rows


# =========================================================
# VEHICLE POSITIONS
# =========================================================

def parse_vehicle_file(
    file_path
):
    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    feed = get_feed(data)

    feed_timestamp = (
        get_feed_timestamp(feed)
    )

    entities = get_entities(feed)

    rows = []

    for entity in entities:

        if not isinstance(
            entity,
            dict,
        ):
            continue

        vehicle = entity.get(
            "vehicle",
            {},
        )

        if not isinstance(
            vehicle,
            dict,
        ):
            continue

        entity_id = entity.get(
            "id"
        )

        trip = vehicle.get(
            "trip",
            {},
        )

        if not isinstance(
            trip,
            dict,
        ):
            trip = {}

        vehicle_info = (
            vehicle.get(
                "vehicle",
                {},
            )
        )

        if not isinstance(
            vehicle_info,
            dict,
        ):
            vehicle_info = {}

        position = vehicle.get(
            "position",
            {},
        )

        if not isinstance(
            position,
            dict,
        ):
            position = {}

        trip_id = trip.get(
            "trip_id"
        )

        route_id = trip.get(
            "route_id"
        )

        vehicle_id = (
            vehicle_info.get("id")
            or vehicle_info.get(
                "vehicle_id"
            )
        )

        event_timestamp = (
            vehicle.get(
                "timestamp"
            )
        )

        record_key = make_key(
            file_path.name,
            entity_id,
            vehicle_id,
            event_timestamp,
        )

        rows.append({

            "record_key":
                record_key,

            "source_file":
                file_path.name,

            "entity_id":
                entity_id,

            "feed_timestamp":
                feed_timestamp,

            "trip_id":
                trip_id,

            "route_id":
                route_id,

            "vehicle_id":
                vehicle_id,

            "latitude":
                position.get(
                    "latitude"
                ),

            "longitude":
                position.get(
                    "longitude"
                ),

            "bearing":
                position.get(
                    "bearing"
                ),

            "speed":
                position.get(
                    "speed"
                ),

            "current_stop_sequence":
                vehicle.get(
                    "current_stop_sequence"
                ),

            "stop_id":
                vehicle.get(
                    "stop_id"
                ),

            "current_status":
                vehicle.get(
                    "current_status"
                ),

            "event_timestamp":
                event_timestamp,

            "raw_json":
                json.dumps(
                    entity
                ),
        })

    return rows


# =========================================================
# SERVICE ALERTS
# =========================================================

def parse_alert_file(
    file_path
):
    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    feed = get_feed(data)

    feed_timestamp = (
        get_feed_timestamp(feed)
    )

    entities = get_entities(feed)

    rows = []

    for entity in entities:

        if not isinstance(
            entity,
            dict,
        ):
            continue

        alert = entity.get(
            "alert",
            {},
        )

        if not isinstance(
            alert,
            dict,
        ):
            continue

        entity_id = entity.get(
            "id"
        )

        active_periods = alert.get(
            "active_period",
            [],
        )

        if isinstance(
            active_periods,
            dict,
        ):
            active_periods = [
                active_periods
            ]

        active_start = None
        active_end = None

        if (
            isinstance(
                active_periods,
                list,
            )
            and active_periods
        ):
            first_period = (
                active_periods[0]
            )

            if isinstance(
                first_period,
                dict,
            ):
                active_start = (
                    first_period.get(
                        "start"
                    )
                )

                active_end = (
                    first_period.get(
                        "end"
                    )
                )

        record_key = make_key(
            file_path.name,
            entity_id,
        )

        rows.append({

            "record_key":
                record_key,

            "source_file":
                file_path.name,

            "entity_id":
                entity_id,

            "feed_timestamp":
                feed_timestamp,

            "cause":
                alert.get(
                    "cause"
                ),

            "effect":
                alert.get(
                    "effect"
                ),

            "active_start":
                active_start,

            "active_end":
                active_end,

            "header_text":
                get_translation_text(
                    alert.get(
                        "header_text"
                    )
                ),

            "description_text":
                get_translation_text(
                    alert.get(
                        "description_text"
                    )
                ),

            "raw_json":
                json.dumps(
                    entity
                ),
        })

    return rows


# =========================================================
# DATABASE LOADERS
# =========================================================

TRIP_INSERT = """
INSERT INTO realtime_trip_updates (
    record_key,
    source_file,
    entity_id,
    feed_timestamp,
    trip_id,
    route_id,
    direction_id,
    start_date,
    vehicle_id,
    stop_id,
    stop_sequence,
    arrival_delay,
    arrival_time,
    departure_delay,
    departure_time,
    schedule_relationship,
    raw_json
)
VALUES (
    :record_key,
    :source_file,
    :entity_id,
    :feed_timestamp,
    :trip_id,
    :route_id,
    :direction_id,
    :start_date,
    :vehicle_id,
    :stop_id,
    :stop_sequence,
    :arrival_delay,
    :arrival_time,
    :departure_delay,
    :departure_time,
    :schedule_relationship,
    CAST(:raw_json AS JSONB)
)
ON CONFLICT (record_key)
DO NOTHING
"""


VEHICLE_INSERT = """
INSERT INTO realtime_vehicle_positions (
    record_key,
    source_file,
    entity_id,
    feed_timestamp,
    trip_id,
    route_id,
    vehicle_id,
    latitude,
    longitude,
    bearing,
    speed,
    current_stop_sequence,
    stop_id,
    current_status,
    event_timestamp,
    raw_json
)
VALUES (
    :record_key,
    :source_file,
    :entity_id,
    :feed_timestamp,
    :trip_id,
    :route_id,
    :vehicle_id,
    :latitude,
    :longitude,
    :bearing,
    :speed,
    :current_stop_sequence,
    :stop_id,
    :current_status,
    :event_timestamp,
    CAST(:raw_json AS JSONB)
)
ON CONFLICT (record_key)
DO NOTHING
"""


ALERT_INSERT = """
INSERT INTO realtime_service_alerts (
    record_key,
    source_file,
    entity_id,
    feed_timestamp,
    cause,
    effect,
    active_start,
    active_end,
    header_text,
    description_text,
    raw_json
)
VALUES (
    :record_key,
    :source_file,
    :entity_id,
    :feed_timestamp,
    :cause,
    :effect,
    :active_start,
    :active_end,
    :header_text,
    :description_text,
    CAST(:raw_json AS JSONB)
)
ON CONFLICT (record_key)
DO NOTHING
"""


def load_realtime():
    trip_files = sorted(
        RAW_DIR.glob(
            "tripupdates_*.json"
        )
    )

    vehicle_files = sorted(
        RAW_DIR.glob(
            "vehiclepositions_*.json"
        )
    )

    alert_files = sorted(
        RAW_DIR.glob(
            "servicealerts_*.json"
        )
    )

    print(
        "REALTIME DATABASE LOAD"
    )

    print(
        "----------------------"
    )

    print(
        "Trip update files:",
        len(trip_files),
    )

    print(
        "Vehicle files:",
        len(vehicle_files),
    )

    print(
        "Alert files:",
        len(alert_files),
    )

    with engine.begin() as connection:

        for file_path in trip_files:

            rows = (
                parse_trip_update_file(
                    file_path
                )
            )

            execute_batches(
                connection,
                TRIP_INSERT,
                rows,
            )

        for file_path in vehicle_files:

            rows = (
                parse_vehicle_file(
                    file_path
                )
            )

            execute_batches(
                connection,
                VEHICLE_INSERT,
                rows,
            )

        for file_path in alert_files:

            rows = (
                parse_alert_file(
                    file_path
                )
            )

            execute_batches(
                connection,
                ALERT_INSERT,
                rows,
            )

        print(
            "\nDATABASE COUNTS"
        )

        print(
            "---------------"
        )

        tables = [
            "realtime_trip_updates",
            "realtime_vehicle_positions",
            "realtime_service_alerts",
        ]

        for table in tables:

            count = connection.execute(
                text(
                    f"""
                    SELECT COUNT(*)
                    FROM {table}
                    """
                )
            ).scalar()

            print(
                f"{table}: "
                f"{count:,}"
            )

    print(
        "\nREALTIME LOAD COMPLETED SUCCESSFULLY"
    )


if __name__ == "__main__":
    load_realtime()