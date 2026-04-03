import os
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)


async def analyze_phone_ai(phone: str, info: dict, leaks: dict, sources: list):

    prompt = f"""
Телефон: {phone}

Данные:
Страна: {info.get("country")}
Оператор: {info.get("operator")}
Источники: {sources}
Утечки: {leaks}

Сделай OSINT анализ:

1. Вероятность реального человека (0-100)
2. Тип (личный / бот / бизнес)
3. Риск (низкий / средний / высокий)
4. Краткий вывод

Пиши коротко и по пунктам.
"""

    try:
        response = await client.chat.completions.create(
            model="openrouter/auto",
            messages=[
                {"role": "system", "content": "Ты OSINT аналитик"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"❌ AI ошибка: {e}"