import re
import asyncio
import time
import os

from aiogram import Router
from aiogram.types import Message

from database import db
from config import FREE_SEARCHES_TOTAL
from utils.rate_limit import rate_limiter

from keyboards.inline import main_menu_keyboard, paywall_keyboard

from modules.username_search import search_username
from modules.username_osint import search_username_socials
from modules.ai_openrouter import analyze_username_ai
from modules.telegram_osint import get_telegram_info

from modules.email_search import search_email
from modules.phone_search import search_phone, search_phone_sources, basic_phone_info
from modules.leak_check import check_leaks
from modules.ai_phone import analyze_phone_ai

router = Router()

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "0").split(",")))

USERNAME_RE = re.compile(r"^@?[a-zA-Z0-9_.-]{2,30}$")
EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
PHONE_RE = re.compile(r"^\+?[0-9]{7,15}$")


# ================= UI =================

def build_bar(p):
    total = 12
    filled = int(p / 100 * total)
    return "█" * filled + "░" * (total - filled)


# ================= HYBRID PROGRESS =================

async def hybrid_progress(msg, tasks, label="🔍 Анализ..."):
    fake = 0

    while True:
        done = sum(t.done() for t in tasks)
        total = len(tasks)

        real = int((done / total) * 80)  # реальные %

        # гибрид: немного "догоняем" анимацией
        if fake < real:
            fake = real
        else:
            fake += 1

        fake = min(fake, 95)

        try:
            await msg.edit_text(f"{label}\n\n[{build_bar(fake)}] {fake}%")
        except:
            pass

        if done == total:
            break

        await asyncio.sleep(0.3)


# ================= RISK =================

def calculate_risk(leaks, sources, tg):
    score = 0

    if leaks and leaks.get("found"):
        score += 50 + len(leaks.get("sources", [])) * 5

    if sources:
        score += min(len(sources) * 3, 20)

    if tg and tg.get("found"):
        score += 10

    score = min(score, 100)

    if score < 30:
        level = "🟢 LOW"
    elif score < 70:
        level = "🟡 MEDIUM"
    else:
        level = "🔴 HIGH"

    return score, level


# ================= MAIN =================

@router.message()
async def handle_search(message: Message):
    text = message.text
    if not text or text.startswith("/"):
        return

    text = text.strip()
    user_id = message.from_user.id

    await db.ensure_user(user_id, message.from_user.username, message.from_user.first_name)

    if not rate_limiter.is_allowed(user_id):
        wait = rate_limiter.seconds_until_reset(user_id)
        await message.answer(f"⏳ Подожди {wait} сек.")
        return

    access = await db.can_search(user_id, FREE_SEARCHES_TOTAL)

    if user_id not in ADMIN_IDS and not access["allowed"]:
        await message.answer("🚫 Лимит исчерпан\n\nКупи доступ 👇", reply_markup=paywall_keyboard())
        return

    clean = re.sub(r"[\s\-\(\)]", "", text)

    if EMAIL_RE.match(text):
        await _handle_email(message, text)

    elif PHONE_RE.match(clean):
        await _handle_phone(message, clean)

    elif text.startswith("@"):
        await _handle_username(message, text.lstrip("@"))

    elif USERNAME_RE.match(text):
        await _handle_username(message, text)

    else:
        await message.answer("❓ Не понял формат")


# ================= USERNAME =================

async def _handle_username(message, username: str):
    status = await message.answer("🚀 Старт...")

    start = time.time()

    try:
        t1 = asyncio.create_task(search_username(username))
        t2 = asyncio.create_task(search_username_socials(username))
        t3 = asyncio.create_task(get_telegram_info(username=username))

        tasks = [t1, t2, t3]

        progress = asyncio.create_task(hybrid_progress(status, tasks, "👤 Поиск username..."))

        db_res, socials, tg = await asyncio.gather(*tasks)
        progress.cancel()

        found_sites, _ = db_res

        try:
            ai = await analyze_username_ai(username, found_sites)
        except:
            ai = "❌ AI недоступен"

        await status.edit_text(f"⚡ Завершение...\n\n[{build_bar(100)}] 100%")
        await asyncio.sleep(0.3)

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

        response += "\n📲 Telegram:\n"
        response += "✅ Найден\n" if tg and tg.get("found") else "❌ Не найден\n"

        response += "\n🧠 AI:\n" + ai
        response += f"\n\n⏱ {time.time()-start:.1f} сек."

        await status.edit_text(response, reply_markup=main_menu_keyboard())

    except Exception as e:
        await status.edit_text(f"❌ {e}")


