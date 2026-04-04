import re
import asyncio
import time
import os

from aiogram import Router
from aiogram.types import Message

from database import db
from config import FREE_SEARCHES_TOTAL
from utils.rate_limit import rate_limiter
from utils.formatter import (
    format_username_results,
    format_email_results,
    format_phone_results,
    format_error,
    split_message,
)

# ✅ ПРАВИЛЬНЫЙ ИМПОРТ
from keyboards.inline import (
    main_menu_keyboard,
    back_to_menu_keyboard,
    paywall_keyboard,
)

from modules.username_search import search_username
from modules.email_search import search_email
from modules.phone_search import (
    search_phone,
    basic_phone_info,
    search_phone_sources,
)
from modules.leak_check import check_leaks
from modules.ai_openrouter import analyze_username_ai
from modules.ai_phone import analyze_phone_ai
from utils.cache import get_cache, set_cache
from modules.telegram_osint import get_telegram_info

router = Router()

# ✅ АДМИНЫ
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "0").split(",")))

EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
PHONE_RE = re.compile(r"^\+?[0-9]{7,15}$")
USERNAME_RE = re.compile(r"^@?[a-zA-Z0-9_.-]{2,30}$")


# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════

@router.message()
async def handle_search(message: Message):
    text = message.text
    if not text or text.startswith("/"):
        return

    text = text.strip()
    user_id = message.from_user.id

    await db.ensure_user(
        user_id,
        message.from_user.username,
        message.from_user.first_name
    )

    # rate limit
    if not rate_limiter.is_allowed(user_id):
        wait = rate_limiter.seconds_until_reset(user_id)
        await message.answer(f"⏳ Подожди {wait} сек.")
        return

    # лимиты
    access = await db.can_search(user_id, FREE_SEARCHES_TOTAL)

    if user_id not in ADMIN_IDS:
        if not access["allowed"]:
            await message.answer(
                "🚫 Лимит исчерпан\n\nКупи доступ 👇",
                reply_markup=paywall_keyboard()
            )
            return

    clean = re.sub(r"[\s\-\(\)]", "", text)

    if EMAIL_RE.match(text):
        await _handle_email(message, text)

    elif PHONE_RE.match(clean):
        await _handle_phone(message, text)

    elif text.startswith("@"):
        await _handle_username(message, text.lstrip("@"))

    elif USERNAME_RE.match(text) and " " not in text:
        await _handle_username(message, text)

    else:
        await message.answer("❓ Не понял формат")


# ═══════════════════════════════════════════════════════
# USERNAME
# ═══════════════════════════════════════════════════════

async def _handle_username(message: Message, username: str):

    status = await message.answer("🔍 Запуск поиска...")

    start = time.time()

    try:
        search_task = asyncio.create_task(search_username(username))
        progress_task = asyncio.create_task(
            _animate_progress(status, f"@{username}")
        )

        found_sites, all_sites = await search_task
        progress_task.cancel()

        elapsed = time.time() - start

        found_sites = found_sites[:20]

        response = format_username_results(username, found_sites, all_sites)

        # AI
        try:
            analysis = await analyze_username_ai(username, found_sites)
        except:
            analysis = "❌ AI недоступен"

        response += "\n\n🧠 AI Анализ:\n" + analysis
        response += f"\n\n⏱ Время: {elapsed:.1f} сек."

        await _safe_send(
            status,
            response,
            reply_markup=main_menu_keyboard()  # ✅ фикс
        )

        await db.log_search(
            message.from_user.id, "username", username, len(found_sites)
        )

    except Exception as e:
        await _safe_send(status, format_error(str(e)))


# ═══════════════════════════════════════════════════════
# EMAIL
# ═══════════════════════════════════════════════════════

async def _handle_email(message: Message, email: str):

    status = await message.answer("📧 Проверка email...")

    start = time.time()

    try:
        results = await search_email(email)

        elapsed = time.time() - start

        response = format_email_results(email, results)
        response += f"\n\n⏱ Время: {elapsed:.1f} сек."

        await _safe_send(
            status,
            response,
            reply_markup=back_to_menu_keyboard()  # ✅ добавили
        )

    except Exception as e:
        await _safe_send(status, format_error(str(e)))


# ═══════════════════════════════════════════════════════
# PHONE
# ═══════════════════════════════════════════════════════

