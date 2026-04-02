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
- реальный или нет
- оценка 0-100
- риск
Коротко.
"""

    try:
        response = await client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",  # 🔥 САМОЕ ВАЖНОЕ
            messages=[
                {"role": "system", "content": "Ты OSINT аналитик"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"❌ AI ошибка: {e}"