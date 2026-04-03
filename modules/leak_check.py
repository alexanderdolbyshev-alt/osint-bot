async def check_leaks(phone: str):
    """
    Базовая проверка утечек (заглушка)
    """

    leaks = []

    # пример логики (потом заменим на API)
    if phone.endswith("00"):
        leaks.append("demo_leak_db")

    return {
        "found": len(leaks) > 0,
        "sources": leaks
    }