from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from config import PAYMENT_PACKAGES


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню с кнопками поиска"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="👤 Username",
                callback_data="mode_username"
            ),
            InlineKeyboardButton(
                text="📧 Email",
                callback_data="mode_email"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📱 Phone",
                callback_data="mode_phone"
            ),
            InlineKeyboardButton(
                text="🔍 Полный скан",
                callback_data="mode_full"
            ),
        ],
        [
            InlineKeyboardButton(
                text="👤 Мой профиль",
                callback_data="profile"
            ),
            InlineKeyboardButton(
                text="💳 Купить запросы",
                callback_data="buy_menu"
            ),
        ],
    ])


def buy_keyboard() -> InlineKeyboardMarkup:
    """Меню покупки запросов"""
    buttons = []

    for pack_id, pack in PAYMENT_PACKAGES.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"⭐ {pack['label']} — {pack['stars']} Stars",
                callback_data=f"buy_{pack_id}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="◀️ В меню",
                callback_data="main_menu"
            ),
            InlineKeyboardButton(
                text="🔍 Ещё поиск",
                callback_data="search_again"
            ),
        ]
    ])


def paywall_keyboard() -> InlineKeyboardMarkup:
    """Кнопки когда лимит исчерпан"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💳 Купить запросы",
                callback_data="buy_menu"
            ),
        ],
        [
            InlineKeyboardButton(
                text="⭐ 10 запросов — 50 Stars",
                callback_data="buy_pack_10"
            ),
        ],
        [
            InlineKeyboardButton(
                text="◀️ В меню",
                callback_data="main_menu"
            ),
        ],
    ])


def confirm_payment_keyboard(pack_id: str) -> InlineKeyboardMarkup:
    """Подтверждение оплаты"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Оплатить",
                callback_data=f"confirm_{pack_id}"
            ),
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="buy_menu"
            ),
        ]
    ])


def search_type_keyboard(query: str) -> InlineKeyboardMarkup:
    """Выбор типа поиска для конкретного запроса"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="👤 Как username",
                callback_data=f"do_username_{query}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📧 Как email",
                callback_data=f"do_email_{query}"
            ),
        ],
    ])