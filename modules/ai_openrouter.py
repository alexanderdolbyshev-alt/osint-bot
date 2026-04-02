import os
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)


async def analyze_username_ai(username: str, found_sites: list) -> str:

    if not found_sites:
        return "❌ Недостаточно данных"

    sites = [s["site"] for s in found_sites][:10]

    prompt = f"""
Username: {username}
Sites: {', '.join(sites)}

Сделай OSINT анализ:

1. Вероятность реального человека (0-100)
2. Тип аккаунта (личный / бот / бренд)
3. Риск (низкий / средний / высокий)
4. Краткий вывод (1-2 строки)

Пиши строго по пунктам.
"""

    try:
        response = await client.chat.completions.create(
            model="qwen/qwen3-7b",  # 🔥 САМОЕ ВАЖНОЕ
            messages=[
                {"role": "system", "content": "Ты OSINT аналитик"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"❌ AI ошибка: {e}"