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
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://prava-test-bot.onrender.com").strip()

DB_PATH = BASE_DIR / "prava_database.db"
QUESTIONS_FILE = BASE_DIR / "data" / "questions_1200.json"

# VIP Tarif (90 kunlik to'liq kirish huquqi)
VIP_PRICE = 30000
VIP_PRICE_STR = "30 000 so'm"
VIP_DURATION_DAYS = 90

# Bepul biletlar
FREE_TICKETS = [1, 2, 3]
