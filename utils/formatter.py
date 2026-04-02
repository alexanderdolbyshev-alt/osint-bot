from config import MAX_MESSAGE_LENGTH


def format_username_results(username: str, found_sites: list,
                            all_sites: list = None) -> str:

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        f"👤 **Поиск: `@{username}`**",
        "━━━━━━━━━━━━━━━━━━━━━━━━\n",
    ]

    if not found_sites:
        lines.append("❌ Профили не найдены.\n")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)

    # 🔥 ЕСЛИ SHERLOCK (много результатов)
    if all_sites and len(all_sites) > 10:

        for site in found_sites[:15]:
            name = site.get("site", "Unknown")
            url = site.get("url", "")

            lines.append(f"  ✅ **{name}**")
            lines.append(f"     └ {url}")

        lines.append(f"\n📊 **Найдено: {len(found_sites)} сайтов**")

    # 🔥 FALLBACK (8 сайтов)
    elif all_sites:
        found_names = {s.get("site", "").lower() for s in found_sites}

        for site_info in all_sites:
            name = site_info.get("site", "Unknown")
            url = site_info.get("url", "")

            if name.lower() in found_names:
                lines.append(f"  ✅ **{name}**")
                lines.append(f"     └ {url}")
            else:
                lines.append(f"  ❌ {name}")

        total = len(all_sites)
        found = len(found_sites)

        lines.append(f"\n📊 **Найдено: {found}/{total}**")
        lines.append(_progress_bar(found, total))

    # 🔥 fallback если all_sites None
    else:
        for site in found_sites[:15]:
            name = site.get("site", "Unknown")
            url = site.get("url", "")

            lines.append(f"  ✅ **{name}**")
            lines.append(f"     └ {url}")

        lines.append(f"\n📊 **Найдено: {len(found_sites)} сайтов**")

    lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━")

    return _truncate("\n".join(lines))


def format_email_results(email: str, services: list) -> str:
    """Красивый вывод email-проверки"""

    registered = [s for s in services if s.get("exists")]
    not_found = [s for s in services if not s.get("exists")]

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📧 **Проверка: `{email}`**",
        "━━━━━━━━━━━━━━━━━━━━━━━━\n",
    ]

    if registered:
        lines.append(f"✅ **Зарегистрирован ({len(registered)}):**\n")
        for s in registered:
            name = s.get("service", "Unknown")
            lines.append(f"  ✅ {name}")
    else:
        lines.append("❌ Регистрации не найдены.\n")

    # Показываем несколько ❌ для наглядности
    if not_found:
        lines.append(f"\n❌ **Не найден ({len(not_found)}):**\n")
        # Показываем первые 10
        for s in not_found[:10]:
            name = s.get("service", "Unknown")
            lines.append(f"  ❌ {name}")
        if len(not_found) > 10:
            lines.append(f"  _...и ещё {len(not_found) - 10}_")

    # Статистика
    total = len(services)
    found = len(registered)
    lines.append(f"\n📊 **Найдено: {found}/{total}**")
    lines.append(_progress_bar(found, total))

    lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━")

    return _truncate("\n".join(lines))


def format_phone_results(phone: str, info: dict) -> str:
    """Красивый вывод анализа телефона"""

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📱 **Анализ: `{phone}`**",
        "━━━━━━━━━━━━━━━━━━━━━━━━\n",
    ]

    if info.get("valid") is False:
        lines.append("❌ **Номер невалидный**")
        if info.get("error"):
            lines.append(f"Причина: _{info['error']}_")
        lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)

    # Основная инфа
    fields = [
        ("🌍 Страна", info.get("country")),
        ("📡 Оператор", info.get("carrier")),
        ("📋 Тип", info.get("line_type")),
        ("🌐 Формат", info.get("international")),
        ("📞 Локальный", info.get("local")),
        ("🕐 Часовой пояс", info.get("timezone")),
        ("🏳️ Код страны", info.get("country_code")),
        ("📍 Регион", info.get("region_code")),
    ]

    for label, value in fields:
        if value:
            lines.append(f"  {label}: **{value}**")

    # PhoneInfoga
    if info.get("phoneinfoga"):
        lines.append("\n🔎 **Расширенный анализ:**\n")
        for item in info["phoneinfoga"]:
            lines.append(f"  • {item}")

    lines.append(f"\n✅ **Статус: Валидный номер**")
    lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━")

    return _truncate("\n".join(lines))


