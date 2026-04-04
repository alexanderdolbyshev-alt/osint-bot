from telethon import TelegramClient
import os
import asyncio
from dotenv import load_dotenv

# 👉 загружаем .env
load_dotenv()

api_id = int(os.getenv("TG_API_ID"))
api_hash = os.getenv("TG_API_HASH")

client = TelegramClient("osint_session", api_id, api_hash)


async def main():
    print("Запуск авторизации...")
    await client.start()
    print("✅ УСПЕШНО АВТОРИЗОВАН")


asyncio.run(main())