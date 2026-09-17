import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import AT_HEADERS


BASE_URL = "https://api.at.govt.nz/realtime/legacy"

TRIP_UPDATES_URL = f"{BASE_URL}/tripupdates"
VEHICLE_POSITIONS_URL = f"{BASE_URL}/vehiclelocations"
ALERTS_URL = f"{BASE_URL}/servicealerts"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    reraise=True,
)
def fetch_trip_updates():
    response = requests.get(
        TRIP_UPDATES_URL,
        headers=AT_HEADERS,
        timeout=20,
    )

    response.raise_for_status()
    return response.json()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    reraise=True,
)
def fetch_vehicle_positions():
    response = requests.get(
        VEHICLE_POSITIONS_URL,
        headers=AT_HEADERS,
        timeout=20,
    )

    response.raise_for_status()
    return response.json()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    reraise=True,
)
def fetch_service_alerts():
    response = requests.get(
        ALERTS_URL,
        headers=AT_HEADERS,
        timeout=20,
    )

    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    trip_data = fetch_trip_updates()
    vehicle_data = fetch_vehicle_positions()
    alert_data = fetch_service_alerts()

    trip_feed = trip_data.get("response", trip_data)
    vehicle_feed = vehicle_data.get("response", vehicle_data)
    alert_feed = alert_data.get("response", alert_data)

    trip_entities = trip_feed.get("entity", [])
    vehicle_entities = vehicle_feed.get("entity", [])
    alert_entities = alert_feed.get("entity", [])

    print("AUCKLAND TRANSPORT LIVE API TEST")
    print("--------------------------------")
    print("Trip updates:", len(trip_entities))
    print("Vehicle positions:", len(vehicle_entities))
    print("Service alerts:", len(alert_entities))