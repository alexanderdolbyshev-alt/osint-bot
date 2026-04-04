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

from keyboards.inline import (
    main_menu_keyboard,
    back_to_menu_keyboard,
    paywall_keyboard,
)

from modules.username_search import search_username
from modules.username_osint import search_username_socials
from modules.email_search import search_email
from modules.phone_search import (
    search_phone,
    basic_phone_info,
    search_phone_sources,
)
from modules.leak_check import check_leaks
from modules.ai_openrouter import analyze_username_ai
from modules.ai_phone import analyze_phone_ai
from modules.telegram_osint import get_telegram_info

from utils.cache import get_cache, set_cache

router = Router()

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "0").split(",")))

EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
PHONE_RE = re.compile(r"^\+?[0-9]{7,15}$")
USERNAME_RE = re.compile(r"^@?[a-zA-Z0-9_.-]{2,30}$")


# ================= MAIN =================

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

    if not rate_limiter.is_allowed(user_id):
        wait = rate_limiter.seconds_until_reset(user_id)
        await message.answer(f"⏳ Подожди {wait} сек.")
        return

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


# ================= USERNAME =================

async def _handle_username(message, username: str):

    status = await message.answer("🔍 Запуск OSINT...")

    async def update(text):
        try:
            await status.edit_text(text)
        except:
            pass

    start = time.time()

    try:
        await update("🌐 Поиск по базам...")
        search_task = asyncio.create_task(search_username(username))

        await update("📡 Скан соцсетей...")
        social_task = asyncio.create_task(search_username_socials(username))

        await update("📲 Telegram OSINT...")
        tg_task = asyncio.create_task(get_telegram_info(username=username))

        found_sites, all_sites = await search_task
        socials = await social_task
        tg = await tg_task

        await update("🧠 AI анализ...")

        try:
            analysis = await analyze_username_ai(username, found_sites)
        except:
            analysis = "❌ AI недоступен"

        elapsed = time.time() - start

        response = f"👤 Username: {username}\n\n"

        # 🌐 сайты
        response += "🌐 Найдено:\n"
        if found_sites:
            for s in found_sites[:10]:
                response += f"• {s['site']}: {s['url']}\n"
        else:
            response += "❌ Не найдено\n"

        # 📡 соцсети
        response += "\n📡 Соцсети:\n"
        if socials:
            for s in socials:
                response += f"• {s['site']}: {s['url']}\n"
        else:
            response += "❌ Не найдено\n"

        # 📲 TELEGRAM PRO
        response += "\n📲 Telegram:\n"
        if tg and tg.get("found"):
            name = f"{tg.get('first_name','')} {tg.get('last_name','')}".strip()

            if name:
                response += f"👤 Имя: {name}\n"

            if tg.get("username"):
                response += f"🔗 @{tg['username']}\n"

            response += f"🆔 ID: {tg['id']}\n"

            if tg.get("bot"):
                response += "🤖 Бот\n"
            else:
                response += "👨 Человек\n"

            if tg.get("bio"):
                response += f"📝 Bio: {tg['bio']}\n"

        else:
            response += "❌ Не найдено\n"

        # 🧠 AI
        response += "\n🧠 AI Анализ:\n" + analysis
        response += f"\n\n⏱ {elapsed:.1f} сек."

        await status.edit_text(
            response,
            reply_markup=main_menu_keyboard()
        )

    except Exception as e:
        await status.edit_text(f"❌ Ошибка: {e}")


# ================= EMAIL =================

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
            reply_markup=back_to_menu_keyboard()
        )

    except Exception as e:
        await _safe_send(status, format_error(str(e)))


# ================= PHONE =================

async def _handle_phone(message: Message, phone: str):

    status = await message.answer("📱 Запуск анализа...")

    async def update(text):
        try:
            await status.edit_text(text)
        except:
            pass

    start = time.time()

    try:
        cache_key = f"phone:{phone}"
        cached = get_cache(cache_key)

        if cached:
            await status.delete()
            await message.answer(
                "⚡ Найдено в кеше\n\n" + cached,
                reply_markup=back_to_menu_keyboard()
            )
            return

        await update("📡 Поиск источников...")

        results, sources, leaks, tg = await asyncio.gather(
            search_phone(phone),
            search_phone_sources(phone),
            check_leaks(phone),
            get_telegram_info(phone)
        )

        await update("🧠 AI анализ...")

        info = basic_phone_info(phone)

        try:
            ai = await analyze_phone_ai(phone, info, leaks, sources)
        except:
            ai = "❌ AI недоступен"

        elapsed = time.time() - start

        response = f"📱 Номер: {phone}\n\n"
        response += f"🌍 {info['country']} | 📡 {info['operator']}\n"

        response += "\n🌐 Источники:\n"
        if sources:
            for s in sources[:10]:
                response += f"• {s['site']}\n"
        else:
            response += "❌ Не найдено\n"

        response += "\n💣 Утечки:\n"
        if leaks.get("found"):
            for l in leaks.get("sources", []):
                response += f"• {l}\n"
        else:
            response += "✅ Не найдено\n"

        response += "\n📲 Telegram PRO:\n"

if tg and tg.get("found"):
    name = f"{tg.get('first_name','')} {tg.get('last_name','')}".strip()

    if name:
        response += f"👤 Имя: {name}\n"

    if tg.get("username"):
        response += f"🔗 @{tg['username']}\n"

    response += f"🆔 ID: {tg['id']}\n"

    if tg.get("bot"):
        response += "🤖 Бот\n"
    else:
        response += "👨 Человек\n"

    if tg.get("bio"):
        response += f"📝 Bio: {tg['bio']}\n"

else:
    response += "❌ Не найдено\n"

        response += "\n🧠 AI:\n" + ai
        response += f"\n\n⏱ {elapsed:.1f} сек."

        set_cache(cache_key, response)

        await status.edit_text(
            response,
            reply_markup=back_to_menu_keyboard()
        )

    except Exception as e:
        await status.edit_text(f"❌ Ошибка: {e}")


# ================= SAFE SEND =================

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