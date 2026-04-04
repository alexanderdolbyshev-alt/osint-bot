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


# ================= PROGRESS ENGINE =================

def build_bar(p):
    total = 12
    filled = int(p / 100 * total)
    return "█" * filled + "░" * (total - filled)


async def live_progress(msg, text, task_list):
    percent = 0

    while True:
        done = sum(t.done() for t in task_list)
        total = len(task_list)

        # реальный %
        percent = int((done / total) * 80)  # до 80% пока задачи идут

        try:
            await msg.edit_text(
                f"{text}\n\n[{build_bar(percent)}] {percent}%"
            )
        except:
            pass

        if done == total:
            break

        await asyncio.sleep(0.4)


# ================= TERMINAL =================

async def dark_terminal(msg, lines):
    output = ""

    for line in lines:
        output += f"{line}\n"
        try:
            await msg.edit_text(f"```bash\n{output}_\n```")
        except:
            pass
        await asyncio.sleep(random.uniform(0.2, 0.5))

    await msg.edit_text(f"```bash\n{output}\n```")


# ================= AI THINK =================

async def ai_thinking(msg):
    steps = [
        "🧠 analyzing darknet patterns...",
        "🧠 correlating leaks...",
        "🧠 building identity graph...",
    ]

    for s in steps:
        await msg.edit_text(f"{s}\n\n⏳ thinking...")
        await asyncio.sleep(random.uniform(0.6, 1.2))


# ================= MAIN =================

@router.message()
async def handle_search(message: Message):
    text = message.text
    if not text or text.startswith("/"):
        return

    user_id = message.from_user.id

    await db.ensure_user(
        user_id,
        message.from_user.username,
        message.from_user.first_name
    )

    clean = re.sub(r"[\s\-\(\)]", "", text)

    if text.startswith("@"):
        await _handle_username(message, text.lstrip("@"))
    elif USERNAME_RE.match(text):
        await _handle_username(message, text)


# ================= USERNAME =================

async def _handle_username(message, username: str):

    status = await message.answer("💀 connecting to darknet...")

    start = time.time()

    try:
        await dark_terminal(status, [
            "> routing via TOR...",
            "> encrypting tunnel...",
            "> access granted ✓",
        ])

        # задачи
        search_task = asyncio.create_task(search_username(username))
        social_task = asyncio.create_task(search_username_socials(username))
        tg_task = asyncio.create_task(get_telegram_info(username=username))

        tasks = [search_task, social_task, tg_task]

        # запускаем живой прогресс
        progress_task = asyncio.create_task(
            live_progress(status, "🌐 scanning networks...", tasks)
        )

        # ждём задачи
        results = await asyncio.gather(*tasks)

        # стоп прогресса
        progress_task.cancel()

        found_sites, socials, tg = results

        # AI
        await ai_thinking(status)

        try:
            analysis = await analyze_username_ai(username, found_sites)
        except:
            analysis = "❌ AI недоступен"

        # финал
        await status.edit_text(
            f"✅ completed\n\n[{build_bar(100)}] 100%"
        )

        await asyncio.sleep(0.4)

        elapsed = time.time() - start

        response = f"👤 {username}\n\n"
        response += f"🧠 {analysis}\n"
        response += f"\n⏱ {elapsed:.1f} сек."

        await status.edit_text(response)

    except Exception as e:
        await status.edit_text(f"❌ {e}")