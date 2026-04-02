import time
from collections import defaultdict
from config import RATE_LIMIT_PER_MINUTE, ADMIN_IDS


class RateLimiter:
    def __init__(self):
        # user_id -> список timestamp'ов
        self._requests: dict[int, list[float]] = defaultdict(list)

    def is_allowed(self, user_id: int) -> bool:
        """
        Проверяет можно ли выполнить запрос
        """

        # 🔥 Админы без лимитов
        if user_id in ADMIN_IDS:
            return True

        now = time.time()
        window = 60.0  # 1 минута

        # очищаем старые запросы
        self._requests[user_id] = [
            ts for ts in self._requests[user_id]
            if now - ts < window
        ]

        # проверяем лимит
        if len(self._requests[user_id]) >= RATE_LIMIT_PER_MINUTE:
            return False

        # добавляем новый запрос
        self._requests[user_id].append(now)
        return True

    def seconds_until_reset(self, user_id: int) -> int:
        """
        Сколько осталось ждать до следующего запроса
        """

        # админам ждать не нужно
        if user_id in ADMIN_IDS:
            return 0

        if not self._requests[user_id]:
            return 0

        oldest = min(self._requests[user_id])
        wait = 60 - (time.time() - oldest)
        return max(0, int(wait))

    def reset(self, user_id: int):
        """
        Сброс лимитов пользователя (удобно для админа)
        """
        self._requests[user_id] = []


# глобальный объект
rate_limiter = RateLimiter()