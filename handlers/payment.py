"""
Оплата через Telegram Stars.
Telegram Stars — встроенная валюта, работает без внешних провайдеров.
"""

from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
    LabeledPrice,
    PreCheckoutQuery,
)

from database import db
from config import PAYMENT_PACKAGES, FREE_SEARCHES_TOTAL
from keyboards.inline import (
    main_menu_keyboard,
    buy_keyboard,
    confirm_payment_keyboard,
)

router = Router()


# ═══════════════════════════════════════════════════════
#  Выбор пакета (callback от кнопок buy_packXX)
# ═══════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("buy_pack_"))
async def cb_select_package(callback: CallbackQuery):
    pack_id = callback.data.replace("buy_", "")

    if pack_id not in PAYMENT_PACKAGES:
        await callback.answer("❌ Пакет не найден", show_alert=True)
        return

    pack = PAYMENT_PACKAGES[pack_id]

    await callback.message.edit_text(
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💳 **Подтверждение покупки**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 Пакет: **{pack['label']}**\n"
        f"🔍 Запросов: **{pack['searches']}**\n"
        f"⭐ Цена: **{pack['stars']} Stars**\n\n"
        "Нажми «Оплатить» для покупки:",
        parse_mode="Markdown",
        reply_markup=confirm_payment_keyboard(pack_id)
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════
#  Подтверждение → отправка инвойса Telegram Stars
# ═══════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("confirm_pack_"))
async def cb_confirm_payment(callback: CallbackQuery):
    pack_id = callback.data.replace("confirm_", "")

    if pack_id not in PAYMENT_PACKAGES:
        await callback.answer("❌ Пакет не найден", show_alert=True)
        return

    pack = PAYMENT_PACKAGES[pack_id]

    # Отправляем инвойс через Telegram Stars
    # XTR — валюта Telegram Stars
    await callback.message.answer_invoice(
        title=f"OSINT Bot — {pack['label']}",
        description=(
            f"Пакет из {pack['searches']} поисковых запросов.\n"
            f"Активируется мгновенно после оплаты."
        ),
        payload=pack_id,  # Передаём ID пакета в payload
        currency="XTR",   # XTR = Telegram Stars
        prices=[
            LabeledPrice(
                label=pack["label"],
                amount=pack["stars"]  # В Stars amount = кол-во звёзд
            )
        ],
    )

    await callback.answer()


# ═══════════════════════════════════════════════════════
#  Pre-checkout — Telegram спрашивает "можно ли провести?"
# ═══════════════════════════════════════════════════════

@router.pre_checkout_query()
async def on_pre_checkout(pre_checkout: PreCheckoutQuery):
    """
    Telegram отправляет это ПЕРЕД списанием денег.
    Нужно ответить за 10 секунд.
    Если ok=True — деньги спишутся.
    """
    pack_id = pre_checkout.invoice_payload

    if pack_id not in PAYMENT_PACKAGES:
        await pre_checkout.answer(
            ok=False,
            error_message="Пакет не найден. Попробуйте снова."
        )
        return

    # Всё ок — разрешаем оплату
    await pre_checkout.answer(ok=True)


# ═══════════════════════════════════════════════════════
#  Успешная оплата — зачисляем запросы
# ═══════════════════════════════════════════════════════

@router.message(F.successful_payment)
async def on_successful_payment(message: Message):
    """
    Telegram подтвердил что деньги списались.
    Зачисляем запросы пользователю.
    """
    payment = message.successful_payment
    pack_id = payment.invoice_payload
    user_id = message.from_user.id

    if pack_id not in PAYMENT_PACKAGES:
        await message.answer("⚠️ Ошибка: пакет не найден. Напишите в поддержку.")
        return

    pack = PAYMENT_PACKAGES[pack_id]

    # Убедимся что юзер есть в базе
    await db.ensure_user(user_id, message.from_user.username,
                         message.from_user.first_name)

    # Для безлимита — выдаём Premium
    if pack_id == "pack_unlimited":
        await db.set_premium(user_id, days=30)
        await message.answer(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ **Оплата прошла!**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⭐ Статус: **Premium (30 дней)**\n"
            "♾️ Безлимитные запросы активированы!\n\n"
            "Спасибо за покупку! 🎉",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
    else:
        # Зачисляем запросы
        charge_id = payment.telegram_payment_charge_id
        await db.add_paid_searches(
            user_id=user_id,
            count=pack["searches"],
            package_id=pack_id,
            stars=pack["stars"],
            charge_id=charge_id
        )

        remaining = await db.get_paid_remaining(user_id)

        await message.answer(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ **Оплата прошла!**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📦 Пакет: **{pack['label']}**\n"
            f"🔍 Зачислено: **+{pack['searches']}** запросов\n"
            f"💰 Всего доступно: **{remaining}** запросов\n\n"
            "Можешь искать! 🎉",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )