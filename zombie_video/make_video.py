#!/usr/bin/env python3
"""Генератор видео «Как выжить в зомби-апокалипсисе» с озвучкой.

Требования: ffmpeg, RHVoice (rhvoice + rhvoice-russian), Pillow, numpy.
Запуск: python3 make_video.py  -> zombie_survival.mp4
"""
import os, subprocess, wave, textwrap, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "build")
OUT = os.path.join(HERE, "zombie_survival.mp4")
os.makedirs(WORK, exist_ok=True)

W, H = 1280, 720
SR = 24000
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

# Персонажи: имя -> (голос RHVoice, цвет)
CAST = {
    "Рассказчик": ("aleksandr-hq", (230, 230, 230)),
    "Марина":     ("elena",        (120, 200, 255)),
    "Сержант":    ("yuriy",        (255, 170, 60)),
}

# Сцены: (заголовок, эмодзи, [(персонаж, реплика), ...])
SCENES = [
    ("КАК ВЫЖИТЬ В ЗОМБИ-АПОКАЛИПСИСЕ", "🧟", [
        ("Рассказчик", "День первый. Город затих. По улицам бродят те, кто ещё вчера были нашими соседями."),
        ("Марина", "Сержант, что нам делать? Я не знаю, с чего начать!"),
        ("Сержант", "Без паники. Паника убивает быстрее зомби. Слушай и запоминай. Семь правил выживания."),
    ]),
    ("ПРАВИЛО 1. ВОДА И ЕДА", "💧", [
        ("Сержант", "Первое — вода. Без еды человек протянет недели, без воды — три дня."),
        ("Марина", "Набрать воду из-под крана, пока она ещё течёт?"),
        ("Сержант", "Верно. Наполни ванну, бутылки, канистры. А еду бери ту, что долго хранится: консервы, крупы, сухари."),
    ]),
    ("ПРАВИЛО 2. ТРЕВОЖНЫЙ РЮКЗАК", "🎒", [
        ("Рассказчик", "Тревожный рюкзак должен быть собран заранее и стоять у двери."),
        ("Сержант", "Фонарик, батарейки, аптечка, нож, спички, верёвка, карта, документы. И пара тёплых носков."),
        ("Марина", "Носков?"),
        ("Сержант", "Мокрые ноги — это болезнь. Больной выживший — мёртвый выживший."),
    ]),
    ("ПРАВИЛО 3. ТИШИНА", "🤫", [
        ("Рассказчик", "Зомби идут на звук. Каждый крик, каждый хлопок двери — это приглашение на ужин."),
        ("Сержант", "Никакой музыки, никаких моторов без нужды. Двигайся тихо, говори шёпотом."),
        ("Марина", "Поняла. А если они уже рядом?"),
        ("Сержант", "Брось что-нибудь шумное в сторону и уходи в противоположную. Отвлекай, а не воюй."),
    ]),
    ("ПРАВИЛО 4. УКРЫТИЕ", "🏠", [
        ("Рассказчик", "Лучшее укрытие — то, которое легко защитить и откуда легко уйти."),
        ("Сержант", "Верхние этажи, крепкие двери, лестницу можно перекрыть. Всегда держи второй выход."),
        ("Марина", "А торговый центр? Там же полно припасов."),
        ("Сержант", "Там полно стёкол и входов. И полно таких же умников, как ты. Выбирай место поменьше."),
    ]),
    ("ПРАВИЛО 5. КОМАНДА", "🤝", [
        ("Рассказчик", "В одиночку выжить почти невозможно. Кто-то должен спать, пока другой стоит на посту."),
        ("Сержант", "Дежурство по очереди. Условные сигналы. И правило: никто не уходит один."),
        ("Марина", "А если кого-то укусили?"),
        ("Сержант", "Тогда группа решает быстро и честно. Укус скрывать нельзя. Это вопрос жизни всех."),
    ]),
    ("ПРАВИЛО 6. ЗДОРОВЬЕ", "🩹", [
        ("Рассказчик", "В мире без больниц любая царапина может стать смертельной."),
        ("Сержант", "Промывай раны, меняй повязки, мой руки. Антисептик ценнее патронов."),
        ("Марина", "И высыпаться, наверное, тоже важно?"),
        ("Сержант", "Именно. Уставший человек делает ошибки. А ошибок тут не прощают."),
    ]),
    ("ПРАВИЛО 7. НЕ ТЕРЯЙ НАДЕЖДУ", "🌅", [
        ("Рассказчик", "Самое сильное оружие выжившего — не нож и не дубина. Это воля к жизни."),
        ("Сержант", "Ставь маленькие цели. Дожить до утра. Найти воду. Добраться до своих."),
        ("Марина", "Значит, мы справимся?"),
        ("Сержант", "Справимся. Если будем думать головой, а не бежать сломя её."),
    ]),
    ("ПОВТОРИМ", "📋", [
        ("Рассказчик", "Итак. Вода и еда. Тревожный рюкзак. Тишина. Надёжное укрытие. Команда. Здоровье. И надежда."),
        ("Марина", "Запомнила все семь!"),
        ("Сержант", "Молодец. А теперь — тихо. Слышишь? Уходим."),
        ("Рассказчик", "Берегите себя. И помните: лучше всего к апокалипсису готовится тот, кто готовится к обычным бедам."),
    ]),
]

