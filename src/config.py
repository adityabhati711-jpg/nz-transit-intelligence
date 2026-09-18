from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env", override=False)


# -----------------------------
# Auckland Transport API
# -----------------------------

AT_API_KEY = os.getenv("AT_API_KEY")

if not AT_API_KEY:
    raise RuntimeError(
        "AT_API_KEY was not found. Please add it to your .env file."
    )

AT_HEADERS = {
    "Ocp-Apim-Subscription-Key": AT_API_KEY,
    "Accept": "application/json",
}


# -----------------------------
# PostgreSQL Database
# -----------------------------

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "nz_transit")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")

if not DB_PASSWORD:
    raise RuntimeError(
        "DB_PASSWORD was not found. Please add it to your .env file."
    )