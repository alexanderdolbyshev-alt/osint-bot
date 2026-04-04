from dotenv import load_dotenv
import os

load_dotenv()

# ─────────────────────────────────────────
# TELEGRAM BOT
# ─────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не задан")


# ─────────────────────────────────────────
# TELEGRAM API (для OSINT через Telethon)
# ─────────────────────────────────────────
TG_API_ID = os.getenv("TG_API_ID")
TG_API_HASH = os.getenv("TG_API_HASH")

if not TG_API_ID or not TG_API_HASH:
    print("⚠️ TG_API_ID или TG_API_HASH не заданы (Telegram OSINT работать не будет)")


# ─────────────────────────────────────────
# AI (OpenRouter / OpenAI)
# ─────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("⚠️ OPENROUTER_API_KEY не задан (AI профиль отключён)")


# ─────────────────────────────────────────
# АДМИНЫ
# ─────────────────────────────────────────
ADMIN_IDS = [
    int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
]


# ─────────────────────────────────────────
# ЛИМИТЫ
# ─────────────────────────────────────────
RATE_LIMIT_PER_MINUTE = 5
MAX_MESSAGE_LENGTH = 4000


# ─────────────────────────────────────────
# БАЗА ДАННЫХ
# ─────────────────────────────────────────
DATABASE_PATH = "osint_bot.db"


# ─────────────────────────────────────────
# PHONEINFOGA
# ─────────────────────────────────────────
PHONEINFOGA_PATH = os.getenv("PHONEINFOGA_PATH", "phoneinfoga")


# ─────────────────────────────────────────
# ЛИМИТЫ ПОЛЬЗОВАТЕЛЕЙ
# ─────────────────────────────────────────
FREE_SEARCHES_TOTAL = 2
PREMIUM_SEARCHES_PER_DAY = 100


# ─────────────────────────────────────────
# ОПЛАТА (Telegram Stars)
# ─────────────────────────────────────────
PAYMENT_PACKAGES = {
    "pack_test": {
        "searches": 1,
        "stars": 1,
        "label": "Тест (1 запрос)"
    },
    "pack_10": {
        "searches": 10,
        "stars": 50,
        "label": "10 запросов"
    },
    "pack_50": {
        "searches": 50,
        "stars": 200,
        "label": "50 запросов"
    },
    "pack_100": {
        "searches": 100,
        "stars": 350,
        "label": "100 запросов"
    },
    "pack_unlimited": {
        "searches": 999999,
        "stars": 500,
        "label": "Безлимит (30 дней)"
    },
}


# ─────────────────────────────────────────
# ДОПОЛНИТЕЛЬНО (PRO настройки)
# ─────────────────────────────────────────

# включить AI профиль
ENABLE_AI = True

# включить Telegram OSINT
ENABLE_TELEGRAM_OSINT = True

# включить проверку утечек
ENABLE_LEAK_CHECK = True

# логирование (очень полезно)
DEBUG = True
