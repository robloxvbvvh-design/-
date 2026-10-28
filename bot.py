# Злой бот для Telegram. Работает без установки библиотек.
# Вставь токен в кавычки ниже и запусти файл.
TOKEN = ""

import json
import os
import random
import time
import urllib.error
import urllib.request


def load_token() -> str:
    if TOKEN:
        return TOKEN.strip()
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                key, _, value = line.strip().partition("=")
                if key == "BOT_TOKEN" and value:
                    return value.strip()
    return os.getenv("BOT_TOKEN", "").strip()


API = ""


def call(method: str, **params):
    data = json.dumps(params).encode()
    req = urllib.request.Request(API + method, data, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.load(resp)["result"]


START_TEXT = "Хуй блять, смотри как твой человек разозлится 😡\nНу давай, напиши что-нибудь, сука."

OPENERS = [
    "Ты еблан?",
    "Блять, опять ты.",
    "Сука, ну чего тебе?",
    "Охуеть, кто пожаловал.",
    "Нахуя ты мне это пишешь?",
    "Ебать ты оригинальный.",
    "Пиздец, ну и бред.",
    "Ты серьёзно, долбоёб?",
    "Ну охуеть теперь.",
    "Опять ты со своей хуйнёй.",
]

MIDDLES = [
    "Мне вообще похуй.",
    "Мне не до твоих шуток, сука.",
    "У меня и так день хуёвый.",
    "Я занят, блять, не видишь?",
    "Ты мне весь мозг выебал.",
    "Заебал уже, честно.",
    "Кому ты это вообще пишешь, а?",
    "Я от тебя уже охуел.",
]

CLOSERS = [
    "Иди нахуй.",
    "Съебись отсюда.",
    "Отъебись от меня.",
    "Пиздуй отсюда, блять.",
    "Не беси меня, сука.",
    "Вали нахуй.",
    "Иди в пизду со своим сообщением.",
]

GREETING_REPLIES = [
    "Привет, ты еблан. Приятно познакомиться, нахуй иди блять, мне не до твоих шуток сука.",
    "Здарова, долбоёб. Чего припёрся? Иди нахуй.",
    "Привет-привет, сука. Лучше б ты не писал, блять.",
]

PHOTO_REPLIES = [
    "Что это за хуйня на фотке, блять?",
    "Нахуя ты мне это фото скинул, еблан?",
    "Пиздец, глаза мои. Убери это нахуй.",
    "Ебать ты фотограф, сука. Руки из жопы.",
    "Я эту хуйню видеть не хотел, блять.",
]

VIDEO_REPLIES = [
    "Я не буду смотреть эту хуйню, блять.",
    "Нахуя мне твоё видео, долбоёб?",
    "Ебать, кино снял. Оскар тебе в жопу, сука.",
    "Это самое тупое видео, что я видел, блять.",
    "Выключи это нахуй и больше не присылай.",
]

OTHER_REPLIES = [
    "Что это за хуйня, блять? Пиши нормально, еблан.",
    "Нахуя ты мне это шлёшь, сука?",
    "Засунь это себе в жопу, блять.",
]

GREETINGS = ("привет", "здравств", "здаров", "хай", "хелло", "ку", "салам", "добрый")


def angry_text(text: str) -> str:
    if text.lower().strip(" !.,").startswith(GREETINGS):
        return random.choice(GREETING_REPLIES)
    parts = [random.choice(OPENERS), random.choice(MIDDLES), random.choice(CLOSERS)]
    if random.random() < 0.4:
        parts.insert(1, f"«{text[:50]}» — серьёзно, блять?")
    return " ".join(parts)


def reply_for(msg: dict) -> str:
    text = msg.get("text")
    if text is not None:
        if text.startswith("/start"):
            return START_TEXT
        return angry_text(text)
    if "photo" in msg:
        return f"{random.choice(PHOTO_REPLIES)} {random.choice(CLOSERS)}"
    if "video" in msg or "video_note" in msg or "animation" in msg:
        return f"{random.choice(VIDEO_REPLIES)} {random.choice(CLOSERS)}"
    return random.choice(OTHER_REPLIES)


def main() -> None:
    global API
    token = load_token()
    if not token:
        print("ОШИБКА: нет токена. Вставь его в строку TOKEN = \"...\" в начале файла.")
        return
    API = f"https://api.telegram.org/bot{token}/"

    try:
        me = call("getMe")
    except urllib.error.HTTPError as e:
        print(f"ОШИБКА: Telegram не принял токен (код {e.code}). Проверь токен в @BotFather.")
        return
    except Exception as e:
        print(f"ОШИБКА: нет связи с Telegram: {e}")
        return

    call("deleteWebhook")
    print(f"Бот @{me['username']} запущен! Иди в Telegram и нажми /start.")
    print("Не закрывай это окно, иначе бот выключится.")

    offset = 0
    while True:
        try:
            updates = call("getUpdates", offset=offset, timeout=30)
        except Exception as e:
            print(f"Связь пропала ({e}), пробую снова...")
            time.sleep(3)
            continue
        for upd in updates:
            offset = upd["update_id"] + 1
            msg = upd.get("message")
            if not msg:
                continue
            answer = reply_for(msg)
            print(f"Пришло сообщение, отвечаю: {answer}")
            try:
                call("sendMessage", chat_id=msg["chat"]["id"], text=answer,
                     reply_to_message_id=msg["message_id"])
            except Exception as e:
                print(f"Не смог ответить: {e}")


if __name__ == "__main__":
    main()
