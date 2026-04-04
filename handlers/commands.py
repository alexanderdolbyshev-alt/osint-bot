from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database import db
from config import ADMIN_IDS, FREE_SEARCHES_TOTAL
from keyboards.inline import (
    main_menu_keyboard,
    buy_keyboard,
    paywall_keyboard,
    back_keyboard  # 👈 ДОБАВИЛИ
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
#  CALLBACK — ГЛАВНОЕ МЕНЮ (фикс назад)
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


# ═══════════════════════════════════════════════════════
#  CALLBACK — РЕЖИМЫ ПОИСКА (С КНОПКОЙ НАЗАД)
# ═══════════════════════════════════════════════════════

@router.callback_query(F.data == "mode_username")
async def cb_mode_username(callback: CallbackQuery):
    await callback.message.edit_text(
        "👤 **Поиск по username**\n\n"
        "Отправь username:\n"
        "• `@johndoe`\n"
        "• `johndoe`\n\n"
        "❗ Можно нажать «Назад»",
        parse_mode="Markdown",
        reply_markup=back_keyboard()  # 👈 ВАЖНО
    )
    await callback.answer()


@router.callback_query(F.data == "mode_email")
async def cb_mode_email(callback: CallbackQuery):
    await callback.message.edit_text(
        "📧 **Проверка email**\n\n"
        "Отправь email:\n"
        "• `john@gmail.com`\n\n"
        "❗ Можно нажать «Назад»",
        parse_mode="Markdown",
        reply_markup=back_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "mode_phone")
async def cb_mode_phone(callback: CallbackQuery):
    await callback.message.edit_text(
        "📱 **Анализ телефона**\n\n"
        "Отправь номер:\n"
        "• `+79001234567`\n"
        "• `89001234567`\n\n"
        "❗ Можно нажать «Назад»",
        parse_mode="Markdown",
        reply_markup=back_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "mode_full")
async def cb_mode_full(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔍 **Полный скан**\n\n"
        "Отправь username, email или телефон.\n"
        "Бот определит тип автоматически.\n\n"
        "❗ Можно нажать «Назад»",
        parse_mode="Markdown",
        reply_markup=back_keyboard()
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════
#  ПРОФИЛЬ / ПОКУПКА
# ═══════════════════════════════════════════════════════

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