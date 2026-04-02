from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database import db
from config import ADMIN_IDS, FREE_SEARCHES_TOTAL
from keyboards.inline import (
    main_menu_keyboard,
    buy_keyboard,
    paywall_keyboard,
)
from utils.formatter import format_profile

router = Router()


# ═══════════════════════════════════════════════════════
#  /start
# ═══════════════════════════════════════════════════════

@router.message(Command("start"))
async def cmd_start(message: Message):
    await db.ensure_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )

    await message.answer(
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔍 **OSINT Bot**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Поиск информации по открытым источникам.\n\n"
        "Выбери тип поиска или отправь данные напрямую:\n\n"
        "• `@username` — профили на сайтах\n"
        "• `email@mail.com` — регистрации\n"
        "• `+79001234567` — анализ номера\n\n"
        f"🆓 Бесплатно: **{FREE_SEARCHES_TOTAL}** запросов\n"
        "⭐ Дальше — за Telegram Stars\n",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )


# ═══════════════════════════════════════════════════════
#  /help
# ═══════════════════════════════════════════════════════

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📖 **Справка**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "**Как искать:**\n\n"
        "👤 Отправь `@username` или нажми кнопку\n"
        "📧 Отправь `email@mail.com`\n"
        "📱 Отправь `+79001234567`\n\n"
        "**Команды:**\n"
        "/start — главное меню\n"
        "/me — профиль и баланс\n"
        "/buy — купить запросы\n"
        "/help — эта справка\n\n"
        "⚠️ Только для законных целей.\n"
        "Бот использует открытые данные.",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )


# ═══════════════════════════════════════════════════════
#  /me — профиль
# ═══════════════════════════════════════════════════════

@router.message(Command("me"))
async def cmd_me(message: Message):
    user_id = message.from_user.id
    await db.ensure_user(user_id, message.from_user.username,
                         message.from_user.first_name)

    user = await db.get_user(user_id)
    can_search = await db.can_search(user_id, FREE_SEARCHES_TOTAL)

    await message.answer(
        format_profile(user, can_search),
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )


# ═══════════════════════════════════════════════════════
#  /buy — купить запросы
# ═══════════════════════════════════════════════════════

@router.message(Command("buy"))
async def cmd_buy(message: Message):
    await message.answer(
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💳 **Купить запросы**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Оплата через **Telegram Stars** ⭐\n"
        "Мгновенное зачисление.\n\n"
        "Выбери пакет:",
        parse_mode="Markdown",
        reply_markup=buy_keyboard()
    )


# ═══════════════════════════════════════════════════════
#  /stats — статистика (админ)
# ═══════════════════════════════════════════════════════

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("🚫 Только для админов")
        return

    stats = await db.get_stats()

    type_lines = ""
    for qtype, count in stats.get("by_type", []):
        type_lines += f"  • {qtype}: {count}\n"
    if not type_lines:
        type_lines = "  — нет данных\n"

    await message.answer(
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📊 **Статистика**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 Пользователей: **{stats['total_users']}**\n"
        f"🔍 Всего поисков: **{stats['total_searches']}**\n"
        f"📈 За 24ч: **{stats['searches_24h']}**\n"
        f"💰 Платежей: **{stats['total_payments']}**\n"
        f"⭐ Stars получено: **{stats['total_stars']}**\n\n"
        f"По типам:\n{type_lines}",
        parse_mode="Markdown"
    )


# ═══════════════════════════════════════════════════════
#  /premium user_id — выдать премиум (админ)
# ═══════════════════════════════════════════════════════

@router.message(Command("premium"))
async def cmd_premium(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer(
            "⭐ Для Premium — купите пакет запросов.",
            reply_markup=buy_keyboard()
        )
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "Использование: `/premium USER_ID [дней]`",
            parse_mode="Markdown"
        )
        return

    try:
        target_id = int(parts[1])
        days = int(parts[2]) if len(parts) > 2 else 30
        await db.set_premium(target_id, days)
        await message.answer(
            f"✅ Premium на **{days}** дней для `{target_id}`",
            parse_mode="Markdown"
        )
    except ValueError:
        await message.answer("❌ Неверный ID")


# ═══════════════════════════════════════════════════════
#  Callback — кнопки меню
# ═══════════════════════════════════════════════════════

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔍 **OSINT Bot — Меню**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Выбери тип поиска или отправь данные:\n\n"
        "• `@username` — профили\n"
        "• `email@mail.com` — регистрации\n"
        "• `+79001234567` — телефон",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "profile")
async def cb_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    await db.ensure_user(user_id, callback.from_user.username,
                         callback.from_user.first_name)

    user = await db.get_user(user_id)
    can_search = await db.can_search(user_id, FREE_SEARCHES_TOTAL)

    await callback.message.edit_text(
        format_profile(user, can_search),
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "buy_menu")
async def cb_buy_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💳 **Купить запросы**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Оплата через **Telegram Stars** ⭐\n\n"
        "Выбери пакет:",
        parse_mode="Markdown",
        reply_markup=buy_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "search_again")
async def cb_search_again(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔍 Отправь данные для поиска:\n\n"
        "• `@username`\n"
        "• `email@mail.com`\n"
        "• `+79001234567`",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════
#  Callback — выбор режима поиска (кнопки)
# ═══════════════════════════════════════════════════════

@router.callback_query(F.data == "mode_username")
async def cb_mode_username(callback: CallbackQuery):
    await callback.message.edit_text(
        "👤 **Поиск по username**\n\n"
        "Отправь username:\n"
        "• `@johndoe`\n"
        "• `johndoe`",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "mode_email")
async def cb_mode_email(callback: CallbackQuery):
    await callback.message.edit_text(
        "📧 **Проверка email**\n\n"
        "Отправь email:\n"
        "• `john@gmail.com`",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "mode_phone")
async def cb_mode_phone(callback: CallbackQuery):
    await callback.message.edit_text(
        "📱 **Анализ телефона**\n\n"
        "Отправь номер:\n"
        "• `+79001234567`\n"
        "• `89001234567`",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "mode_full")
async def cb_mode_full(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔍 **Полный скан**\n\n"
        "Отправь username, email или телефон.\n"
        "Бот определит тип автоматически.",
        parse_mode="Markdown"
    )
    await callback.answer()