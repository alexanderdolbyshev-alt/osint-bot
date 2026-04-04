"""
Оплата через Telegram Stars
"""

from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
    LabeledPrice,
    PreCheckoutQuery,
)

from database import db
from config import PAYMENT_PACKAGES
from keyboards.inline import (
    main_menu_keyboard,
    confirm_payment_keyboard,
)

router = Router()


# ═══════════════════════════════════════════════════════
#  Выбор пакета
# ═══════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("buy_pack_"))
async def cb_select_package(callback: CallbackQuery):
    pack_id = callback.data.replace("buy_pack_", "")

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
        "Нажми «Оплатить»:",
        parse_mode="Markdown",
        reply_markup=confirm_payment_keyboard(pack_id)
    )

    await callback.answer()


# ═══════════════════════════════════════════════════════
#  Отправка инвойса
# ═══════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("confirm_"))
async def cb_confirm_payment(callback: CallbackQuery):
    pack_id = callback.data.replace("confirm_", "")

    if pack_id not in PAYMENT_PACKAGES:
        await callback.answer("❌ Пакет не найден", show_alert=True)
        return

    pack = PAYMENT_PACKAGES[pack_id]

    await callback.message.answer_invoice(
        title=f"OSINT Bot — {pack['label']}",
        description=(
            f"{pack['searches']} поисковых запросов.\n"
            f"Активируется сразу после оплаты."
        ),
        payload=pack_id,  # ВАЖНО
        currency="XTR",
        prices=[
            LabeledPrice(
                label=pack["label"],
                amount=pack["stars"]
            )
        ],
    )

    await callback.answer()


# ═══════════════════════════════════════════════════════
#  Pre-checkout
# ═══════════════════════════════════════════════════════

@router.pre_checkout_query()
async def on_pre_checkout(pre_checkout: PreCheckoutQuery):
    pack_id = pre_checkout.invoice_payload

    if pack_id not in PAYMENT_PACKAGES:
        await pre_checkout.answer(
            ok=False,
            error_message="Ошибка пакета"
        )
        return

    await pre_checkout.answer(ok=True)


# ═══════════════════════════════════════════════════════
#  УСПЕШНАЯ ОПЛАТА
# ═══════════════════════════════════════════════════════

@router.message(F.successful_payment)
async def on_successful_payment(message: Message):

    payment = message.successful_payment
    pack_id = payment.invoice_payload
    user_id = message.from_user.id

    if pack_id not in PAYMENT_PACKAGES:
        await message.answer("❌ Ошибка оплаты. Напиши в поддержку.")
        return

    pack = PAYMENT_PACKAGES[pack_id]

    # создаем пользователя если нет
    await db.ensure_user(
        user_id,
        message.from_user.username,
        message.from_user.first_name
    )

    # ⭐ БЕЗЛИМИТ
    if pack_id == "pack_unlimited":
        await db.set_premium(user_id, days=30)

        await message.answer(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ **Оплата прошла!**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "♾️ **Premium активирован (30 дней)**\n"
            "🚀 Безлимитный доступ включён\n\n"
            "Спасибо! 🔥",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
        return

    # ⭐ ОБЫЧНЫЕ ПАКЕТЫ
    await db.add_paid_searches(
        user_id=user_id,
        count=pack["searches"],
        package_id=pack_id,
        stars=pack["stars"],
        charge_id=payment.telegram_payment_charge_id
    )

    remaining = await db.get_paid_remaining(user_id)

    await message.answer(
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ **Оплата прошла!**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 Пакет: **{pack['label']}**\n"
        f"🔍 +{pack['searches']} запросов\n"
        f"💰 Баланс: **{remaining}**\n\n"
        "🚀 Можешь продолжать поиск",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )