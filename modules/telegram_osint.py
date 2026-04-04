from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import os

api_id = int(os.getenv("TG_API_ID"))
api_hash = os.getenv("TG_API_HASH")

client = TelegramClient("osint_session", api_id, api_hash)


async def get_telegram_info(phone: str):
    try:
        await client.connect()

        if not await client.is_user_authorized():
            return {"error": "Не авторизован в Telegram API"}

        result = await client.get_entity(phone)

        return {
            "found": True,
            "username": result.username,
            "name": f"{result.first_name or ''} {result.last_name or ''}".strip(),
            "id": result.id
        }

    except Exception as e:
        return {"found": False, "error": str(e)}