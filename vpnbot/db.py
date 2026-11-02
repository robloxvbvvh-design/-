import secrets
import time

import aiosqlite

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY,
    token       TEXT UNIQUE NOT NULL,
    trial_state INTEGER NOT NULL DEFAULT 0,   -- 0 не спрашивали, 1 взял, 2 отказался
    expires_at  INTEGER NOT NULL DEFAULT 0,
    forever     INTEGER NOT NULL DEFAULT 0,
    taps        INTEGER NOT NULL DEFAULT 0,   -- натапанные минуты
    notify      INTEGER NOT NULL DEFAULT 1,
    created_at  INTEGER NOT NULL
);
"""


async def init():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(SCHEMA)
        await db.commit()


def _row(cur_row):
    if cur_row is None:
        return None
    keys = ("id", "token", "trial_state", "expires_at", "forever", "taps", "notify", "created_at")
    return dict(zip(keys, cur_row))


async def get_user(uid: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT * FROM users WHERE id=?", (uid,))
        return _row(await cur.fetchone())


async def get_by_token(token: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT * FROM users WHERE token=?", (token,))
        return _row(await cur.fetchone())


async def get_or_create(uid: int):
    user = await get_user(uid)
    if user:
        return user
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (id, token, created_at) VALUES (?, ?, ?)",
            (uid, secrets.token_urlsafe(16), int(time.time())),
        )
        await db.commit()
    return await get_user(uid)


async def set_trial_state(uid: int, state: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET trial_state=? WHERE id=?", (state, uid))
        await db.commit()


async def add_time(uid: int, seconds: int | None):
    """Продлить подписку. seconds=None — выдать навсегда."""
    async with aiosqlite.connect(DB_PATH) as db:
        if seconds is None:
            await db.execute("UPDATE users SET forever=1 WHERE id=?", (uid,))
        else:
            now = int(time.time())
            await db.execute(
                "UPDATE users SET expires_at = MAX(expires_at, ?) + ? WHERE id=?",
                (now, seconds, uid),
            )
        await db.commit()


async def add_tap(uid: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET taps = taps + 1 WHERE id=?", (uid,))
        await db.commit()
        cur = await db.execute("SELECT taps FROM users WHERE id=?", (uid,))
        return (await cur.fetchone())[0]


async def take_taps(uid: int) -> int:
    """Списывает все натапанные минуты и возвращает их количество."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT taps FROM users WHERE id=?", (uid,))
        taps = (await cur.fetchone())[0]
        await db.execute("UPDATE users SET taps = 0 WHERE id=?", (uid,))
        await db.commit()
        return taps


async def reset_token(uid: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET token=? WHERE id=?", (secrets.token_urlsafe(16), uid))
        await db.commit()


async def toggle_notify(uid: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET notify = 1 - notify WHERE id=?", (uid,))
        await db.commit()


def is_active(user) -> bool:
    return bool(user["forever"]) or user["expires_at"] > time.time()
