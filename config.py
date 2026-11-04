import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "9289282529:AAGjNjOlA1rXrGofD_bsoaiEsGv78Q6EX8M").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "1438313297"))
CARD_NUMBER = os.getenv("CARD_NUMBER", "9860 1606 3439 0605").strip()
CARD_HOLDER = os.getenv("CARD_HOLDER", "K.E.").strip()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "Kubayev_E").strip()
PORT = int(os.getenv("PORT", "8080"))
WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip()

DB_PATH = BASE_DIR / "prava_database.db"
QUESTIONS_FILE = BASE_DIR / "data" / "questions.json"

# Biletlar paketlari
PACKAGES = {
    "pack_4_6": {
        "title": "4–6 biletlar (60 ta savol)",
        "from_ticket": 4,
        "to_ticket": 6,
        "price": 5000,
        "price_str": "5 000 so'm",
        "duration_days": 90
    },
    "pack_7_10": {
        "title": "7–10 biletlar (80 ta savol)",
        "from_ticket": 7,
        "to_ticket": 10,
        "price": 10000,
        "price_str": "10 000 so'm",
        "duration_days": 90
    },
    "pack_11_14": {
        "title": "11–14 biletlar (80 ta savol)",
        "from_ticket": 11,
        "to_ticket": 14,
        "price": 10000,
        "price_str": "10 000 so'm",
        "duration_days": 90
    },
    "pack_15_18": {
        "title": "15–18 biletlar (80 ta savol)",
        "from_ticket": 15,
        "to_ticket": 18,
        "price": 10000,
        "price_str": "10 000 so'm",
        "duration_days": 90
    },
    "pack_19_22": {
        "title": "19–22 biletlar (80 ta savol)",
        "from_ticket": 19,
        "to_ticket": 22,
        "price": 10000,
        "price_str": "10 000 so'm",
        "duration_days": 90
    }
}
