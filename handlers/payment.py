from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
    LabeledPrice,
    PreCheckoutQuery,
)

from config import PAYMENT_PACKAGES
from database import db
from keyboards.inline import main_menu_keyboard, confirm_payment_keyboard

router = Router()


# ================= ВЫБОР ПАКЕТА =================

@router.callback_query(F.data.startswith("buy_"))
async def buy(callback: CallbackQuery):
    pack_id = callback.data.replace("buy_", "")

    print("BUY PACK:", pack_id)
    print("AVAILABLE:", PAYMENT_PACKAGES.keys())

    if pack_id not in PAYMENT_PACKAGES:
        await callback.answer("❌ Пакет не найден", show_alert=True)
        return

    pack = PAYMENT_PACKAGES[pack_id]

    await callback.message.edit_text(
        f"💳 Покупка\n\n"
        f"📦 {pack['label']}\n"
        f"🔍 {pack['searches']} запросов\n"
        f"⭐ {pack['stars']} Stars\n\n"
        f"Подтвердить оплату?",
        reply_markup=confirm_payment_keyboard(pack_id)
    )

    await callback.answer()


# ================= ПОДТВЕРЖДЕНИЕ =================

@router.callback_query(F.data.startswith("confirm_"))
async def confirm(callback: CallbackQuery):
    pack_id = callback.data.replace("confirm_", "")

    print("CONFIRM PACK:", pack_id)

    if pack_id not in PAYMENT_PACKAGES:
        await callback.answer("❌ Пакет не найден", show_alert=True)
        return

    pack = PAYMENT_PACKAGES[pack_id]

    await callback.message.answer_invoice(
        title=pack["label"],
        description=f"{pack['searches']} запросов",
        payload=pack_id,  # 🔥 ВАЖНО
        currency="XTR",
        prices=[
            LabeledPrice(
                label=pack["label"],
                amount=pack["stars"]
            )
        ],
    )

    await callback.answer()


# ================= PRE CHECKOUT =================

@router.pre_checkout_query()
async def pre_checkout(pre_checkout: PreCheckoutQuery):
    print("PRE CHECK:", pre_checkout.invoice_payload)

    if pre_checkout.invoice_payload not in PAYMENT_PACKAGES:
        await pre_checkout.answer(
            ok=False,
            error_message="Ошибка пакета"
        )
        return

    await pre_checkout.answer(ok=True)


# ================= УСПЕШНАЯ ОПЛАТА =================

@router.message(F.successful_payment)
async def success(message: Message):

    payment = message.successful_payment
    pack_id = payment.invoice_payload
    user_id = message.from_user.id

    print("SUCCESS PACK:", pack_id)

    if pack_id not in PAYMENT_PACKAGES:
        await message.answer("❌ Ошибка оплаты")
        return

    pack = PAYMENT_PACKAGES[pack_id]

    await db.ensure_user(
        user_id,
        message.from_user.username,
        message.from_user.first_name
    )

    # обычные пакеты
    await db.add_paid_searches(
        user_id=user_id,
        count=pack["searches"],
        package_id=pack_id,
        stars=pack["stars"],
        charge_id=payment.telegram_payment_charge_id
    )

    await message.answer(
        f"✅ Оплата прошла!\n\n"
        f"+{pack['searches']} запросов добавлено 🚀",
        reply_markup=main_menu_keyboard()
    )