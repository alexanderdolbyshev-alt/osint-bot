import asyncio
import aiohttp
import shutil

SITES = {
    "GitHub": "https://github.com/{}",
    "Twitter/X": "https://x.com/{}",
    "Instagram": "https://instagram.com/{}",
    "Reddit": "https://reddit.com/user/{}",
    "TikTok": "https://tiktok.com/@{}",
    "YouTube": "https://youtube.com/@{}",
    "Telegram": "https://t.me/{}",
    "LinkedIn": "https://linkedin.com/in/{}",
}


async def search_username(username: str):

    if _sherlock_available():
        found = await _sherlock_search(username)

        if found:
            return found, None

    return await _fallback_search(username)


async def _sherlock_search(username: str):
    try:
        process = await asyncio.create_subprocess_exec(
            "sherlock", username,
            "--print-found",
            "--no-color",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()
        output = (stdout + stderr).decode()

        results = []

        for line in output.splitlines():
            if line.startswith("[+]"):
                try:
                    content = line[3:].strip()
                    site, url = content.split(": ", 1)

                    results.append({
                        "site": site.strip(),
                        "url": url.strip(),
                        "exists": True
                    })
                except:
                    continue

        return results

    except:
        return []


async def _fallback_search(username: str):
    all_sites = []
    found_sites = []

    timeout = aiohttp.ClientTimeout(total=8)

    async with aiohttp.ClientSession(timeout=timeout) as session:

        tasks = [
            _check_site(session, name, url.format(username), username)
            for name, url in SITES.items()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, dict):
                all_sites.append(result)
                if result["exists"]:
                    found_sites.append(result)

    return found_sites, all_sites


async def _check_site(session, site_name, url, username):
    try:
        async with session.get(url, allow_redirects=True) as resp:
            text = await resp.text()
            final_url = str(resp.url)

            exists = False

            if resp.status == 200:
                if final_url.rstrip("/") == url.rstrip("/"):
                    if username.lower() in text.lower():
                        if "not found" not in text.lower():
                            exists = True

            return {
                "site": site_name,
                "url": url,
                "exists": exists
            }

    except:
        return {
            "site": site_name,
            "url": url,
            "exists": False
        }


def _sherlock_available():
    return shutil.which("sherlock") is not None