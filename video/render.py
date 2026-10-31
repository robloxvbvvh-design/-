#!/usr/bin/env python3
"""Рендер вертикального видео 1080x1920 с караоке-субтитрами.

Слово, которое сейчас произносится, загорается красным.
Использование:  python3 render.py audio.mp3 words.json out.mp4
words.json — таймкоды слов (из распознавания речи, см. asr.py).
"""
import json, math, random, subprocess, sys, re
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
FONT = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FONT_B = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
RED = (255, 38, 38)

# ---------------------------------------------------------------- текст
PHRASES = [
    "Обычный дневной день.", "Ты сидишь за компьютером.",
    "Кстати, тебя зовут Дима.", "И говоришь:", "«Сука, блять,",
    "идите на б… блядь, блять!»",
    "Ты продолжаешь играть,", "пока ты не слышишь,",
    "что начинается зомби-апокалипсис!", "Блядь, сука!",
    "Я был обычным человеком, сука!",
    "Ты бежишь к бункеру.", "И как убежал — никто не знает.",
    "Ты сидишь.", "Остались только консервы,", "пару банок питья…",
    "И слышен стук в бункер.",
    "К тебе приходит друг.", "— Это кто, блядь, сука?",
    "— Открывайте!", "Я твой друг!", "Откройте, пожалуйста!",
    "Вы сидите двое,", "и после этого слышите", "огромный взрыв.",
    "Вы боитесь.", "— Эй, Дима, к нам кто-то стучится!",
    "Похоже, зомби изобрели ядерку…", "Блядь, сука!",
    "И к вам кто-то стучится…",
]

SCENES = [  # (start, title, kind)
    (0.0, "ОБЫЧНЫЙ ДЕНЬ", "room"),
    (10.0, "ЗОМБИ-АПОКАЛИПСИС", "zombie"),
    (18.5, "БУНКЕР", "bunker"),
    (27.6, "ТУК-ТУК…", "door"),
    (34.2, "ВЗРЫВ", "boom"),
    (43.9, "КТО ТАМ?", "door2"),
]
MAT = {"сука", "блять", "блядь", "б"}


def norm(s):
    return re.sub(r"[^а-яa-z]", "", s.lower().replace("ё", "е"))


def build(words):
    """Сопоставляет красивый текст (с пунктуацией) с таймкодами распознавания."""
    phrases, k = [], 0
    for p in PHRASES:
        toks, raw = [], []
        for tok in p.split():  # одиночные «—» приклеиваем к соседнему слову
            if norm(tok):
                raw.append(tok)
            elif raw:
                raw[-1] += "\u00a0" + tok
            else:
                raw.append(tok + "\u00a0")
        for i in range(len(raw) - 1):
            if not norm(raw[i]):
                raw[i + 1] = raw[i] + raw[i + 1]; raw[i] = ""
        for tok in filter(None, raw):
            target, acc, s = norm(tok), "", None
            while acc != target:
                w = words[k]; k += 1
                s = w["s"] if s is None else s
                acc += norm(w["w"])
                assert target.startswith(acc), (tok, acc)
            toks.append({"t": tok, "s": s, "e": w["last"] + 0.12,
                         "mat": target in MAT})
        phrases.append(toks)
    assert k == len(words)
    flat = [t for p in phrases for t in p]
    for a, b in zip(flat, flat[1:]):
        a["end"] = min(b["s"], a["e"] + 0.35)
    flat[-1]["end"] = flat[-1]["e"] + 0.5
    for i, p in enumerate(phrases):
        nxt = phrases[i + 1][0]["s"] if i + 1 < len(phrases) else 99
        p_on, p_off = p[0]["s"] - 0.12, min(nxt - 0.12, p[-1]["e"] + 1.2)
        for t in p:
            t["on"], t["off"] = p_on, p_off
    return phrases


# ---------------------------------------------------------------- графика
def grad(top, bot, h=H):
    t = np.linspace(0, 1, h)[:, None]
    col = (np.array(top)[None, :] * (1 - t) + np.array(bot)[None, :] * t)
    return np.repeat(col[:, None, :], W, axis=1).astype(np.uint8)


