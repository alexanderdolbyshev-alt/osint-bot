import asyncio
import shutil

import phonenumbers
from phonenumbers import (
    geocoder, carrier,
    timezone as pn_timezone,
    number_type, PhoneNumberType
)

from config import PHONEINFOGA_PATH

LINE_TYPES = {
    PhoneNumberType.FIXED_LINE: "Стационарный",
    PhoneNumberType.MOBILE: "Мобильный",
    PhoneNumberType.FIXED_LINE_OR_MOBILE: "Стационарный/Мобильный",
    PhoneNumberType.TOLL_FREE: "Бесплатный",
    PhoneNumberType.PREMIUM_RATE: "Премиум",
    PhoneNumberType.SHARED_COST: "Разделённая стоимость",
    PhoneNumberType.VOIP: "VoIP",
    PhoneNumberType.PERSONAL_NUMBER: "Персональный",
    PhoneNumberType.PAGER: "Пейджер",
    PhoneNumberType.UAN: "UAN",
    PhoneNumberType.VOICEMAIL: "Голосовая почта",
    PhoneNumberType.UNKNOWN: "Неизвестный",
}


async def search_phone(phone: str) -> dict:
    result = {
        "valid": False,
        "country": None, "carrier": None,
        "line_type": None, "international": None,
        "local": None, "timezone": None,
        "country_code": None, "region_code": None,
        "phoneinfoga": None,
    }

    try:
        parsed = None
        formats = []

        if phone.startswith("+"):
            formats.append((phone, None))
        else:
            formats.append(("+" + phone.lstrip("0"), None))
            formats.append((phone, "RU"))
            formats.append(("+" + phone, None))

        for phone_str, region in formats:
            try:
                candidate = phonenumbers.parse(phone_str, region)
                if phonenumbers.is_valid_number(candidate):
                    parsed = candidate
                    break
            except phonenumbers.NumberParseException:
                continue

        if not parsed:
            result["error"] = "Не удалось распознать номер"
            return result

        result["valid"] = True

        country = geocoder.description_for_number(parsed, "ru")
        if not country:
            country = geocoder.description_for_number(parsed, "en")
        result["country"] = country or "Неизвестна"

        c_name = carrier.name_for_number(parsed, "ru")
        if not c_name:
            c_name = carrier.name_for_number(parsed, "en")
        result["carrier"] = c_name or "Неизвестен"

        line = number_type(parsed)
        result["line_type"] = LINE_TYPES.get(line, "Неизвестный")

        result["international"] = phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )
        result["local"] = phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.NATIONAL
        )

        timezones = pn_timezone.time_zones_for_number(parsed)
        if timezones:
            result["timezone"] = ", ".join(timezones)

        result["country_code"] = parsed.country_code
        result["region_code"] = phonenumbers.region_code_for_number(parsed)

    except phonenumbers.NumberParseException as e:
        result["error"] = str(e)
        return result

    if _phoneinfoga_available():
        infoga = await _phoneinfoga_scan(
            result.get("international", phone)
        )
        if infoga:
            result["phoneinfoga"] = infoga

    return result


async def _phoneinfoga_scan(phone: str) -> list:
    try:
        process = await asyncio.create_subprocess_exec(
            PHONEINFOGA_PATH, "scan", "-n", phone,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=30
        )
        output = stdout.decode("utf-8", errors="ignore")
        results = []
        skip = ("Running", "Scanning", "[i]", "phoneinfoga")
        for line in output.strip().split("\n"):
            line = line.strip()
            if line and not any(line.startswith(p) for p in skip):
                results.append(line)
        return results if results else None
    except Exception:
        return None


def _phoneinfoga_available() -> bool:
    return shutil.which(PHONEINFOGA_PATH) is not None