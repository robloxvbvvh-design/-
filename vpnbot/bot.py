import asyncio
import logging
import time
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import (CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
                           LabeledPrice, Message, PreCheckoutQuery)
import aiosqlite
from aiohttp import web

import db
from config import (ADMINS, BOT_TOKEN, DAY, DB_PATH, PROVIDER_TOKEN, SUB_PORT, TAP_SECONDS,
                    TAP_WITHDRAW_MIN, TARIFFS, TRIAL_DAYS, load_servers)
from sub_server import make_app, open_url, sub_url

dp = Dispatcher()
_last_tap: dict[int, float] = {}


def kb(*rows):
    return InlineKeyboardMarkup(inline_keyboard=[list(r) for r in rows])


def btn(text, data=None, url=None):
    return InlineKeyboardButton(text=text, callback_data=data, url=url)


MAIN_KB = kb(
    [btn("🌍 Серверы (10)", "servers")],
    [btn("👤 Профиль", "profile"), btn("💳 Продлить", "extend")],
    [btn("👆 Тапалка", "tap"), btn("⚙️ Настройки", "settings")],
)
BACK = [btn("⬅️ Меню", "menu")]


def fmt_left(user) -> str:
    if user["forever"]:
        return "♾ навсегда"
    left = user["expires_at"] - int(time.time())
    if left <= 0:
        return "❌ не активна"
    d, rem = divmod(left, DAY)
    h, rem = divmod(rem, 3600)
    m = rem // 60
    until = datetime.fromtimestamp(user["expires_at"]).strftime("%d.%m.%Y %H:%M")
    return f"✅ до {until} (осталось {d} д {h} ч {m} мин)"


async def edit(cb: CallbackQuery, text: str, markup=None):
    try:
        await cb.message.edit_text(text, reply_markup=markup, disable_web_page_preview=True)
    except TelegramBadRequest:
        pass  # "message is not modified"


# ---------- старт и пробный период ----------

@dp.message(CommandStart())
async def start(msg: Message):
    user = await db.get_or_create(msg.from_user.id)
    if user["trial_state"] == 0:
        await msg.answer(
            f"👋 Добро пожаловать!\n\nАктивировать бесплатный пробный период на {TRIAL_DAYS} дня?",
            reply_markup=kb([btn(f"🎁 Активировать {TRIAL_DAYS} дня", "trial_yes")],
                            [btn("Отказаться", "trial_no")]),
        )
    else:
        await msg.answer("Главное меню:", reply_markup=MAIN_KB)


@dp.callback_query(F.data.in_({"trial_yes", "trial_no"}))
async def trial(cb: CallbackQuery):
    user = await db.get_or_create(cb.from_user.id)
    if user["trial_state"] != 0:
        await cb.answer("Вы уже сделали выбор")
        return await edit(cb, "Главное меню:", MAIN_KB)
    if cb.data == "trial_yes":
        await db.set_trial_state(cb.from_user.id, 1)
        await db.add_time(cb.from_user.id, TRIAL_DAYS * DAY)
        text = f"🎉 Пробный период на {TRIAL_DAYS} дня активирован!\nЗайдите в «Профиль», чтобы подключить Happ."
    else:
        await db.set_trial_state(cb.from_user.id, 2)
        text = "Хорошо, без пробного периода. Подписку можно купить в «Продлить» или натапать."
    await edit(cb, text, MAIN_KB)


@dp.callback_query(F.data == "menu")
async def menu(cb: CallbackQuery):
    await edit(cb, "Главное меню:", MAIN_KB)


# ---------- серверы ----------

@dp.callback_query(F.data == "servers")
async def servers(cb: CallbackQuery):
    user = await db.get_or_create(cb.from_user.id)
    names = "\n".join(f"{i}. {s['name']}" for i, s in enumerate(load_servers(), 1))
    status = "доступны ✅" if db.is_active(user) else "недоступны — нужна подписка ❌"
    await edit(
        cb,
        f"🌍 Серверы ({status}):\n\n{names}\n\nВсе серверы добавляются в Happ одной подпиской.",
        kb([btn("📲 Подключить в Happ", url=open_url(user["token"]))], BACK),
    )


# ---------- профиль ----------

@dp.callback_query(F.data == "profile")
async def profile(cb: CallbackQuery):
    user = await db.get_or_create(cb.from_user.id)
    await edit(
        cb,
        f"👤 Профиль\n\n🆔 ID: <code>{user['id']}</code>\n"
        f"📅 Подписка: {fmt_left(user)}\n"
        f"👆 Натапано: {user['taps']} мин\n\n"
        f"🔗 Ссылка подписки для Happ:\n<code>{sub_url(user['token'])}</code>",
        kb([btn("📲 Открыть в Happ", url=open_url(user["token"]))],
           [btn("💳 Продлить", "extend")], BACK),
    )


# ---------- продление / оплата ----------

@dp.callback_query(F.data == "extend")
async def extend(cb: CallbackQuery):
    rows = [[btn(f"{name} — {price} ₽", f"buy:{code}")] for code, (name, price, _) in TARIFFS.items()]
    await edit(
        cb,
        "💳 Тарифы:\n\n• Месяц (30 дней) — 100 ₽\n• Год (365 дней) — 1 000 ₽\n• Навсегда — 10 000 ₽",
        kb(*rows, BACK),
    )


@dp.callback_query(F.data.startswith("buy:"))
async def buy(cb: CallbackQuery, bot: Bot):
    code = cb.data.split(":", 1)[1]
    if code not in TARIFFS:
        return await cb.answer()
    if not PROVIDER_TOKEN:
        return await cb.answer("Оплата пока не подключена. Напишите администратору.", show_alert=True)
    name, price, _ = TARIFFS[code]
    await cb.answer()
    await bot.send_invoice(
        chat_id=cb.from_user.id,
        title=f"VPN — {name}",
        description=f"Подписка VPN: {name}",
        payload=f"tariff:{code}",
        provider_token=PROVIDER_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label=name, amount=price * 100)],
    )