# ================= EMAIL =================

async def _handle_email(message: Message, email: str):
    status = await message.answer("📧 Старт...")

    start = time.time()

    try:
        t1 = asyncio.create_task(search_email(email))
        t2 = asyncio.create_task(check_leaks(email))
        t3 = asyncio.create_task(get_telegram_info(email))

        tasks = [t1, t2, t3]

        progress = asyncio.create_task(hybrid_progress(status, tasks, "📧 Анализ email..."))

        results, leaks, tg = await asyncio.gather(*tasks)
        progress.cancel()

        found = [r["service"] for r in results if r.get("exists")]
        score, level = calculate_risk(leaks, found, tg)

        await status.edit_text(f"⚡ Завершение...\n\n[{build_bar(100)}] 100%")
        await asyncio.sleep(0.3)

        response = f"📧 Email: {email}\n\n"
        response += f"⚠️ Risk Score: {score}/100 ({level})\n\n"

        response += f"🌐 Найдено аккаунтов: {len(found)}\n"
        if found:
            for s in found[:15]:
                response += f"• {s}\n"
        else:
            response += "❌ Не найдено\n"

        response += "\n💣 Утечки:\n"
        if leaks.get("found"):
            for l in leaks.get("sources", []):
                response += f"• {l}\n"
        else:
            response += "✅ Не найдено\n"

        response += "\n📲 Telegram:\n"
        response += "✅ Найден\n" if tg and tg.get("found") else "❌ Не найден\n"

        response += f"\n\n⏱ {time.time()-start:.1f} сек."

        await status.edit_text(response, reply_markup=main_menu_keyboard())

    except Exception as e:
        await status.edit_text(f"❌ {e}")


# ================= PHONE =================

async def _handle_phone(message: Message, phone: str):
    status = await message.answer("📱 Старт...")

    start = time.time()

    try:
        t1 = asyncio.create_task(search_phone(phone))
        t2 = asyncio.create_task(search_phone_sources(phone))
        t3 = asyncio.create_task(check_leaks(phone))
        t4 = asyncio.create_task(get_telegram_info(phone))

        tasks = [t1, t2, t3, t4]

        progress = asyncio.create_task(hybrid_progress(status, tasks, "📱 Анализ номера..."))

        results, sources, leaks, tg = await asyncio.gather(*tasks)
        progress.cancel()

        info = basic_phone_info(phone)

        try:
            ai = await analyze_phone_ai(phone, info, leaks, sources)
        except:
            ai = "❌ AI недоступен"

        score, level = calculate_risk(leaks, sources, tg)

        await status.edit_text(f"⚡ Завершение...\n\n[{build_bar(100)}] 100%")
        await asyncio.sleep(0.3)

        response = f"📱 Номер: {phone}\n\n"
        response += f"⚠️ Risk Score: {score}/100 ({level})\n\n"

        response += "📊 Инфо:\n"
        response += f"🌍 {info['country']}\n📡 {info['operator']}\n"

        response += "\n🌐 Источники:\n"
        if sources:
            for s in sources[:10]:
                response += f"• {s['site']} ({s['hint']})\n"

        response += "\n💣 Утечки:\n"
        if leaks.get("found"):
            for l in leaks.get("sources", []):
                response += f"• {l}\n"
        else:
            response += "✅ Не найдено\n"

        response += "\n📲 Telegram:\n"
        response += "✅ Найден\n" if tg and tg.get("found") else "❌ Не найден\n"

        response += "\n🧠 AI:\n" + ai

        response += f"\n\n⏱ {time.time()-start:.1f} сек."

        await status.edit_text(response, reply_markup=main_menu_keyboard())

    except Exception as e:
        await status.edit_text(f"❌ {e}")