"""Сборщик бесплатных публичных ключей с GitHub.

Раз в час скачивает списки, проверяет, что сервер отвечает (TCP), и оставляет
10 самых быстрых. Результат — servers_auto.json, его отдаёт сервер подписок.
"""
import asyncio
import base64
import json
import logging
import re
import time
from urllib.parse import unquote, urlsplit

import aiohttp

from config import BASE_DIR, FREE_SOURCES

AUTO_PATH = BASE_DIR / "servers_auto.json"
LINK_RE = re.compile(r"(?:vless|vmess|trojan|ss)://[^\s]+")
log = logging.getLogger("collector")


def _decode_if_base64(text: str) -> str:
    if "://" in text:
        return text
    try:
        return base64.b64decode(text.strip() + "===").decode("utf-8", "ignore")
    except Exception:
        return text


def _host_port(link: str):
    try:
        if link.startswith("vmess://"):
            data = json.loads(base64.b64decode(link[8:] + "===").decode())
            return data["add"], int(data["port"])
        u = urlsplit(link)
        return u.hostname, u.port
    except Exception:
        return None, None


def _name(link: str, i: int) -> str:
    # в названиях публичных ключей обычно реклама каналов — берём только флаг страны
    tag = unquote(link.split("#", 1)[1]) if "#" in link and not link.startswith("vmess://") else ""
    flag = re.search(r"[\U0001F1E6-\U0001F1FF]{2}", tag)
    return f"{flag.group(0) if flag else '🌐'} Сервер {i}"


async def _ping(host, port, timeout=3.0):
    start = time.monotonic()
    try:
        _, w = await asyncio.wait_for(asyncio.open_connection(host, port), timeout)
        w.close()
        return time.monotonic() - start
    except Exception:
        return None


async def collect(limit: int = 10) -> list[dict]:
    links: list[str] = []
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as s:
        for url in FREE_SOURCES:
            try:
                async with s.get(url) as r:
                    links += LINK_RE.findall(_decode_if_base64(await r.text()))
            except Exception as e:
                log.warning("source failed %s: %s", url, e)

    seen, candidates = set(), []
    for link in links:
        hp = _host_port(link)
        if hp[0] and hp[1] and hp not in seen:
            seen.add(hp)
            candidates.append((link, hp))
    candidates = candidates[:300]

    sem = asyncio.Semaphore(50)

    async def check(item):
        async with sem:
            return item[0], await _ping(*item[1])

    results = await asyncio.gather(*(check(c) for c in candidates))
    alive = sorted((r for r in results if r[1] is not None), key=lambda r: r[1])[:limit]
    servers = [{"name": _name(link, i), "link": link} for i, (link, _) in enumerate(alive, 1)]
    log.info("collected %d links, %d alive, saved %d", len(candidates), len(alive), len(servers))
    if servers:
        AUTO_PATH.write_text(json.dumps(servers, ensure_ascii=False, indent=1), encoding="utf-8")
    return servers


async def collector_loop(interval: int = 3600):
    while True:
        try:
            await collect()
        except Exception:
            log.exception("collect failed")
        await asyncio.sleep(interval)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    for s in asyncio.run(collect()):
        print(s["name"])
