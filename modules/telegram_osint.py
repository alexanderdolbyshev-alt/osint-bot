from telethon import TelegramClient
import os

api_id = int(os.getenv("TG_API_ID"))
api_hash = os.getenv("TG_API_HASH")

client = TelegramClient("osint_session", api_id, api_hash)


async def get_telegram_info(phone: str):
    try:
        await client.connect()

        if not await client.is_user_authorized():
            return {"found": False, "error": "не авторизован"}

        entity = await client.get_entity(phone)

        return {
            "found": True,
            "username": entity.username,
            "name": f"{entity.first_name or ''} {entity.last_name or ''}".strip(),
            "id": entity.id,
            "bot": entity.bot,
        }

    except Exception as e:
        return {
            "found": False,
            "error": str(e)
        }