async def _handle_phone(message: Message, phone: str):

    status = await message.answer("📱 Анализ номера...")

    start = time.time()

    try:
        # ⚡ КЕШ
        cache_key = f"phone:{phone}"
        cached = get_cache(cache_key)

        if cached:
            await status.delete()
            await message.answer(
                "⚡ Найдено в кеше\n\n" + cached,
                reply_markup=back_to_menu_keyboard()
            )
            return

        # ⚡ ПАРАЛЛЕЛЬНО ВСЁ
        results, sources, leaks, tg = await asyncio.gather(
            search_phone(phone),
            search_phone_sources(phone),
            check_leaks(phone),
            get_telegram_info(phone)  # 🔥 ВОТ НОВОЕ
        )

        info = basic_phone_info(phone)

        # 🧠 AI
        try:
            ai = await analyze_phone_ai(phone, info, leaks, sources)
        except:
            ai = "❌ AI недоступен"

        elapsed = time.time() - start

        # 🎯 UI
        response = f"""
📱 **АНАЛИЗ НОМЕРА**
━━━━━━━━━━━━━━━━━━━
📞 `{phone}`

📊 **Основное**
✔️ Валидность: {"Да" if info["valid"] else "Нет"}
🌍 Страна: {info["country"]}
📡 Оператор: {info["operator"]}
"""

        response += "\n" + format_phone_results(phone, results)

        # 🌐 Источники
        response += "\n\n🌐 **Источники**\n"
        if sources:
            for s in sources[:10]:
                response += f"• {s['site']} ({s['hint']})\n"
        else:
            response += "❌ Не найдено\n"

        # 💣 Утечки
        response += "\n💣 **Утечки**\n"
        if leaks.get("found"):
            for l in leaks.get("sources", [])[:10]:
                response += f"• {l}\n"
        else:
            response += "✅ Не найдено\n"

        # 🔥 TELEGRAM (НОВОЕ)
        response += "\n\n📱 **Telegram**\n"
        if tg.get("found"):
            response += f"👤 Имя: {tg.get('name')}\n"

            if tg.get("username"):
                response += f"🔗 Username: @{tg.get('username')}\n"

            if tg.get("bot"):
                response += "🤖 Это бот\n"
        else:
            response += "❌ Не найдено\n"

        # 🧠 AI
        response += "\n🧠 **AI профиль**\n"
        response += ai

        # ⏱
        response += f"\n\n⏱ {elapsed:.1f} сек."
        response += "\n━━━━━━━━━━━━━━━━━━━"
        response += "\n⚡ Powered by OSINT Engine"

        # 💾 кеш
        set_cache(cache_key, response)

        await _safe_send(
            status,
            response,
            reply_markup=back_to_menu_keyboard()
        )

        await db.log_search(
            message.from_user.id,
            "phone",
            phone,
            1 if results.get("valid") else 0
        )

    except Exception as e:
        await _safe_send(status, format_error(str(e)))


# ═══════════════════════════════════════════════════════
# PROGRESS BAR
# ═══════════════════════════════════════════════════════

async def _animate_progress(status_msg: Message, query: str):

    steps = [
        "🔍 Поиск по базам",
        "🌐 Проверка сайтов",
        "📡 Сканирование источников",
        "🧠 Анализ данных",
        "⚙️ Обработка результатов",
    ]

    progress = 0

    try:
        while True:
            step = steps[progress % len(steps)]
            percent = int((progress % len(steps) + 1) / len(steps) * 100)
            bar = _progress_bar(percent)

            text = (
                f"{step}...\n"
                f"{bar} {percent}%\n"
                f"🔎 {query}"
            )

            try:
                await status_msg.edit_text(text)
            except:
                break

            progress += 1
            await asyncio.sleep(2)

    except asyncio.CancelledError:
        pass


def _progress_bar(percent: int) -> str:
    total = 10
    filled = int(percent / 100 * total)
    return "█" * filled + "░" * (total - filled)


# ═══════════════════════════════════════════════════════
# SAFE SEND
# ═══════════════════════════════════════════════════════

async def _safe_send(status_msg: Message, text: str, reply_markup=None):

    chunks = split_message(text, 4000)

    try:
        await status_msg.delete()
    except:
        pass

    for i, chunk in enumerate(chunks):
        await status_msg.answer(
            chunk,
            disable_web_page_preview=True,
            reply_markup=reply_markup if i == len(chunks) - 1 else None
        )