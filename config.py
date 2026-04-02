from dotenv import load_dotenv
import os

load_dotenv()

# ─── Telegram ─────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не задан")

# ─── Админы ───────────────────────────────
ADMIN_IDS = [
    int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
]

# ─── Лимиты ───────────────────────────────────────────
RATE_LIMIT_PER_MINUTE = 5
MAX_MESSAGE_LENGTH = 4000

# ─── База данных ──────────────────────────────────────
DATABASE_PATH = "osint_bot.db"

# ─── PhoneInfoga ──────────────────────────────────────
PHONEINFOGA_PATH = os.getenv("PHONEINFOGA_PATH", "phoneinfoga")

# ─── Админы ───────────────────────────────────────────
ADMIN_IDS = [
    int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
]

# ─── Бесплатные запросы ───────────────────────────────
FREE_SEARCHES_TOTAL = 4          # всего бесплатных на аккаунт
PREMIUM_SEARCHES_PER_DAY = 100   # для premium юзеров

# ─── Оплата (Telegram Stars) ─────────────────────────
# Пакеты: (количество запросов, цена в Stars)
PAYMENT_PACKAGES = {
    "pack_10":  {"searches": 10,  "stars": 50,   "label": "10 запросов"},
    "pack_50":  {"searches": 50,  "stars": 200,  "label": "50 запросов"},
    "pack_100": {"searches": 100, "stars": 350,  "label": "100 запросов"},
    "pack_unlimited": {"searches": 999999, "stars": 500, "label": "Безлимит (30 дней)"},
}