import csv
import shutil
import zipfile
from pathlib import Path

import requests


BASE_DIR = Path(__file__).resolve().parent.parent.parent

STATIC_DATA_DIR = BASE_DIR / "data" / "static"
EXTRACT_DIR = STATIC_DATA_DIR / "latest"
GTFS_ZIP_PATH = STATIC_DATA_DIR / "gtfs_latest.zip"

GTFS_URL = "https://gtfs.at.govt.nz/gtfs.zip"


def download_gtfs():
    """Download the latest Auckland Transport GTFS Static feed."""

    STATIC_DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("Downloading latest Auckland Transport GTFS data...")

    response = requests.get(
        GTFS_URL,
        timeout=120,
    )

    response.raise_for_status()

    with open(GTFS_ZIP_PATH, "wb") as file:
        file.write(response.content)

    print("GTFS download successful.")
    print("Saved ZIP to:", GTFS_ZIP_PATH)


def extract_gtfs():
    """Extract the downloaded GTFS ZIP file."""

    if EXTRACT_DIR.exists():
        shutil.rmtree(EXTRACT_DIR)

    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(GTFS_ZIP_PATH, "r") as zip_file:
        zip_file.extractall(EXTRACT_DIR)

    print("GTFS extraction successful.")
    print("Extracted to:", EXTRACT_DIR)


def count_rows(filename):
    """Count rows in a GTFS text/CSV file."""

    file_path = EXTRACT_DIR / filename

    if not file_path.exists():
        return 0

    with open(
        file_path,
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)
        return sum(1 for _ in reader)


def verify_gtfs():
    """Verify important GTFS files and display row counts."""

    required_files = [
        "routes.txt",
        "stops.txt",
        "trips.txt",
        "stop_times.txt",
    ]

    print("\nGTFS STATIC DATA SUMMARY")
    print("------------------------")

    for filename in required_files:
        file_path = EXTRACT_DIR / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"Required GTFS file missing: {filename}"
            )

        rows = count_rows(filename)

        print(f"{filename}: {rows:,} rows")


def main():
    download_gtfs()
    extract_gtfs()
    verify_gtfs()

    print("\nGTFS Static collection completed successfully.")


if __name__ == "__main__":
    main()