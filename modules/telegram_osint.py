import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.contacts import ImportContactsRequest
from telethon.tl.types import InputPhoneContact

# 🔥 ENV
api_id = int(os.getenv("TG_API_ID"))
api_hash = os.getenv("TG_API_HASH")

client = TelegramClient("osint_session", api_id, api_hash)


async def get_telegram_info(phone: str = None, username: str = None):
    try:
        await client.connect()

        if not await client.is_user_authorized():
            return {"found": False, "error": "Not authorized"}

        user = None

        # ================= PHONE =================
        if phone:
            contact = InputPhoneContact(
                client_id=0,
                phone=phone,
                first_name="Temp",
                last_name="User"
            )

            result = await client(ImportContactsRequest([contact]))

            if result.users:
                user = result.users[0]

        # ================= USERNAME =================
        elif username:
            try:
                user = await client.get_entity(username)
            except:
                return {"found": False}

        if not user:
            return {"found": False}

        # 🔥 БИО
        bio = None
        try:
            full = await client.get_entity(user.id)
            bio = getattr(full, "about", None)
        except:
            pass

        # 🔥 ФОТО
        photo = None
        try:
            photo = await client.download_profile_photo(user, file="temp.jpg")
        except:
            pass

        return {
            "found": True,
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "bot": user.bot,
            "bio": bio,
            "photo": photo,
        }

    except Exception as e:
        return {
            "found": False,
            "error": str(e)
        }