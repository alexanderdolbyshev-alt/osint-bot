import os
from telethon import TelegramClient
from telethon.tl.functions.contacts import ImportContactsRequest
from telethon.tl.types import InputPhoneContact

api_id = os.getenv("TG_API_ID")
api_hash = os.getenv("TG_API_HASH")

if api_id:
    api_id = int(api_id)


async def get_telegram_info(phone: str) -> dict:
    if not api_id or not api_hash:
        return {"found": False}

    try:
        async with TelegramClient("session", api_id, api_hash) as client:

            contact = InputPhoneContact(
                client_id=0,
                phone=phone,
                first_name="Temp",
                last_name="User"
            )

            result = await client(ImportContactsRequest([contact]))

            if not result.users:
                return {"found": False}

            user = result.users[0]

            # 🔥 получаем bio
            full = await client.get_entity(user.id)

            return {
                "found": True,
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "bot": user.bot,
            }

    except Exception as e:
        return {"found": False, "error": str(e)}