# ---------------- звук ----------------
def tts(text, voice, path):
    if not os.path.exists(path):
        subprocess.run(["RHVoice-test", "-p", voice, "-o", path],
                       input=text.encode(), check=True)
    with wave.open(path) as w:
        sr, n = w.getframerate(), w.getnframes()
        data = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768
        if w.getnchannels() == 2:
            data = data.reshape(-1, 2).mean(1)
    if sr != SR:  # линейный ресемплинг
        x = np.linspace(0, len(data) - 1, int(len(data) * SR / sr))
        data = np.interp(x, np.arange(len(data)), data)
    return data

def ambient(n):
    """Мрачный эмбиент: низкий дрон + ветер."""
    t = np.arange(n) / SR
    drone = (np.sin(2*np.pi*55*t) + 0.6*np.sin(2*np.pi*82.4*t + 0.3*np.sin(2*np.pi*0.1*t))
             + 0.3*np.sin(2*np.pi*110.3*t))
    drone *= 0.5 + 0.5*np.sin(2*np.pi*0.05*t)
    rng = np.random.default_rng(1)
    noise = rng.standard_normal(n)
    k = 400
    wind = np.convolve(noise, np.ones(k)/k, mode="same") * 8
    wind *= 0.6 + 0.4*np.sin(2*np.pi*0.07*t + 1)
    return 0.035*drone + 0.03*wind

def growl(dur=1.4, seed=0):
    """Синтетическое рычание зомби."""
    rng = np.random.default_rng(seed)
    n = int(dur*SR); t = np.arange(n)/SR
    f = 70 + 25*np.sin(2*np.pi*3*t) + 10*rng.standard_normal(n).cumsum()/np.sqrt(n)*5
    phase = 2*np.pi*np.cumsum(f)/SR
    saw = 2*((phase/(2*np.pi)) % 1) - 1
    rough = saw * (0.6 + 0.4*np.sign(np.sin(2*np.pi*28*t)))
    noise = np.convolve(rng.standard_normal(n), np.ones(30)/30, "same")*3
    env = np.sin(np.pi*t/dur)**0.7
    return np.tanh(2*(rough*0.7 + noise*0.5)) * env * 0.18

# ---------------- картинка ----------------
_emoji_cache = {}
def emoji_img(ch, size):
    key = (ch, size)
    if key not in _emoji_cache:
        f = ImageFont.truetype(EMOJI, 109)
        im = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((0, 0), ch, font=f, embedded_color=True)
        im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
        _emoji_cache[key] = im
    return _emoji_cache[key]