def format_combined_results(username: str = None, email: str = None,
                            phone: str = None, results: dict = None,
                            elapsed: float = 0) -> str:
    """Объединённый результат параллельного сканирования"""

    sections = [
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        "🚀 **Полное сканирование**",
        "━━━━━━━━━━━━━━━━━━━━━━━━\n",
    ]

    if "username" in results:
        data = results["username"]
        if isinstance(data, dict) and "error" in data:
            sections.append(f"👤 @{username}: ❌ {data['error']}")
        elif isinstance(data, list):
            sections.append(
                f"👤 **@{username}** → **{len(data)}** сайтов"
            )
            for site in data[:10]:
                sections.append(
                    f"  ✅ {site.get('site')}"
                )
            if len(data) > 10:
                sections.append(f"  _...и ещё {len(data) - 10}_")

    if "email" in results:
        data = results["email"]
        if isinstance(data, dict) and "error" in data:
            sections.append(f"\n📧 {email}: ❌ {data['error']}")
        elif isinstance(data, list):
            registered = [s for s in data if s.get("exists")]
            sections.append(
                f"\n📧 **{email}** → **{len(registered)}** сервисов"
            )
            for s in registered[:10]:
                sections.append(f"  ✅ {s.get('service')}")

    if "phone" in results:
        data = results["phone"]
        if isinstance(data, dict) and "error" in data:
            sections.append(f"\n📱 {phone}: ❌ {data['error']}")
        elif isinstance(data, dict) and data.get("valid"):
            sections.append(f"\n📱 **{phone}**")
            if data.get("country"):
                sections.append(f"  🌍 {data['country']}")
            if data.get("carrier"):
                sections.append(f"  📡 {data['carrier']}")

    sections.append(f"\n⏱ Время: **{elapsed:.1f}** сек.")
    sections.append("━━━━━━━━━━━━━━━━━━━━━━━━")

    return _truncate("\n".join(sections))


def format_error(error_msg: str) -> str:
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ **Ошибка**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"```\n{error_msg[:500]}\n```\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def format_profile(user: dict, can_search_info: dict) -> str:
    """Красивый профиль пользователя"""
    is_prem = bool(user.get("is_premium"))
    status = "⭐ Premium" if is_prem else "🆓 Free"
    total = user.get("total_searches", 0)
    paid = user.get("paid_searches_remaining", 0)

    remaining = can_search_info.get("remaining", 0)
    search_type = can_search_info.get("type", "free")

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        "👤 **Мой профиль**",
        "━━━━━━━━━━━━━━━━━━━━━━━━\n",
        f"  🆔 ID: `{user['user_id']}`",
        f"  📛 Статус: **{status}**",
        f"  🔍 Всего поисков: **{total}**",
    ]

    if search_type == "premium":
        lines.append(f"  ♾️ Запросов: **безлимит**")
    elif search_type == "paid":
        lines.append(f"  💰 Оплаченных осталось: **{paid}**")
    elif search_type == "free":
        lines.append(f"  🆓 Бесплатных осталось: **{remaining}**")
    else:
        lines.append(f"  🚫 Запросы **закончились**")

    # Прогресс-бар использования
    if not is_prem and search_type != "premium":
        from config import FREE_SEARCHES_TOTAL
        used = min(total, FREE_SEARCHES_TOTAL)
        bar = _progress_bar(used, FREE_SEARCHES_TOTAL)
        lines.append(f"\n  Использовано: {bar}")

    lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━")

    return "\n".join(lines)


def format_processing(query: str, search_type: str, stage: int = 0) -> str:
    """Сообщение обработки с анимацией"""

    icons = {
        "username": "👤",
        "email": "📧",
        "phone": "📱",
    }
    icon = icons.get(search_type, "🔍")

    stages_text = {
        "username": [
            "Подключаюсь к источникам",
            "Проверяю социальные сети",
            "Проверяю форумы и блоги",
            "Проверяю IT-платформы",
            "Собираю результаты",
        ],
        "email": [
            "Подключаюсь к сервисам",
            "Проверяю Google, Microsoft",
            "Проверяю социальные сети",
            "Проверяю остальные платформы",
            "Собираю результаты",
        ],
        "phone": [
            "Анализирую номер",
            "Определяю оператора",
            "Собираю данные",
        ],
    }

    current_stages = stages_text.get(search_type, ["Обрабатываю"])
    stage = min(stage, len(current_stages) - 1)

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        f"{icon} **Обработка: `{query}`**",
        "━━━━━━━━━━━━━━━━━━━━━━━━\n",
    ]

    for i, s in enumerate(current_stages):
        if i < stage:
            lines.append(f"  ✅ {s}")
        elif i == stage:
            lines.append(f"  ⏳ {s}...")
        else:
            lines.append(f"  ⬜ {s}")

    # Прогресс-бар
    progress = (stage + 1) / len(current_stages)
    filled = int(progress * 10)
    empty = 10 - filled
    bar = "█" * filled + "░" * empty
    pct = int(progress * 100)

    lines.append(f"\n  [{bar}] {pct}%")
    lines.append(f"\n  ⏳ _Подождите..._")
    lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━")

    return "\n".join(lines)


# ─── Утилиты ──────────────────────────────────────────

def _progress_bar(value: int, total: int, length: int = 10) -> str:
    """Генерирует текстовый прогресс-бар"""
    if total == 0:
        return "[░░░░░░░░░░] 0%"

    ratio = min(value / total, 1.0)
    filled = int(ratio * length)
    empty = length - filled
    bar = "█" * filled + "░" * empty
    pct = int(ratio * 100)

    return f"[{bar}] {pct}%"


def _truncate(text: str) -> str:
    if len(text) <= MAX_MESSAGE_LENGTH:
        return text
    return text[:MAX_MESSAGE_LENGTH - 50] + "\n\n⚠️ _...результат обрезан_"


def split_message(text: str, max_len: int = 4000) -> list:
    """Разбивает длинное сообщение"""
    if len(text) <= max_len:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break

        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len

        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")

    return chunks