import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import db
from handlers import commands, search, payment

# ─── Логирование ──────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def on_startup():
    await db.connect()
    logger.info("Database connected")
    logger.info("Bot is ready")


async def on_shutdown():
    await db.close()
    logger.info("Bot stopped")


async def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error(
            "BOT_TOKEN not set! "
            "export BOT_TOKEN='your_token'"
        )
        return

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Порядок роутеров важен!
    # 1. Команды (/start, /help)
    # 2. Платежи (pre_checkout, successful_payment)
    # 3. Поиск (catch-all для текстовых сообщений)
    dp.include_router(commands.router)
    dp.include_router(payment.router)
    dp.include_router(search.router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.info("Starting polling...")

    try:
        await dp.start_polling(bot, drop_pending_updates=True)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())