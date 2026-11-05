import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "1438313297"))
CARD_NUMBER = os.getenv("CARD_NUMBER", "9860 1606 3439 0605").strip()
CARD_HOLDER = os.getenv("CARD_HOLDER", "K.E.").strip()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "Kubayev_E").strip()
PORT = int(os.getenv("PORT", "8080"))
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://prava-test-bot.onrender.com").strip()

DB_PATH = BASE_DIR / "prava_database.db"
QUESTIONS_FILE = BASE_DIR / "data" / "questions_1200.json"

# Tariflar narxlari
PRICE_3_TICKETS = 5000       # 3 ta ixtiyoriy bilet (90 kun)
PRICE_3_TICKETS_STR = "5 000 so'm"

PRICE_EXAM_1 = 2000          # 1 martalik 20 talik imtihon
PRICE_EXAM_1_STR = "2 000 so'm"

PRICE_EXAM_30 = 15000        # 30 kunlik cheksiz imtihon
PRICE_EXAM_30_STR = "15 000 so'm"

PRICE_VIP_90 = 30000         # VIP To'liq obuna (90 kun barcha biletlar + cheksiz imtihon)
PRICE_VIP_90_STR = "30 000 so'm"

FREE_TICKETS = [1, 2, 3]
TOTAL_TICKETS = 34
