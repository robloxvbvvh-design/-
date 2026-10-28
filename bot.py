import asyncio
import logging
import os
import random

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message


def load_token() -> str:
    token = os.getenv("BOT_TOKEN")
    if not token and os.path.exists(".env"):
        with open(".env", encoding="utf-8") as f:
            for line in f:
                key, _, value = line.strip().partition("=")
                if key == "BOT_TOKEN":
                    token = value.strip()
    if not token:
        raise SystemExit("Нет BOT_TOKEN: задай переменную окружения или файл .env")
    return token


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


dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(START_TEXT)


@dp.message(F.photo)
async def photo(message: Message) -> None:
    await message.reply(f"{random.choice(PHOTO_REPLIES)} {random.choice(CLOSERS)}")


@dp.message(F.video | F.video_note | F.animation)
async def video(message: Message) -> None:
    await message.reply(f"{random.choice(VIDEO_REPLIES)} {random.choice(CLOSERS)}")


@dp.message(F.text)
async def text(message: Message) -> None:
    await message.reply(angry_text(message.text))


@dp.message()
async def other(message: Message) -> None:
    await message.reply(random.choice(OTHER_REPLIES))


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(load_token())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