@dp.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
    code = q.invoice_payload.removeprefix("tariff:")
    ok = code in TARIFFS and q.total_amount == TARIFFS[code][1] * 100 and q.currency == "RUB"
    await q.answer(ok=ok, error_message=None if ok else "Неверный тариф")


@dp.message(F.successful_payment)
async def paid(msg: Message):
    code = msg.successful_payment.invoice_payload.removeprefix("tariff:")
    await db.add_time(msg.from_user.id, TARIFFS[code][2])
    user = await db.get_user(msg.from_user.id)
    await msg.answer(f"✅ Оплата прошла! Подписка: {fmt_left(user)}", reply_markup=MAIN_KB)


# ---------- тапалка ----------

def tap_view(taps: int):
    need = max(0, TAP_WITHDRAW_MIN - taps)
    text = (f"👆 Тапалка\n\nКаждый клик = 1 минута подписки.\n"
            f"Натапано: <b>{taps}</b> мин ({taps // 60} ч {taps % 60} мин)\n\n"
            + ("✅ Можно вывести!" if need == 0 else f"Вывод от 1 дня (1440 мин). Осталось: {need}"))
    rows = [[btn("👆 ТАП +1 мин", "tap_click")]]
    if need == 0:
        rows.append([btn("💸 Вывести в подписку", "tap_withdraw")])
    rows.append(BACK)
    return text, kb(*rows)


@dp.callback_query(F.data == "tap")
async def tap(cb: CallbackQuery):
    user = await db.get_or_create(cb.from_user.id)
    await edit(cb, *tap_view(user["taps"]))


@dp.callback_query(F.data == "tap_click")
async def tap_click(cb: CallbackQuery):
    now = time.monotonic()
    if now - _last_tap.get(cb.from_user.id, 0) < 0.3:  # антиавтокликер
        return await cb.answer("Не так быстро 🙂")
    _last_tap[cb.from_user.id] = now
    await db.get_or_create(cb.from_user.id)
    taps = await db.add_tap(cb.from_user.id)
    await cb.answer(f"+1 мин (всего {taps})")
    await edit(cb, *tap_view(taps))


@dp.callback_query(F.data == "tap_withdraw")
async def tap_withdraw(cb: CallbackQuery):
    user = await db.get_or_create(cb.from_user.id)
    if user["taps"] < TAP_WITHDRAW_MIN:
        return await cb.answer("Нужно натапать минимум 1 день (1440 мин)", show_alert=True)
    taps = await db.take_taps(cb.from_user.id)
    await db.add_time(cb.from_user.id, taps * TAP_SECONDS)
    user = await db.get_user(cb.from_user.id)
    await edit(cb, f"💸 Выведено {taps} мин в подписку!\nПодписка: {fmt_left(user)}", MAIN_KB)


# ---------- настройки ----------

def settings_view(user):
    return ("⚙️ Настройки", kb(
        [btn(f"🔔 Уведомления: {'вкл' if user['notify'] else 'выкл'}", "set_notify")],
        [btn("🔄 Сбросить ссылку подписки", "set_reset")],
        BACK,
    ))


@dp.callback_query(F.data == "settings")
async def settings(cb: CallbackQuery):
    await edit(cb, *settings_view(await db.get_or_create(cb.from_user.id)))


@dp.callback_query(F.data == "set_notify")
async def set_notify(cb: CallbackQuery):
    await db.toggle_notify(cb.from_user.id)
    await edit(cb, *settings_view(await db.get_user(cb.from_user.id)))


@dp.callback_query(F.data == "set_reset")
async def set_reset(cb: CallbackQuery):
    await db.reset_token(cb.from_user.id)
    await cb.answer("Ссылка сброшена. Старая больше не работает — добавьте новую в Happ.", show_alert=True)
    await profile(cb)


# ---------- админ: /give <id> <days|forever> ----------

@dp.message(Command("give"))
async def give(msg: Message):
    if msg.from_user.id not in ADMINS:
        return
    parts = msg.text.split()
    if len(parts) != 3 or not parts[1].isdigit():
        return await msg.answer("Использование: /give <id> <дней|forever>")
    uid = int(parts[1])
    await db.get_or_create(uid)
    await db.add_time(uid, None if parts[2] == "forever" else int(parts[2]) * DAY)
    await msg.answer(f"Готово: {fmt_left(await db.get_user(uid))}")


# ---------- напоминания об окончании ----------

async def reminder_loop(bot: Bot):
    warned: set[int] = set()
    while True:
        await asyncio.sleep(3600)
        now = int(time.time())
        async with aiosqlite.connect(DB_PATH) as conn:
            cur = await conn.execute(
                "SELECT id FROM users WHERE notify=1 AND forever=0 AND expires_at BETWEEN ? AND ?",
                (now, now + DAY))
            ids = [r[0] for r in await cur.fetchall()]
        warned &= set(ids)  # после продления снова можно предупредить
        for uid in ids:
            if uid in warned:
                continue
            warned.add(uid)
            try:
                await bot.send_message(uid, "⏰ Подписка закончится меньше чем через сутки. Продлите в меню «💳 Продлить».")
            except Exception:
                pass


async def main():
    logging.basicConfig(level=logging.INFO)
    await db.init()
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))

    runner = web.AppRunner(make_app())
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", SUB_PORT).start()

    asyncio.create_task(reminder_loop(bot))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
