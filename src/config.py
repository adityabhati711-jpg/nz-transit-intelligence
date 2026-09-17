from pathlib import Path
import os

from dotenv import load_dotenv


# Project root folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Load variables from .env
load_dotenv(BASE_DIR / ".env")

# Auckland Transport API key
AT_API_KEY = os.getenv("AT_API_KEY")

# Safety check
if not AT_API_KEY:
    raise RuntimeError(
        "AT_API_KEY was not found. Please add it to your .env file."
    )

# Headers required by Auckland Transport API
AT_HEADERS = {
    "Ocp-Apim-Subscription-Key": AT_API_KEY,
    "Accept": "application/json",
}