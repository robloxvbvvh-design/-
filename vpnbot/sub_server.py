"""HTTP-сервер подписок для Happ.

GET /sub/<token>   — список ключей (base64), Happ добавляет его как подписку
GET /open/<token>  — страница-редирект happ://add/... (Telegram не даёт ставить happ:// в кнопки)
"""
import base64
import html
import json

from aiohttp import web

import db
from config import PROFILE_TITLE, PUBLIC_URL, load_servers


def sub_url(token: str) -> str:
    return f"{PUBLIC_URL}/sub/{token}"


def open_url(token: str) -> str:
    return f"{PUBLIC_URL}/open/{token}"


async def handle_sub(request: web.Request):
    user = await db.get_by_token(request.match_info["token"])
    if not user:
        return web.Response(status=404, text="not found")
    active = db.is_active(user)
    links = [s["link"] for s in load_servers()] if active else []
    body = base64.b64encode("\n".join(links).encode()).decode()
    expire = 0 if user["forever"] else max(user["expires_at"], 1)  # 0 в Happ = бессрочно
    title = base64.b64encode(PROFILE_TITLE.encode()).decode()
    headers = {
        "profile-title": f"base64:{title}",
        "profile-update-interval": "1",
        "subscription-userinfo": f"upload=0; download=0; total=0; expire={expire}",
    }
    if not active:
        headers["announce"] = "base64:" + base64.b64encode(
            "Подписка закончилась — продлите в боте".encode()
        ).decode()
    return web.Response(text=body, headers=headers)


async def handle_open(request: web.Request):
    token = request.match_info["token"]
    if not await db.get_by_token(token):
        return web.Response(status=404, text="not found")
    deeplink = f"happ://add/{sub_url(token)}"
    safe = html.escape(deeplink, quote=True)
    page = f"""<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(PROFILE_TITLE)}</title>
<body style="font-family:sans-serif;text-align:center;padding:40px">
<p>Открываем Happ…</p>
<p><a href="{safe}" style="font-size:20px">Нажмите, если не открылось</a></p>
<script>location.href={json.dumps(deeplink)};</script>"""
    return web.Response(text=page, content_type="text/html")


def make_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/sub/{token}", handle_sub)
    app.router.add_get("/open/{token}", handle_open)
    return app
