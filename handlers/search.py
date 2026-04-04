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
    paywall_keyboard,
)

from modules.username_search import search_username
from modules.username_osint import search_username_socials
from modules.leak_check import check_leaks
from modules.ai_openrouter import analyze_username_ai
from modules.telegram_osint import get_telegram_info

router = Router()

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "0").split(",")))
USERNAME_RE = re.compile(r"^@?[a-zA-Z0-9_.-]{2,30}$")


# ================= UI =================

def build_bar(p):
    total = 12
    filled = int(p / 100 * total)
    return "█" * filled + "░" * (total - filled)


def render_status(progress, modules):
    text = f"🌐 OSINT Scan in progress...\n\n"
    text += f"[{build_bar(progress)}] {progress}%\n\n"

    for name, status in modules.items():
        text += f"{name:<20} {status}\n"

    return text


# ================= MODULE PROGRESS =================

async def module_progress_loop(msg, tasks, modules):
    progress = 0

    while True:
        done = sum(t.done() for t in tasks)
        total = len(tasks)

        progress = int((done / total) * 80)

        # обновляем статусы
        if tasks[0].done():
            modules["📡 Databases"] = "✅ DONE"
        if tasks[1].done():
            modules["🌍 Socials"] = "✅ DONE"
        if tasks[2].done():
            modules["📲 Telegram"] = "✅ DONE"
        if tasks[3].done():
            modules["💣 Leaks"] = "✅ DONE"

        try:
            await msg.edit_text(render_status(progress, modules))
        except:
            pass

        if done == total:
            break

        await asyncio.sleep(0.4)


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

    if text.startswith("@"):
        await _handle_username(message, text.lstrip("@"))

    elif USERNAME_RE.match(text):
        await _handle_username(message, text)


# ================= USERNAME =================

async def _handle_username(message, username: str):

    status = await message.answer("💀 starting darknet scan...")

    start = time.time()

    try:
        modules = {
            "📡 Databases": "⏳ SCANNING",
            "🌍 Socials": "⏳ SCANNING",
            "📲 Telegram": "⏳ SCANNING",
            "💣 Leaks": "⏳ SCANNING",
            "🧠 AI Analysis": "❌ WAITING",
        }

        # задачи
        task_db = asyncio.create_task(search_username(username))
        task_social = asyncio.create_task(search_username_socials(username))
        task_tg = asyncio.create_task(get_telegram_info(username=username))
        task_leaks = asyncio.create_task(check_leaks(username))

        tasks = [task_db, task_social, task_tg, task_leaks]

        # прогресс
        progress_task = asyncio.create_task(
            module_progress_loop(status, tasks, modules)
        )

        results = await asyncio.gather(*tasks)
        progress_task.cancel()

        found_sites, socials, tg, leaks = results

        # AI
        modules["🧠 AI Analysis"] = "⏳ RUNNING"
        await status.edit_text(render_status(90, modules))

        try:
            analysis = await analyze_username_ai(username, found_sites)
            modules["🧠 AI Analysis"] = "✅ DONE"
        except:
            analysis = "❌ AI недоступен"
            modules["🧠 AI Analysis"] = "❌ ERROR"

        await status.edit_text(render_status(100, modules))
        await asyncio.sleep(0.5)

        elapsed = time.time() - start

        response = f"👤 {username}\n\n"
        response += f"🧠 {analysis}\n"
        response += f"\n⏱ {elapsed:.1f} сек."

        await status.edit_text(
            response,
            reply_markup=main_menu_keyboard()
        )

    except Exception as e:
        await status.edit_text(f"❌ {e}")