def background(seed):
    rng = random.Random(seed)
    img = Image.new("RGB", (W, H), (12, 14, 12))
    d = ImageDraw.Draw(img)
    # градиент неба
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=(int(40 - 25*k), int(18 + 10*k), int(16 + 5*k)))
    # луна
    d.ellipse([980, 60, 1120, 200], fill=(200, 200, 170))
    # силуэт разрушенного города
    x = 0
    while x < W:
        bw = rng.randint(50, 130); bh = rng.randint(120, 330)
        d.rectangle([x, H - 150 - bh, x + bw, H], fill=(8, 8, 10))
        for wy in range(H - 140 - bh, H - 160, 28):
            for wx in range(x + 8, x + bw - 12, 22):
                if rng.random() < 0.08:
                    d.rectangle([wx, wy, wx + 8, wy + 12], fill=(170, 130, 50))
        x += bw + rng.randint(0, 12)
    img = img.filter(ImageFilter.GaussianBlur(2))
    # виньетка
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse([-200, -150, W + 200, H + 150], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(120))
    img = Image.composite(img, Image.new("RGB", (W, H), (0, 0, 0)), vig)
    return img

def frame(bg, title, emo, speaker, text, idx, total):
    img = bg.copy()
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.rounded_rectangle([40, 470, W - 40, 690], 22, fill=(0, 0, 0, 185))
    img = Image.alpha_composite(img.convert("RGBA"), ov)
    d = ImageDraw.Draw(img)
    # заголовок
    ft = ImageFont.truetype(FONT_B, 46)
    tw = d.textlength(title, font=ft)
    d.text(((W - tw)/2 + 3, 43), title, font=ft, fill=(0, 0, 0))
    d.text(((W - tw)/2, 40), title, font=ft, fill=(200, 40, 40))
    # эмодзи
    e = emoji_img(emo, 230)
    img.alpha_composite(e, ((W - 230)//2, 140))
    # говорящий
    name, (voice, col) = speaker, CAST[speaker]
    fn = ImageFont.truetype(FONT_B, 30)
    d.text((70, 490), name.upper(), font=fn, fill=col)
    # реплика
    fr = ImageFont.truetype(FONT_R, 31)
    y = 538
    for line in textwrap.wrap(text, 62)[:4]:
        d.text((70, y), line, font=fr, fill=(240, 240, 240))
        y += 40
    # прогресс
    d.rectangle([0, H - 6, int(W*idx/total), H], fill=(200, 40, 40))
    return img.convert("RGB")

# ---------------- сборка ----------------
def main():
    total_lines = sum(len(s[2]) for s in SCENES)
    pieces, concat, idx = [], [], 0
    gap = np.zeros(int(0.45*SR), np.float32)
    growls = []  # позиции (сэмпл) для рыка
    pos = 0
    for si, (title, emo, lines) in enumerate(SCENES):
        bg = background(si)
        for li, (who, text) in enumerate(lines):
            idx += 1
            lead = np.zeros(int((1.6 if li == 0 else 0.0)*SR), np.float32)
            if li == 0:
                growls.append(pos + int(0.1*SR))
            voice = tts(text, CAST[who][0], os.path.join(WORK, f"l{idx:03d}.wav"))
            seg = np.concatenate([lead, voice, gap])
            pieces.append(seg)
            pos += len(seg)
            png = os.path.join(WORK, f"f{idx:03d}.png")
            frame(bg, title, emo, who, text, idx, total_lines).save(png)
            concat.append((png, len(seg)/SR))
            print(f"[{idx}/{total_lines}] {who}: {text[:40]}...")
    tail = np.zeros(int(2.0*SR), np.float32)
    speech = np.concatenate(pieces + [tail])
    n = len(speech)
    mix = speech*0.95 + ambient(n)
    for k, p in enumerate(growls):
        g = growl(1.4, k)
        mix[p:p+len(g)] += g[:max(0, n-p)]
    g = growl(2.0, 99); mix[n-len(g)-int(0.3*SR):n-int(0.3*SR)] += g*1.3  # финальный рык
    mix = np.clip(mix / max(1.0, np.abs(mix).max()/0.95), -1, 1)
    wav = os.path.join(WORK, "audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix*32767).astype(np.int16).tobytes())
    concat[-1] = (concat[-1][0], concat[-1][1] + len(tail)/SR)
    lst = os.path.join(WORK, "list.txt")
    with open(lst, "w") as f:
        for png, dur in concat:
            f.write(f"file '{png}'\nduration {dur:.4f}\n")
        f.write(f"file '{concat[-1][0]}'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-i", wav, "-vf", "fps=25,format=yuv420p,fade=in:0:25",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                    "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", OUT],
                   check=True)
    print("Готово:", OUT)

if __name__ == "__main__":
    main()
