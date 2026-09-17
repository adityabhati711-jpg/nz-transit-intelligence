import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import AT_HEADERS


BASE_URL = "https://api.at.govt.nz/realtime/legacy"

TRIP_UPDATES_URL = f"{BASE_URL}/tripupdates"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    reraise=True,
)
def fetch_trip_updates():
    """Fetch live Auckland Transport trip updates."""

    response = requests.get(
        TRIP_UPDATES_URL,
        headers=AT_HEADERS,
        timeout=20,
    )

    response.raise_for_status()

    return response.json()


if __name__ == "__main__":
    data = fetch_trip_updates()

    # Some AT responses wrap the GTFS feed inside "response".
    feed = data.get("response", data)

    header = feed.get("header", {})
    entities = feed.get("entity", [])

    print("LIVE AT REQUEST SUCCESSFUL")
    print("--------------------------")
    print("Feed timestamp:", header.get("timestamp"))
    print("Entities received:", len(entities))

    if entities:
        first_entity = entities[0]

        trip_update = first_entity.get("trip_update", {})
        trip = trip_update.get("trip", {})
        vehicle = trip_update.get("vehicle", {})

        print("\nSample live record")
        print("------------------")
        print("Trip ID:", trip.get("trip_id"))
        print("Route ID:", trip.get("route_id"))
        print("Vehicle ID:", vehicle.get("id"))