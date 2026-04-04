from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from config import PAYMENT_PACKAGES


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 Username", callback_data="mode_username"),
            InlineKeyboardButton(text="📧 Email", callback_data="mode_email"),
        ],
        [
            InlineKeyboardButton(text="📱 Phone", callback_data="mode_phone"),
            InlineKeyboardButton(text="🔍 Полный скан", callback_data="mode_full"),
        ],
        [
            InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile"),
            InlineKeyboardButton(text="💳 Купить запросы", callback_data="buy_menu"),
        ],
    ])


# 🔥 НОВАЯ КНОПКА НАЗАД (универсальная)
def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")
        ]
    ])


def buy_keyboard() -> InlineKeyboardMarkup:
    buttons = []

    order = ["pack_test", "pack_10", "pack_50", "pack_100", "pack_unlimited"]

    for pack_id in order:
        if pack_id not in PAYMENT_PACKAGES:
            continue

        pack = PAYMENT_PACKAGES[pack_id]

        buttons.append([
            InlineKeyboardButton(
                text=f"⭐ {pack['label']} — {pack['stars']} Stars",
                callback_data=f"buy_{pack_id}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu"),
            InlineKeyboardButton(text="🔍 Ещё поиск", callback_data="search_again"),
        ]
    ])


def paywall_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💳 Купить запросы", callback_data="buy_menu"),
        ],
        [
            InlineKeyboardButton(text="⭐ 10 запросов — 50 Stars", callback_data="buy_pack_10"),
        ],
        [
            InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu"),
        ],
    ])


def confirm_payment_keyboard(pack_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Оплатить", callback_data=f"confirm_{pack_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="buy_menu"),
        ]
    ])


def search_type_keyboard(query: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 Как username", callback_data=f"do_username_{query}"),
        ],
        [
            InlineKeyboardButton(text="📧 Как email", callback_data=f"do_email_{query}"),
        ],
        [
            InlineKeyboardButton(text="📱 Как phone", callback_data=f"do_phone_{query}"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu"),
        ]
    ])