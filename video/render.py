#!/usr/bin/env python3
"""Рендер вертикального видео 1080x1920 с караоке-субтитрами.

Слово, которое сейчас произносится, загорается красным.
Использование:  python3 render.py audio.mp3 words.json out.mp4 story.json
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
# Текст, сцены и события задаются в story*.json (см. load_story).
PHRASES, SCENES, MAT = [], [], set()


def norm(s):
    return re.sub(r"[^а-яa-z]", "", s.lower().replace("ё", "е"))


def build(words, PHRASES, MAT):
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
BG.update({"attack": BG["bunker"], "shoot": grad((34, 40, 30), (6, 8, 6)), "outside": BG["zombie"],
           "store": grad((58, 52, 44), (12, 11, 10)), "nest": grad((16, 14, 14), (2, 2, 2)),
           "bunker_empty": BG["bunker"]})

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
    if kind in NEW_KINDS:
        return draw_new(img, kind, t, ts, ev)
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
    elif kind in ("bunker", "boom", "bunker_empty"):
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
        elif kind == "boom":
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


# ---------------------------------------------------------------- сцены 2-й серии
NEW_KINDS = {"attack", "shoot", "outside", "store", "nest"}
random.seed(11)
EYES = [(random.randint(60, W - 60), random.randint(420, 1180), random.uniform(.6, 1.3)) for _ in range(26)]
BUN_SLOTS = [(150 + k * 85, 690) for k in range(9)]


def _mask_overlay():
    y, x = np.mgrid[0:H, 0:W]
    inside = np.zeros((H, W), bool)
    for cx in (300, 780):
        inside |= (x - cx) ** 2 + ((y - 800) * 1.05) ** 2 < 400 ** 2
    al = np.where(inside, 0, 215).astype(np.uint8)
    ov = np.zeros((H, W, 4), np.uint8); ov[..., 3] = al
    im = Image.fromarray(ov, "RGBA").filter(ImageFilter.GaussianBlur(10))
    d = ImageDraw.Draw(im)
    for cx in (300, 780):
        d.ellipse([cx - 400, 800 - 381, cx + 400, 800 + 381], outline=(30, 30, 30, 255), width=26)
    return im


MASK_OV = None


def blood(d, x, y, t, s=1.0):
    random.seed(int(x * 7 + y))
    for k in range(10):
        dx, dy = random.uniform(-60, 60) * s, random.uniform(-40, 70) * s
        r = random.uniform(8, 22) * s
        d.ellipse([x + dx - r, y + dy - r, x + dx + r, y + dy + r], fill=(200, 0, 0, 230))
    d.rectangle([x - 6, y, x + 6, y + min(160, t * 200)], fill=(170, 0, 0, 220))


def eyes(d, x, y, s=1.0, a=255):
    for ex in (-18, 18):
        d.ellipse([x + ex * s - 9 * s, y - 7 * s, x + ex * s + 9 * s, y + 7 * s], fill=(255, 30, 20, a))


def gasmask(d, cx, cy, s):
    d.rounded_rectangle([cx - 170 * s, cy - 190 * s, cx + 170 * s, cy + 170 * s], 140 * s, fill=(70, 75, 70))
    for ex in (-80, 80):
        d.ellipse([cx + ex * s - 62 * s, cy - 110 * s, cx + ex * s + 62 * s, cy + 14 * s], fill=(30, 30, 30))
        d.ellipse([cx + ex * s - 46 * s, cy - 94 * s, cx + ex * s + 46 * s, cy - 2 * s], fill=(120, 170, 160))
    d.rounded_rectangle([cx - 70 * s, cy + 60 * s, cx + 70 * s, cy + 240 * s], 30 * s, fill=(50, 52, 50))
    for k in range(4):
        d.line([(cx - 55 * s, cy + (95 + k * 38) * s), (cx + 55 * s, cy + (95 + k * 38) * s)], fill=(30, 30, 30), width=int(8 * s))


def pistol(d, x, y, s=1.0, flash=0):
    d.polygon([(x, y), (x + 330 * s, y - 120 * s), (x + 360 * s, y - 60 * s), (x + 60 * s, y + 50 * s)], fill=(85, 85, 95), outline=(200, 200, 210))
    d.polygon([(x + 40 * s, y + 20 * s), (x + 120 * s, y - 10 * s), (x + 150 * s, y + 160 * s), (x + 70 * s, y + 190 * s)], fill=(60, 50, 45))
    d.polygon([(x + 120 * s, y + 160 * s), (x - 10 * s, y + 420 * s), (x + 130 * s, y + 420 * s), (x + 190 * s, y + 140 * s)], fill=(45, 45, 52), outline=(200, 200, 210))
    if flash:
        tx, ty = x + 360 * s, y - 95 * s
        pts = []
        for k in range(16):
            r = (110 if k % 2 == 0 else 40) * s * flash
            a = k / 16 * math.pi * 2
            pts.append((tx + math.cos(a) * r * 1.4, ty + math.sin(a) * r))
        d.polygon(pts, fill=(255, 220, 90))
        d.ellipse([tx - 30 * s, ty - 25 * s, tx + 30 * s, ty + 25 * s], fill=(255, 255, 230))


def draw_new(img, kind, t, ts, ev):
    global MASK_OV
    if kind in ("attack", "shoot", "nest"):
        draw_scene(img, "bunker_empty", t, ts, ev)
    elif kind == "outside":
        draw_scene(img, "zombie", t, ts, ev)
    d = ImageDraw.Draw(img, "RGBA")
    if kind == "attack":
        person(d, 300, 1220, 1.0, (6, 6, 6))
        bit = t >= ts["укус1"]
        person(d, 680, 1220, .95, (30, 45, 30) if bit and t > ts["укус1"] + .6 else (6, 6, 6))
        te = t - ts["выход"] + .4
        if te > 0:
            zx = max(860, W + 220 - te * 420)
            zombie(d, zx, 1225, 1.05, t * 5, (0, 0, 0))
        if bit:
            blood(d, 760, 960, t - ts["укус1"])
    elif kind == "shoot":
        tf = t - ts["падает"]
        if tf < 0:
            jit = math.sin(t * 31) * 6
            person(d, 640 + jit, 1220, 1.0, (35, 60, 35))
            eyes(d, 640 + jit, 975, 1.4)
            blood(d, 700, 1060, 2)
        else:
            k = min(1, tf / .35)
            ang = k * math.pi / 2
            cx, gy = 640, 1220
            hx, hy = cx + math.sin(ang) * 265, gy - math.cos(ang) * 265
            d.line([(cx, gy - 40), ((cx + hx) / 2, (gy - 40 + hy) / 2)], fill=(35, 60, 35), width=200)
            d.ellipse([hx - 62, hy - 62, hx + 62, hy + 62], fill=(35, 60, 35))
            if k == 1:
                d.ellipse([cx - 40, gy - 30, cx + 380, gy + 30], fill=(150, 0, 0, 200))
        tp = t - ts["пушку"]
        if tp > 0:
            sl = max(0, 1 - tp / .3)
            tsh = t - ts["выстрел"]
            fl = 1 - tsh / .18 if 0 <= tsh < .18 else 0
            rec = 25 * fl
            pistol(d, 120 - rec, 1130 + sl * 500 + rec, 1.0, fl)
    elif kind == "outside":
        bob = abs(math.sin(t * 9)) * 18
        person(d, 260, 1250 - bob, .85, (0, 0, 0))
        tm = t - ts["противогаз"]
        if tm > 0:
            gasmask(d, 260, 1250 - bob - 235, .3)
        tk = t - ts["убиваешь"]
        if 0 <= tk < .2:
            pistol(d, 300, 1030 - bob, .5, 1 - tk / .2)
        if tm > .9:
            if MASK_OV is None:
                MASK_OV = _mask_overlay()
            img.alpha_composite(MASK_OV)
            d = ImageDraw.Draw(img, "RGBA")
        if -.3 < tm < .9:
            p = min(1, (tm + .3) / .25)
            gasmask(d, W / 2, 700, 1.6 * p)
    elif kind == "store":
        d.rectangle([60, 360, 1020, 1200], fill=(40, 34, 28))
        for sy in (520, 760, 1000):
            d.rectangle([60, sy, 1020, sy + 22], fill=(110, 80, 50))
        random.seed(5)
        for sy in (520, 1000):
            x = 80
            while x < 990:
                w = random.randint(50, 90); h = random.randint(80, 140)
                d.rectangle([x, sy - h, x + w, sy], fill=random.choice([(180, 50, 40), (40, 110, 170), (220, 180, 60), (60, 140, 70), (200, 200, 200)]))
                x += w + 10
        taken = 0 if t < ts["булочек"] - .8 else min(9, int((t - ts["булочек"] + .8) / .15))
        for k, (bx, by) in enumerate(BUN_SLOTS):
            if k >= taken:
                d.ellipse([bx - 38, by - 40, bx + 38, by + 8], fill=(214, 150, 70))
                d.arc([bx - 24, by - 32, bx + 24, by - 4], 200, 340, fill=(250, 210, 140), width=5)
        d.rectangle([0, 1200, W, 1260], fill=(30, 28, 26))
        # ты
        tr = t - ts["бежишь2"]
        yx = 300 - max(0, tr) * 900
        if yx > -200:
            person(d, yx, 1230, 1.0, (6, 6, 6))
            for k in range(taken):  # булочки в руках
                bx, by = yx - 90 + (k % 3) * 60, 1100 - (k // 3) * 40
                d.ellipse([bx - 34, by - 26, bx + 34, by + 18], fill=(214, 150, 70), outline=(120, 70, 20), width=3)
        # Тимофей
        tt = t - ts["тимофей"]
        if tt > 0:
            a = min(1, tt / .4)
            bit = t >= ts["укус2"]
            tx = 760 + (1 - a) * 300
            person(d, tx, 1230, .95, (30, 50, 30) if bit and t > ts["укус2"] + .5 else (14, 10, 8))
            tw = F_TTL.getlength("ТИМОФЕЙ")
            d.rounded_rectangle([tx - tw / 2 - 24, 860, tx + tw / 2 + 24, 930], 35, fill=(255, 255, 255, int(235 * a)))
            d.text((tx, 895), "ТИМОФЕЙ", font=F_TTL, anchor="mm", fill=(20, 20, 20, int(255 * a)))
            tz = t - ts["укус2"] + .5
            if tz > 0:
                zombie(d, max(920, W + 200 - tz * 700), 1235, 1.0, t * 5, (0, 0, 0))
            if bit:
                blood(d, 830, 990, t - ts["укус2"])
    elif kind == "nest":
        d.rectangle([0, 0, W, H], fill=(0, 0, 0, 120))
        ty = t - ts["глаза"]
        if ty > 0:
            n = min(len(EYES), int(ty * 14) + 1)
            for k in range(n):
                ex, ey, sc = EYES[k]
                blink = 0 if math.sin(t * 3 + k * 1.7) > .97 else 255
                gl = 0.6 + 0.4 * math.sin(t * 4 + k)
                eyes(d, ex, ey, sc * 1.4, int(blink * gl))
        person(d, 540, 1260, 1.05, (0, 0, 0))


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
    # вспышки (взрыв, выстрел, укус)
    for t0, col, fd in FLASHES:
        tb = t - t0
        if 0 <= tb < fd:
            k = (1 - tb / fd) ** 2 * (0.75 if col != [255, 245, 220] else 1)
            arr = arr * (1 - k) + np.array(col) * k
    arr = arr * VIG + GRAIN[i % len(GRAIN)]
    # переход между сценами (затемнение)
    for s, *_ in SCENES[1:]:
        dt = abs(t - s)
        if dt < .25:
            arr *= .2 + .8 * dt / .25
    if t > ADUR - 1.0:
        arr *= max(0, (ADUR - t) / 1.0)
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
    if t > ADUR - 1.0:
        img = Image.fromarray((np.asarray(img.convert("RGB")) * max(0, (ADUR - t))).astype(np.uint8)).convert("RGBA")
    if OUTRO and t > ADUR:  # финальная надпись
        a = min(1, (t - ADUR) / .5)
        d = ImageDraw.Draw(img, "RGBA")
        f = ImageFont.truetype(FONT, 96)
        lines = OUTRO.split("\n")
        for li, ln in enumerate(lines):
            d.text((W / 2, H / 2 - (len(lines) - 1) * 60 + li * 120), ln, font=f, anchor="mm",
                   fill=(RED if li == len(lines) - 1 else (255, 255, 255)) + (int(255 * a),))
    return img.convert("RGB").tobytes()


class _TS(dict):  # нет такой метки — событие «никогда»
    def __missing__(self, k):
        return 1e9


def init(ph, ts, knocks, level, dur, adur, story):
    global PH, TS, KNOCKS, LEVEL, DUR, ADUR, SCENES, FLASHES, OUTRO
    PH, TS, KNOCKS, LEVEL, DUR, ADUR = ph, _TS(ts), knocks, level, dur, adur
    SCENES = [tuple(x) for x in story["scenes"]]
    FLASHES = story["_flashes"]; OUTRO = story.get("outro", "")


def times_of(flat, word, which):
    hits = [tk["s"] for tk in flat if norm(tk["t"]) == norm(word)]
    assert hits, word
    return hits if which == "all" else [hits[which]]


def load_story(path, words):
    """story.json: phrases, scenes [t, title, kind], mat, marks {имя: [слово, номер]},
    knocks [[слово, сила, номер|"all"]], flashes [[слово, номер|"all", [r,g,b], длит.]], outro."""
    st = json.load(open(path))
    ph = build(words, st["phrases"], set(st["mat"]))
    flat = [t for p in ph for t in p]
    ts = {name: times_of(flat, w, n)[0] for name, (w, n) in st.get("marks", {}).items()}
    knocks = [(t, amp) for w, amp, n in st.get("knocks", []) for t in times_of(flat, w, n)]
    st["_flashes"] = [(t, col, fd) for w, n, col, fd in st.get("flashes", []) for t in times_of(flat, w, n)]
    return st, ph, ts, knocks


def main():
    audio, wjson, out = sys.argv[1:4]
    story = sys.argv[4] if len(sys.argv) > 4 else "story1.json"
    words = json.load(open(wjson))
    st, ph, ts, knocks = load_story(story, words)
    # громкость голоса по кадрам
    pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", audio, "-ac", "1", "-ar", "16000",
                          "-f", "s16le", "-"], capture_output=True).stdout
    a = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    adur = len(a) / 16000
    dur = adur + (2.5 if st.get("outro") else 0)
    hop = 16000 // FPS
    lv = np.array([np.sqrt((a[j * hop:(j + 1) * hop] ** 2).mean() + 1e-9) for j in range(len(a) // hop)])
    lv = np.clip(lv / np.percentile(lv, 97), 0, 1).tolist() + [0.0] * int(3 * FPS)
    n = int(dur * FPS)
    enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", audio, "-af", "apad", "-t", f"{dur:.3f}",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "26", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out],
                           stdin=subprocess.PIPE)
    with Pool(4, init, (ph, ts, knocks, lv, dur, adur, st)) as pool:
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
