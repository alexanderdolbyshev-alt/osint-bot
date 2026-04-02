import asyncio
import re


async def search_email(email: str) -> list[dict]:

    # базовая проверка
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return [{"service": "INVALID EMAIL", "exists": False}]

    try:
        process = await asyncio.create_subprocess_exec(
            "holehe", email,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=120
        )

        output = (stdout + stderr).decode()

        results = []

        # 🔥 ПРАВИЛЬНЫЙ ЦИКЛ
        for line in output.splitlines():
            line = line.strip()

            # ✅ найдено
            if line.startswith("[+]") and "Email used" not in line:
                try:
                    service = line.split("]", 1)[1].split(":")[0].strip()

                    # фильтр мусора
                    if len(service) > 2:
                        results.append({
                            "service": service,
                            "exists": True
                        })
                except:
                    continue

            # ❌ не найдено
            elif line.startswith("[-]"):
                try:
                    service = line.split("]", 1)[1].split(":")[0].strip()

                    if len(service) > 2:
                        results.append({
                            "service": service,
                            "exists": False
                        })
                except:
                    continue

        # если вообще ничего не нашли
        if not results:
            return [{"service": "No results", "exists": False}]

        return results

    except asyncio.TimeoutError:
        return [{"service": "TIMEOUT", "exists": False}]
    except Exception as e:
        return [{"service": f"ERROR: {e}", "exists": False}]