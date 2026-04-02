import aiosqlite
import time
from config import DATABASE_PATH, ADMIN_IDS


class Database:
    def __init__(self):
        self.path = DATABASE_PATH
        self.db = None

    async def connect(self):
        self.db = await aiosqlite.connect(self.path)

        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                first_seen REAL,
                is_premium INTEGER DEFAULT 0,
                premium_until REAL DEFAULT 0,
                total_searches INTEGER DEFAULT 0,
                paid_searches_remaining INTEGER DEFAULT 0
            )
        """)

        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS search_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                query_type TEXT,
                query TEXT,
                timestamp REAL,
                results_count INTEGER DEFAULT 0
            )
        """)

        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                package_id TEXT,
                stars_amount INTEGER,
                searches_added INTEGER,
                timestamp REAL,
                telegram_charge_id TEXT
            )
        """)

        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_search_user_time
            ON search_log(user_id, timestamp)
        """)

        await self.db.commit()

    async def close(self):
        if self.db:
            await self.db.close()

    # ─── Пользователи ────────────────────────────────

    async def ensure_user(self, user_id: int, username: str = None,
                          first_name: str = None):
        await self.db.execute("""
            INSERT OR IGNORE INTO users
            (user_id, username, first_name, first_seen)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, first_name, time.time()))
        await self.db.commit()

    async def get_user(self, user_id: int) -> dict:
        async with self.db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            cols = [d[0] for d in cursor.description]
            return dict(zip(cols, row))

    async def is_premium(self, user_id: int) -> bool:
        user = await self.get_user(user_id)
        if not user:
            return False

        if user["is_premium"] and user["premium_until"] > time.time():
            return True

        if user["is_premium"] and user["premium_until"] <= time.time():
            await self.db.execute(
                "UPDATE users SET is_premium = 0 WHERE user_id = ?",
                (user_id,)
            )
            await self.db.commit()
            return False

        return False

    async def set_premium(self, user_id: int, days: int = 30):
        until = time.time() + (days * 86400)
        await self.db.execute("""
            UPDATE users SET is_premium = 1, premium_until = ?
            WHERE user_id = ?
        """, (until, user_id))
        await self.db.commit()

    # ─── Подсчёт запросов ─────────────────────────────

    async def get_total_searches(self, user_id: int) -> int:
        user = await self.get_user(user_id)
        return user["total_searches"] if user else 0

    async def get_paid_remaining(self, user_id: int) -> int:
        user = await self.get_user(user_id)
        return user["paid_searches_remaining"] if user else 0

    async def can_search(self, user_id: int, free_limit: int) -> dict:
        """
        Проверяет может ли юзер делать поиск.
        """

        # 🔥 АДМИН БЕЗ ЛИМИТОВ
        if user_id in ADMIN_IDS:
            return {
                "allowed": True,
                "remaining": 9999,
                "type": "admin"
            }

        user = await self.get_user(user_id)
        if not user:
            return {"allowed": True, "remaining": free_limit, "type": "free"}

        # Premium
        if await self.is_premium(user_id):
            return {"allowed": True, "remaining": 999, "type": "premium"}

        # Платные запросы
        if user["paid_searches_remaining"] > 0:
            return {
                "allowed": True,
                "remaining": user["paid_searches_remaining"],
                "type": "paid"
            }

        # Бесплатные
        used = user["total_searches"]
        remaining = free_limit - used

        if remaining > 0:
            return {
                "allowed": True,
                "remaining": remaining,
                "type": "free"
            }

        return {
            "allowed": False,
            "remaining": 0,
            "type": "exhausted"
        }

    # ─── Логирование ──────────────────────────────────

    async def log_search(self, user_id: int, query_type: str,
                         query: str, results_count: int = 0):

        await self.db.execute("""
            INSERT INTO search_log
            (user_id, query_type, query, timestamp, results_count)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, query_type, query, time.time(), results_count))

        # ❗ НЕ увеличиваем для админа
        if user_id not in ADMIN_IDS:
            await self.db.execute("""
                UPDATE users SET total_searches = total_searches + 1
                WHERE user_id = ?
            """, (user_id,))

        user = await self.get_user(user_id)

        if user and user["paid_searches_remaining"] > 0:
            if not await self.is_premium(user_id):
                await self.db.execute("""
                    UPDATE users
                    SET paid_searches_remaining = paid_searches_remaining - 1
                    WHERE user_id = ?
                """, (user_id,))

        await self.db.commit()


db = Database()