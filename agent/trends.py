"""Поиск залетевших видео: YouTube Data API, а без ключа — веб-поиск через Claude."""

import re
from datetime import datetime, timedelta, timezone

import requests

YT = "https://www.googleapis.com/youtube/v3"


def _duration_sec(iso: str) -> int:
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def _get(endpoint: str, key: str, **params) -> dict:
    r = requests.get(f"{YT}/{endpoint}", params={**params, "key": key}, timeout=30)
    r.raise_for_status()
    return r.json()


def _video_details(ids: list[str], key: str) -> list[dict]:
    items = []
    for i in range(0, len(ids), 50):
        items += _get("videos", key, part="snippet,statistics,contentDetails",
                      id=",".join(ids[i:i + 50]))["items"]
    return items


def _subscribers(channel_ids: set[str], key: str) -> dict[str, int]:
    subs, ids = {}, list(channel_ids)
    for i in range(0, len(ids), 50):
        for ch in _get("channels", key, part="statistics", id=",".join(ids[i:i + 50]))["items"]:
            subs[ch["id"]] = int(ch["statistics"].get("subscriberCount", 0) or 0)
    return subs


def fetch_youtube(cfg: dict, key: str) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=cfg["lookback_days"])
    ids: set[str] = set()

    popular = _get("videos", key, part="id", chart="mostPopular",
                   regionCode=cfg["region"], maxResults=50)
    ids.update(v["id"] for v in popular["items"])

    for q in cfg["search_queries"]:
        found = _get("search", key, part="id", q=q, type="video", order="viewCount",
                     publishedAfter=since.isoformat().replace("+00:00", "Z"),
                     regionCode=cfg["region"], relevanceLanguage=cfg["language"],
                     videoDuration="short" if cfg["shorts_only"] else "any",
                     maxResults=25)
        ids.update(v["id"]["videoId"] for v in found["items"])

    videos = _video_details(sorted(ids), key)
    subs = _subscribers({v["snippet"]["channelId"] for v in videos}, key)
    now = datetime.now(timezone.utc)

    result = []
    for v in videos:
        sn, st = v["snippet"], v["statistics"]
        duration = _duration_sec(v["contentDetails"]["duration"])
        if cfg["shorts_only"] and duration > 60:
            continue
        published = datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00"))
        hours = max((now - published).total_seconds() / 3600, 1)
        views = int(st.get("viewCount", 0) or 0)
        channel_subs = subs.get(sn["channelId"], 0)
        result.append({
            "url": f"https://youtu.be/{v['id']}",
            "title": sn["title"],
            "channel": sn["channelTitle"],
            "published": sn["publishedAt"],
            "duration_sec": duration,
            "views": views,
            "likes": int(st.get("likeCount", 0) or 0),
            "comments": int(st.get("commentCount", 0) or 0),
            "subscribers": channel_subs,
            "views_per_hour": round(views / hours),
            # Во сколько раз просмотры превышают подписчиков — главный признак «залёта»
            "outlier_ratio": round(views / max(channel_subs, 1000), 2),
            "tags": sn.get("tags", [])[:10],
            "description": sn.get("description", "")[:400],
        })

    result.sort(key=lambda x: x["views_per_hour"] * min(x["outlier_ratio"], 20), reverse=True)
    return result[:cfg["top_videos"]]


def fetch_via_web_search(cfg: dict, client) -> str:
    """Запасной вариант без ключа YouTube: Claude ищет залетевшие ролики в интернете."""
    prompt = (
        f"Найди 10-15 видео (YouTube Shorts, TikTok, Reels) в нише «{cfg['niche']}», "
        f"которые сильно залетели за последние {cfg['lookback_days']} дня(ей), язык: {cfg['language']}. "
        "Для каждого дай: ссылку, название, автора, примерное число просмотров, "
        "и в одной-двух фразах — в чём хук и почему оно залетело. Только реальные видео из найденного."
    )
    messages = [{"role": "user", "content": prompt}]
    tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 10}]
    for _ in range(5):
        with client.messages.stream(model=cfg["model"], max_tokens=16000, tools=tools,
                                    output_config={"effort": "medium"},
                                    messages=messages) as stream:
            response = stream.get_final_message()
        if response.stop_reason != "pause_turn":
            break
        messages = [messages[0], {"role": "assistant", "content": response.content}]
    return "\n".join(b.text for b in response.content if b.type == "text")
