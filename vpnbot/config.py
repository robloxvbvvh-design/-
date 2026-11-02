import json
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN", "")
PUBLIC_URL = os.getenv("PUBLIC_URL", "http://localhost:8080").rstrip("/")
SUB_PORT = int(os.getenv("SUB_PORT", "8080"))
PROFILE_TITLE = os.getenv("PROFILE_TITLE", "My VPN")
# Тестовая оплата: кнопка «купить» сразу выдаёт подписку без денег
TEST_PAYMENTS = os.getenv("TEST_PAYMENTS", "1") == "1"
# Брать бесплатные публичные ключи с GitHub (обновление раз в час)
USE_FREE_KEYS = os.getenv("USE_FREE_KEYS", "1") == "1"
FREE_SOURCES = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub1.txt",
]
ADMINS = {int(x) for x in os.getenv("ADMINS", "").replace(" ", "").split(",") if x}
DB_PATH = str(BASE_DIR / "vpn.db")

TRIAL_DAYS = 3
TAP_SECONDS = 60            # 1 клик = 1 минута
TAP_WITHDRAW_MIN = 24 * 60  # вывести можно от 1 дня (1440 кликов)

DAY = 24 * 60 * 60
# код тарифа: (название, цена в рублях, секунды; None = навсегда)
TARIFFS = {
    "month": ("Месяц", 100, 30 * DAY),
    "year": ("Год", 1000, 365 * DAY),
    "forever": ("Навсегда ♾", 10000, None),
}


def load_servers() -> list[dict]:
    """servers.json (свои ключи) > servers_auto.json (бесплатные с GitHub) > пример. До 10 штук."""
    path = BASE_DIR / "servers.json"
    if not path.exists() and USE_FREE_KEYS:
        path = BASE_DIR / "servers_auto.json"
    if not path.exists():
        path = BASE_DIR / "servers.example.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)[:10]