def vignette():
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x - W / 2) / (W * .75)) ** 2 + ((y - H * .42) / (H * .62)) ** 2)
    return np.clip(1.15 - d ** 2 * .9, .25, 1)[..., None]


VIG = vignette()
RNG = np.random.default_rng(7)
GRAIN = [RNG.normal(0, 9, (H // 4, W // 4, 1)).repeat(4, 0).repeat(4, 1)
         for _ in range(6)]

BG = {
    "room": grad((14, 20, 40), (5, 6, 12)),
    "zombie": grad((120, 12, 10), (12, 2, 4)),
    "bunker": grad((38, 36, 32), (8, 8, 8)),
    "door": grad((30, 30, 34), (6, 6, 8)),
    "boom": grad((40, 14, 6), (6, 3, 2)),
}
BG["door2"] = BG["door"]

random.seed(3)
SKYLINE = []
x = -20
while x < W + 40:
    w = random.randint(60, 150); SKYLINE.append((x, w, random.randint(180, 520)))
    x += w + random.randint(-10, 8)
WINDOWS = [(bx + 12 + i * 26, 1150 - bh + 20 + j * 34) for bx, bw, bh in SKYLINE
           for i in range(max(1, (bw - 20) // 26)) for j in range(bh // 34 - 1)
           if random.random() < .18]
ASH = [(random.random() * W, random.random() * H, random.uniform(1.5, 4.5),
        random.uniform(40, 140)) for _ in range(140)]


def scene_at(t):
    cur = SCENES[0]
    for s in SCENES:
        if t >= s[0]:
            cur = s
    return cur


def zombie(d, cx, gy, s, ph, col=(10, 2, 3)):
    bob = math.sin(ph) * 8 * s
    hx, hy = cx, gy - 330 * s + bob
    d.ellipse([hx - 38 * s, hy - 44 * s, hx + 38 * s, hy + 40 * s], fill=col)
    d.polygon([(cx - 55 * s, gy - 280 * s + bob), (cx + 50 * s, gy - 280 * s + bob),
               (cx + 40 * s, gy - 120 * s), (cx - 45 * s, gy - 120 * s)], fill=col)
    for k in (-1, 1):  # руки вперёд
        ay = gy - 255 * s + bob + k * 22 * s + math.sin(ph * 1.3 + k) * 6 * s
        d.line([(cx - 30 * s, ay), (cx - 170 * s, ay - 12 * s)], fill=col,
               width=int(26 * s))
    sw = math.sin(ph) * 40 * s
    d.line([(cx - 20 * s, gy - 125 * s), (cx - 30 * s + sw, gy)], fill=col, width=int(34 * s))
    d.line([(cx + 20 * s, gy - 125 * s), (cx + 25 * s - sw, gy)], fill=col, width=int(34 * s))
    d.ellipse([hx - 24 * s, hy - 10 * s, hx - 10 * s, hy + 4 * s], fill=(255, 40, 30))


def person(d, cx, gy, s, col):
    d.ellipse([cx - 60 * s, gy - 330 * s, cx + 60 * s, gy - 200 * s], fill=col)
    d.rounded_rectangle([cx - 120 * s, gy - 200 * s, cx + 120 * s, gy], 70 * s, fill=col)


def draw_scene(img, kind, t, ts, ev):
    d = ImageDraw.Draw(img, "RGBA")
    if kind == "room":
        mat = ev["mat"]
        # окно со светом дня
        d.rectangle([90, 330, 400, 720], fill=(60, 110, 170)); d.rectangle([90, 330, 400, 720], outline=(25, 30, 45), width=18)
        d.line([(245, 330), (245, 720)], fill=(25, 30, 45), width=12)
        d.ellipse([300, 380, 370, 450], fill=(255, 230, 140))
        # стол и монитор
        d.rectangle([60, 1080, 1020, 1120], fill=(45, 32, 24))
        flick = .85 + .15 * math.sin(t * 37) * math.sin(t * 13)
        scr = (int(40 * flick), int(120 * flick), int(230 * flick)) if not mat else (int(230 * flick), 40, 40)
        glow = Image.new("RGBA", img.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
        gd.ellipse([250, 520, 1010, 1180], fill=scr + (90,))
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(70)))
        d = ImageDraw.Draw(img, "RGBA")
        d.rounded_rectangle([380, 600, 980, 960], 18, fill=(20, 20, 24))
        d.rectangle([405, 625, 955, 935], fill=scr)
        for i in range(9):  # «игра» / строчки на экране
            y = 645 + ((i * 34 + int(t * 60)) % 280)
            ln = 120 + (i * 97 % 300)
            d.rectangle([430, y, 430 + ln, y + 12], fill=(255, 255, 255, 70))
        d.rectangle([650, 960, 710, 1080], fill=(20, 20, 24)); d.rectangle([590, 1060, 770, 1082], fill=(20, 20, 24))
        sh = math.sin(t * 40) * 10 if mat else 0
        person(d, 470 + sh, 1250, 1.25, (8, 8, 12))
        if mat:  # облачко с ругательством
            d.rounded_rectangle([90, 760, 430, 920], 40, fill=(255, 255, 255))
            d.polygon([(330, 915), (390, 915), (420, 990)], fill=(255, 255, 255))
            f = ImageFont.truetype(FONT, 76)
            d.text((260, 840), "#@!%", font=f, fill=RED, anchor="mm")
    elif kind == "zombie":
        d.ellipse([650, 330, 930, 610], fill=(255, 190, 150, 230))
        for bx, bw, bh in SKYLINE:
            d.rectangle([bx, 1150 - bh, bx + bw, 1150], fill=(78, 12, 14))
        for wx, wy in WINDOWS:
            if math.sin(wx * 3.1 + wy + t * 2) > -.3:
                d.rectangle([wx, wy, wx + 12, wy + 16], fill=(255, 170, 60, 200))
        d.rectangle([0, 1150, W, 1260], fill=(40, 6, 8))
        tz = t - 10
        for i, (s, sp, off) in enumerate([(.9, 70, 0), (1.15, 95, 420), (.75, 55, 850), (1.3, 110, 1200)]):
            cx = W + 200 - ((tz * sp + off) % (W + 450))
            zombie(d, cx, 1240 + (s - 1) * 40, s, tz * 4 + i, (0, 0, 0))
    elif kind in ("bunker", "boom"):
        for y in range(380, 1250, 120):  # бетонные блоки
            for x in range(-60 * ((y // 120) % 2), W, 240):
                d.rectangle([x + 4, y + 4, x + 236, y + 116], outline=(0, 0, 0, 70), width=4)
        d.rectangle([0, 1180, W, 1260], fill=(18, 18, 18))
        # полка с консервами
        d.rectangle([120, 760, 560, 780], fill=(70, 50, 30))
        for i, cx in enumerate([170, 260, 350]):
            d.rounded_rectangle([cx - 38, 650, cx + 38, 760], 10, fill=(150, 150, 160))
            d.rectangle([cx - 38, 680, cx + 38, 730], fill=(180, 40, 30) if i != 1 else (40, 110, 60))
        for cx in (450, 520):  # бутылки
            d.rounded_rectangle([cx - 24, 640, cx + 24, 760], 12, fill=(80, 150, 200, 200))
            d.rectangle([cx - 9, 615, cx + 9, 645], fill=(80, 150, 200, 200))
        # качающаяся лампа
        ang = math.sin(t * 1.6) * .28 * (1 + 2 * ev["shake"])
        px, py, L = W // 2 + 170, 330, 300
        lx, ly = px + math.sin(ang) * L, py + math.cos(ang) * L
        cone = Image.new("RGBA", img.size, (0, 0, 0, 0)); cd = ImageDraw.Draw(cone)
        dx, dy = math.sin(ang), math.cos(ang); nx, ny = -dy, dx
        cd.polygon([(lx, ly), (lx + dx * 900 + nx * 380, ly + dy * 900 + ny * 380),
                    (lx + dx * 900 - nx * 380, ly + dy * 900 - ny * 380)], fill=(255, 210, 120, 60))
        img.alpha_composite(cone.filter(ImageFilter.GaussianBlur(25)))
        d = ImageDraw.Draw(img, "RGBA")
        d.line([(px, py), (lx, ly)], fill=(10, 10, 10), width=5)
        d.ellipse([lx - 26, ly - 10, lx + 26, ly + 38], fill=(255, 230, 160))
        if kind == "bunker":
            person(d, 760, 1220, 1.0, (6, 6, 6))
        else:
            person(d, 360, 1220, 1.0, (6, 6, 6)); person(d, 690, 1220, .92, (6, 6, 6))
            tb = t - ts["взрыв"]
            if tb > 0:  # ядерный гриб на заднем плане и вспышка
                g = min(1, tb / 2.5)
                cl = Image.new("RGBA", img.size, (0, 0, 0, 0)); c2 = ImageDraw.Draw(cl)
                c2.rectangle([W / 2 - 50 * g, 1180 - 520 * g, W / 2 + 50 * g, 1180], fill=(255, 120, 30, 160))
                for k in range(7):
                    a = k / 7 * math.pi * 2 + tb * .3
                    r = 150 * g
                    cx, cy = W / 2 + math.cos(a) * r * 1.4, 1180 - 560 * g + math.sin(a) * r * .5
                    c2.ellipse([cx - r, cy - r * .8, cx + r, cy + r * .8], fill=(255, 140 + k * 10, 40, 150))
                img.alpha_composite(cl.filter(ImageFilter.GaussianBlur(18)), (0, 0))
                img.alpha_composite(Image.new("RGBA", img.size, (0, 0, 0, 0)))
            ty = t - ts["ядерку"]
            if ty > 0:  # знак радиации
                d = ImageDraw.Draw(img, "RGBA")
                cx, cy, r = W / 2, 560, 150 * min(1, ty / .4)
                d.ellipse([cx - r - 20, cy - r - 20, cx + r + 20, cy + r + 20], fill=(255, 210, 0))
                for k in range(3):
                    a0 = math.degrees(ty * 1.5) + k * 120
                    d.pieslice([cx - r, cy - r, cx + r, cy + r], a0, a0 + 60, fill=(15, 15, 15))
                d.ellipse([cx - r * .28, cy - r * .28, cx + r * .28, cy + r * .28], fill=(255, 210, 0))
                d.ellipse([cx - r * .18, cy - r * .18, cx + r * .18, cy + r * .18], fill=(15, 15, 15))
    elif kind in ("door", "door2"):
        cx, cy, R = W / 2, 790, 380
        d.ellipse([cx - R - 30, cy - R - 30, cx + R + 30, cy + R + 30], fill=(20, 20, 22))
        d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(95, 98, 100))
        d.ellipse([cx - R + 40, cy - R + 40, cx + R - 40, cy + R - 40], outline=(60, 62, 64), width=16)
        for k in range(12):
            a = k / 12 * math.pi * 2
            bx, by = cx + math.cos(a) * (R - 20), cy + math.sin(a) * (R - 20)
            d.ellipse([bx - 12, by - 12, bx + 12, by + 12], fill=(55, 55, 58))
        wa = t * .4 + ev["shake"] * .5
        for k in range(3):
            a = wa + k * math.pi / 3
            d.line([(cx - math.cos(a) * 170, cy - math.sin(a) * 170), (cx + math.cos(a) * 170, cy + math.sin(a) * 170)],
                   fill=(150, 30, 25), width=26)
        d.ellipse([cx - 175, cy - 175, cx + 175, cy + 175], outline=(150, 30, 25), width=22)
        d.ellipse([cx - 40, cy - 40, cx + 40, cy + 40], fill=(150, 30, 25))
        d.rectangle([0, 1180, W, 1260], fill=(12, 12, 12))
        if ev["shake"] > .05:
            f = ImageFont.truetype(FONT, int(110 + 40 * ev["shake"]))
            d.text((cx + 260, 400), "ТУК!", font=f, fill=(255, 255, 255, int(255 * min(1, ev["shake"] * 1.5))),
                   anchor="mm", stroke_width=8, stroke_fill=(0, 0, 0))
            d.text((cx - 280, 1120), "ТУК!", font=f, fill=(255, 255, 255, int(255 * min(1, ev["shake"] * 1.5))),
                   anchor="mm", stroke_width=8, stroke_fill=(0, 0, 0))
        if kind == "door" and t > ts["открывайте"]:
            person(d, 200, 1240, .8, (5, 5, 5))
    # пепел / пыль
    if kind in ("zombie", "boom", "bunker"):
        for x0, y0, r, sp in ASH:
            y = (y0 + t * sp) % H; x = (x0 + math.sin(t + y0) * 30) % W
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 200, 180, 90) if kind != "bunker" else (220, 220, 200, 50))


# ---------------------------------------------------------------- субтитры
F_SUB = ImageFont.truetype(FONT, 84)
F_CUR = ImageFont.truetype(FONT, 98)
F_TTL = ImageFont.truetype(FONT_B, 46)


def layout(phrase, maxw=940):
    lines, cur, cw = [], [], 0
    sp = F_SUB.getlength(" ") * 1.2
    for tk in phrase:
        w = F_CUR.getlength(tk["t"])  # место под увеличенное слово
        if cur and cw + sp + w > maxw:
            lines.append((cur, cw)); cur, cw = [], 0
        cw += (sp if cur else 0) + w; cur.append((tk, w))
    lines.append((cur, cw))
    return lines, sp


def draw_subs(img, phrases, t):
    d = ImageDraw.Draw(img, "RGBA")
    for p in phrases:
        if not (p[0]["on"] <= t < p[0]["off"]):
            continue
        a_in = min(1, (t - p[0]["on"]) / .15); a_out = min(1, (p[0]["off"] - t) / .15)
        alpha = max(0, min(a_in, a_out))
        lines, sp = layout(p)
        lh = 122; y0 = 1480 - (len(lines) - 1) * lh / 2 + (1 - a_in) * 30
        cur_draw = None
        for li, (ln, _) in enumerate(lines):
            # реальные ширины: текущее слово крупнее, остальные — обычные
            ws = [F_CUR.getlength(tk["t"]) if tk["s"] <= t < tk["end"] else F_SUB.getlength(tk["t"])
                  for tk, _ in ln]
            sp0 = F_SUB.getlength(" ")
            lw = sum(ws) + sp0 * (len(ws) - 1)
            x = W / 2 - lw / 2; y = y0 + li * lh
            for (tk, _), w in zip(ln, ws):
                sp = sp0
                cx = x + w / 2
                if tk["s"] <= t < tk["end"]:
                    cur_draw = (tk, cx, y)
                else:
                    col = (255, 255, 255) if t >= tk["end"] else (255, 255, 255)
                    a = 255 if t >= tk["end"] else 130
                    d.text((cx, y), tk["t"], font=F_SUB, anchor="mm", fill=col + (int(a * alpha),),
                           stroke_width=7, stroke_fill=(0, 0, 0, int(230 * alpha)))
                x += w + sp
        if cur_draw:  # текущее слово — красное, крупнее, со свечением
            tk, cx, y = cur_draw
            pop = min(1, (t - tk["s"]) / .08)
            f = ImageFont.truetype(FONT, int(84 + 14 * pop))
            gl = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
            ImageDraw.Draw(gl).text((cx, 150), tk["t"], font=f, anchor="mm", fill=(255, 0, 0, 200))
            img.alpha_composite(gl.filter(ImageFilter.GaussianBlur(16)), (0, int(y - 150)))
            d = ImageDraw.Draw(img, "RGBA")
            d.text((cx, y), tk["t"], font=f, anchor="mm", fill=RED + (int(255 * alpha),),
                   stroke_width=8, stroke_fill=(0, 0, 0, int(255 * alpha)))


# ---------------------------------------------------------------- кадр
def render(i):
    t = i / FPS
    st, title, kind = scene_at(t)
    # тряска
    shake = 0
    for k, amp in KNOCKS:
        if 0 <= t - k < .45:
            shake = max(shake, amp * (1 - (t - k) / .45))
    flat_mat = any(tk["mat"] and tk["s"] <= t < tk["end"] for p in PH for tk in p)
    ev = {"shake": shake, "mat": flat_mat}
    base = Image.fromarray(BG[kind]).convert("RGBA")
    draw_scene(base, kind, t, TS, ev)
    arr = np.asarray(base.convert("RGB")).astype(np.float32)
    # вспышка взрыва
    tb = t - TS["взрыв"]
    if 0 <= tb < 1.6:
        k = (1 - tb / 1.6) ** 2
        arr = arr * (1 - k) + np.array([255, 245, 220]) * k
    arr = arr * VIG + GRAIN[i % len(GRAIN)]
    # переход между сценами (затемнение)
    for s, *_ in SCENES[1:]:
        dt = abs(t - s)
        if dt < .25:
            arr *= .2 + .8 * dt / .25
    if t > DUR - 1.0:
        arr *= max(0, (DUR - t) / 1.0)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    if shake > 0:
        dx, dy = int(math.sin(i * 2.7) * 28 * shake), int(math.cos(i * 3.3) * 28 * shake)
        img = Image.fromarray(np.roll(np.asarray(img), (dy, dx), (0, 1)))
    d = ImageDraw.Draw(img, "RGBA")
    # плашка сцены
    ta = min(1, (t - st) / .4)
    tw = F_TTL.getlength(title)
    d.rounded_rectangle([W / 2 - tw / 2 - 40, 150, W / 2 + tw / 2 + 40, 240], 45,
                        fill=(200, 20, 20, int(230 * ta)))
    d.text((W / 2, 195), title, font=F_TTL, anchor="mm", fill=(255, 255, 255, int(255 * ta)))
    # эквалайзер голоса
    lv = LEVEL[min(i, len(LEVEL) - 1)]
    for b in range(31):
        h = 8 + lv * 120 * (0.45 + 0.55 * abs(math.sin(b * 1.7 + t * 9)))
        x = W / 2 + (b - 15) * 26
        d.rounded_rectangle([x - 8, 1745 - h / 2, x + 8, 1745 + h / 2], 8,
                            fill=(255, 40, 40, 200) if abs(b - 15) < 4 else (255, 255, 255, 120))
    # прогресс
    d.rectangle([0, H - 14, W * t / DUR, H], fill=RED)
    draw_subs(img, PH, t)
    if t > DUR - 1.0:
        img = Image.fromarray((np.asarray(img.convert("RGB")) * max(0, (DUR - t))).astype(np.uint8))
    return img.convert("RGB").tobytes()


def init(ph, ts, knocks, level, dur):
    global PH, TS, KNOCKS, LEVEL, DUR
    PH, TS, KNOCKS, LEVEL, DUR = ph, ts, knocks, level, dur


def main():
    audio, wjson, out = sys.argv[1:4]
    words = json.load(open(wjson))
    ph = build(words)
    flat = [t for p in ph for t in p]
    ts = {}
    for tk in flat:
        ts.setdefault(norm(tk["t"]), tk["s"])
    knocks = [(ts["стук"], 1.0), (ts["открывайте"], .8), (ts["откройте"], .7),
              (ts["взрыв"], 1.4), (ts["ядерку"], .5)]
    knocks += [(tk["s"], .9) for tk in flat if norm(tk["t"]) == "стучится"]
    # громкость голоса по кадрам
    pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", audio, "-ac", "1", "-ar", "16000",
                          "-f", "s16le", "-"], capture_output=True).stdout
    a = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    dur = len(a) / 16000
    hop = 16000 // FPS
    lv = np.array([np.sqrt((a[j * hop:(j + 1) * hop] ** 2).mean() + 1e-9) for j in range(len(a) // hop)])
    lv = np.clip(lv / np.percentile(lv, 97), 0, 1).tolist()
    n = int(dur * FPS)
    enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", audio,
                            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                           stdin=subprocess.PIPE)
    with Pool(4, init, (ph, ts, knocks, lv, dur)) as pool:
        for j, fr in enumerate(pool.imap(render, range(n), chunksize=4)):
            enc.stdin.write(fr)
            if j % 150 == 0:
                print(f"{j}/{n}", flush=True)
    enc.stdin.close(); enc.wait()
    # субтитры .srt рядом
    def ft(x):
        return f"{int(x // 3600):02}:{int(x % 3600 // 60):02}:{int(x % 60):02},{int(x * 1000 % 1000):03}"
    with open(out.rsplit(".", 1)[0] + ".srt", "w") as f:
        for k, p in enumerate(ph, 1):
            f.write(f"{k}\n{ft(p[0]['s'])} --> {ft(p[-1]['e'])}\n{' '.join(t['t'] for t in p)}\n\n")


if __name__ == "__main__":
    main()
