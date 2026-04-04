import re
import asyncio
import time
import os
import random

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


# ================= 💀 DARK TERMINAL =================

async def dark_terminal(msg, lines):
    output = ""

    for line in lines:
        output += f"{line}\n"

        try:
            await msg.edit_text(f"```bash\n{output}_\n```")
        except:
            pass

        await asyncio.sleep(random.uniform(0.25, 0.6))

    try:
        await msg.edit_text(f"```bash\n{output}\n```")
    except:
        pass


# ================= 🔥 ALERT =================

async def alert_block(msg, text):
    try:
        await msg.edit_text(f"🚨 {text}")
    except:
        pass
    await asyncio.sleep(1)


# ================= 🧠 AI THINK =================

async def ai_thinking(msg):
    steps = [
        "🧠 scanning darknet patterns...",
        "🧠 correlating leak databases...",
        "🧠 analyzing identity footprint...",
        "🧠 building risk profile...",
    ]

    for s in steps:
        try:
            await msg.edit_text(f"{s}\n\n⏳ processing...")
        except:
            pass

        await asyncio.sleep(random.uniform(0.6, 1.2))


# ================= 📊 BAR =================

def bar(p):
    total = 12
    filled = int(p / 100 * total)
    return "█" * filled + "░" * (total - filled)


async def progress(msg, p, text):
    try:
        await msg.edit_text(f"{text}\n\n[{bar(p)}] {p}%")
    except:
        pass


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

    status = await message.answer("💀 connecting to darknet...")

    start = time.time()

    try:
        # TOR подключение
        await dark_terminal(status, [
            "> booting darknet interface...",
            "> routing traffic via TOR...",
            "> establishing encrypted tunnel...",
            "> connection established ✓",
        ])

        # 💣 threat alert
        if random.random() < 0.4:
            await alert_block(status, "Suspicious activity detected...")
            await dark_terminal(status, [
                "> bypassing firewall...",
                "> masking identity...",
                "> access granted ✓",
            ])

        # запуск задач
        search_task = asyncio.create_task(search_username(username))
        social_task = asyncio.create_task(search_username_socials(username))
        tg_task = asyncio.create_task(get_telegram_info(username=username))

        # процесс
        await dark_terminal(status, [
            "> scanning surface web...",
            "> scanning deep web...",
            "> scanning darknet markets...",
            "> querying breach databases...",
        ])

        await progress(status, 40, "🌐 extracting data...")
        await asyncio.sleep(0.5)

        await progress(status, 70, "📡 correlating identity...")
        await asyncio.sleep(0.5)

        found_sites, all_sites = await search_task
        socials = await social_task
        tg = await tg_task

        # утечки триггер
        if found_sites and len(found_sites) > 3:
            await alert_block(status, "Data traces found in leak sources")

        # AI
        await ai_thinking(status)

        try:
            analysis = await analyze_username_ai(username, found_sites)
        except:
            analysis = "❌ AI недоступен"

        await progress(status, 100, "✅ completed")

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