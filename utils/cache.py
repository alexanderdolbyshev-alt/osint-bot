import time

CACHE = {}
TTL = 300  # 5 минут


def get_cache(key: str):
    data = CACHE.get(key)

    if not data:
        return None

    if time.time() - data["time"] > TTL:
        del CACHE[key]
        return None

    return data["value"]


def set_cache(key: str, value):
    CACHE[key] = {
        "value": value,
        "time": time.time()
    }