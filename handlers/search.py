import re
import asyncio
import time
import os

from aiogram import Router
from aiogram.types import Message

from database import db
from config import FREE_SEARCHES_TOTAL
from utils.rate_limit import rate_limiter

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

router = Router()

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "0").split(",")))

EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
PHONE_RE = re.compile(r"^\+?[0-9]{7,15}$")
USERNAME_RE = re.compile(r"^@?[a-zA-Z0-9_.-]{2,30}$")


# ================= 💻 HACKER TERMINAL =================

async def hacker_terminal(msg, lines, delay=0.35):
    output = ""

    for line in lines:
        output += f"{line}\n"

        try:
            await msg.edit_text(f"```bash\n{output}\n```")
        except:
            pass

        await asyncio.sleep(delay)


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

    status = await message.answer("💻 Initializing...")

    start = time.time()

    try:
        # 🔥 Терминал — запуск
        await hacker_terminal(status, [
            "> initializing OSINT engine...",
            "> loading modules █░░░░░░░░",
            "> loading modules ███░░░░░░",
            "> loading modules ███████░░",
            "> modules loaded ✓",
            "> preparing scan...",
        ])

        # 🚀 запускаем задачи
        search_task = asyncio.create_task(search_username(username))
        social_task = asyncio.create_task(search_username_socials(username))
        tg_task = asyncio.create_task(get_telegram_info(username=username))

        # 🔥 Терминал — процесс
        await hacker_terminal(status, [
            "> scanning username...",
            "> connecting to databases...",
            "> scanning social networks...",
            "> checking telegram...",
            "> collecting data...",
        ])

        found_sites, all_sites = await search_task
        socials = await social_task
        tg = await tg_task

        # 🧠 AI блок
        await hacker_terminal(status, [
            "> analyzing patterns...",
            "> running AI model...",
        ])

        try:
            analysis = await analyze_username_ai(username, found_sites)
        except:
            analysis = "❌ AI недоступен"

        # ✅ финал
        await hacker_terminal(status, [
            "> finalizing report...",
            "> DONE ✓",
        ])

        elapsed = time.time() - start

        response = f"👤 Username: {username}\n\n"

        response += "🌐 Найдено:\n"
        if found_sites:
            for s in found_sites[:10]:
                response += f"• {s['site']}: {s['url']}\n"
        else:
            response += "❌ Не найдено\n"

        response += "\n📡 Соцсети:\n"
        if socials:
            for s in socials:
                response += f"• {s['site']}: {s['url']}\n"
        else:
            response += "❌ Не найдено\n"

        response += "\n📲 Telegram:\n"
        if tg and tg.get("found"):
            response += f"🆔 ID: {tg['id']}\n"
        else:
            response += "❌ Не найдено\n"

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

    status = await message.answer("💻 Starting email scan...")

    await hacker_terminal(status, [
        "> validating email...",
        "> checking databases...",
        "> scanning leaks...",
        "> DONE ✓",
    ])

    try:
        results = await search_email(email)
        await status.edit_text(str(results))
    except Exception as e:
        await status.edit_text(f"❌ {e}")


# ================= PHONE =================

async def _handle_phone(message: Message, phone: str):

    status = await message.answer("💻 Starting phone scan...")

    await hacker_terminal(status, [
        "> validating number...",
        "> scanning operators...",
        "> checking leaks...",
        "> searching telegram...",
    ])

    try:
        results, sources, leaks, tg = await asyncio.gather(
            search_phone(phone),
            search_phone_sources(phone),
            check_leaks(phone),
            get_telegram_info(phone)
        )

        await hacker_terminal(status, [
            "> running AI analysis...",
            "> DONE ✓",
        ])

        ai = await analyze_phone_ai(phone, {}, leaks, sources)

        await status.edit_text(f"📱 {phone}\n\n{ai}")

    except Exception as e:
        await status.edit_text(f"❌ {e}")