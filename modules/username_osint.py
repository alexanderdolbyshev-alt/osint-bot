import asyncio
import httpx

SOCIAL_SITES = {
    "Instagram": "https://www.instagram.com/{username}",
    "TikTok": "https://www.tiktok.com/@{username}",
    "GitHub": "https://github.com/{username}",
    "Twitter": "https://twitter.com/{username}",
    "Reddit": "https://www.reddit.com/user/{username}",
    "Telegram": "https://t.me/{username}",
    "YouTube": "https://www.youtube.com/@{username}",
}


async def check_site(client, name, url, username):
    try:
        r = await client.get(url, timeout=10)

        if r.status_code != 200:
            return None

        text = r.text.lower()

        if "not found" in text:
            return None

        if username.lower() not in text:
            return None

        return {"site": name, "url": url}

    except:
        return None


async def search_username_socials(username: str):
    results = []

    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = []

        for name, pattern in SOCIAL_SITES.items():
            url = pattern.format(username=username)
            tasks.append(check_site(client, name, url, username))

        responses = await asyncio.gather(*tasks)

        for r in responses:
            if r:
                results.append(r)

    return results