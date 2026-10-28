#!/usr/bin/env python3
"""Рендер мультяшных вертикальных роликов (стиль «Жора и Макс») из JSON-сценария.

Использование:
    python3 render.py scenario.json -o out.mp4 [--stills DIR] [--audio voice.mp3] [--fps 30]

Каждая сцена: фон, персонажи (zhora / max), плашка-«бейдж» сверху,
предметы (props), крупные надписи (labels) и субтитр (caption).
Всё анимируется: персонажи покачиваются, предметы «выпрыгивают»,
между сценами — плавный переход, под каждое появление — звук «поп».
"""
import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 720, 1280
SS = 2  # суперсэмплинг для гладких контуров
OUT = (29, 29, 43)
SKIN = (246, 196, 140)
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

PALETTE = {
    "blue": ((150, 185, 245), (75, 120, 220)),
    "orange": ((252, 214, 160), (240, 140, 60)),
    "green": ((180, 230, 180), (70, 160, 90)),
    "purple": ((205, 185, 245), (120, 90, 210)),
    "red": ((250, 180, 170), (215, 70, 60)),
}
LABEL_COLORS = {
    "white": (255, 255, 255),
    "green": (90, 210, 110),
    "red": (235, 70, 60),
    "pink": (250, 120, 130),
    "yellow": (255, 210, 31),
    "blue": (90, 150, 255),
}
BADGE_ACCENT = {"blue": (60, 110, 230), "orange": (240, 130, 30), "green": (40, 160, 80), "red": (220, 60, 60)}

_font_cache = {}


def font(size):
    key = int(size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(FONT_BOLD, key)
    return _font_cache[key]


def ease_out_back(x):
    x = max(0.0, min(1.0, x))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def sprite(w, h, fn):
    """Рисует спрайт w×h с суперсэмплингом: fn(draw, k) где k — множитель координат."""
    im = Image.new("RGBA", (int(w * SS), int(h * SS)), (0, 0, 0, 0))
    fn(ImageDraw.Draw(im), SS)
    return im.resize((max(1, int(w)), max(1, int(h))), Image.LANCZOS)


# ---------------------------------------------------------------- фоны
def make_background(kind):
    bg = Image.new("RGB", (W, H))
    arr = np.zeros((H, W, 3), dtype=np.float32)
    ys = np.linspace(0, 1, H)[:, None]

    def grad(top, bot, y0, y1):
        t = np.linspace(0, 1, y1 - y0)[:, None]
        for c in range(3):
            arr[y0:y1, :, c] = top[c] + (bot[c] - top[c]) * t

    if kind == "split":
        grad(*PALETTE["blue"], 0, H // 2)
        grad(*PALETTE["orange"], H // 2, H)
    else:
        top, bot = PALETTE.get(kind, PALETTE["blue"])
        grad(top, bot, 0, H)
    _ = ys
    bg = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(bg, "RGBA")
    for y in range(20, H, 40):
        for x in range(20 + (y // 40 % 2) * 20, W, 40):
            d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(0, 0, 0, 22))
    if kind == "split":
        d.rectangle((0, H // 2 - 9, W, H // 2 + 9), fill=(255, 255, 255))
        d.line((0, H // 2 - 9, W, H // 2 - 9), fill=OUT, width=3)
        d.line((0, H // 2 + 9, W, H // 2 + 9), fill=OUT, width=3)
    return bg


# ---------------------------------------------------------------- персонажи
def _limb(d, a, b, color, w, k):
    d.line([(a[0] * k, a[1] * k), (b[0] * k, b[1] * k)], fill=OUT, width=int((w + 8) * k))
    for p in (a, b):
        r = (w + 8) / 2
        d.ellipse(((p[0] - r) * k, (p[1] - r) * k, (p[0] + r) * k, (p[1] + r) * k), fill=OUT)
    d.line([(a[0] * k, a[1] * k), (b[0] * k, b[1] * k)], fill=color, width=int(w * k))
    for p in (a, b):
        r = w / 2
        d.ellipse(((p[0] - r) * k, (p[1] - r) * k, (p[0] + r) * k, (p[1] + r) * k), fill=color)


def _circ(d, cx, cy, r, fill, k, w=4):
    d.ellipse(((cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k), fill=fill, outline=OUT, width=int(w * k))


def _rect(d, box, fill, k, r=10, w=4):
    d.rounded_rectangle([v * k for v in box], radius=r * k, fill=fill, outline=OUT, width=int(w * k))


def _poly(d, pts, fill, k, w=4):
    d.polygon([(x * k, y * k) for x, y in pts], fill=fill, outline=OUT, width=int(w * k))


def _face(d, hx, hy, r, mood, k):
    ex = 0.38 * r
    ey = hy - 0.05 * r
    er = 0.27 * r
    for sx in (-1, 1):
        _circ(d, hx + sx * ex, ey, er, (255, 255, 255), k, 4)
        px = hx + sx * ex + 0.06 * r
        pr = 0.12 * r if mood != "shocked" else 0.08 * r
        d.ellipse(((px - pr) * k, (ey - pr) * k, (px + pr) * k, (ey + pr) * k), fill=OUT)
        d.ellipse(((px + pr * 0.2) * k, (ey - pr * 0.7) * k, (px + pr * 0.7) * k, (ey - pr * 0.2) * k), fill=(255, 255, 255))
        bx, by = hx + sx * 0.62 * r, hy + 0.3 * r
        d.ellipse(((bx - 0.17 * r) * k, (by - 0.08 * r) * k, (bx + 0.17 * r) * k, (by + 0.08 * r) * k), fill=(244, 160, 150))
    # брови
    if mood in ("angry", "sad"):
        for sx in (-1, 1):
            inner = (hx + sx * 0.15 * r, ey - er - (0.02 if mood == "angry" else 0.14) * r)
            outer = (hx + sx * 0.62 * r, ey - er - (0.16 if mood == "angry" else 0.0) * r)
            d.line([(inner[0] * k, inner[1] * k), (outer[0] * k, outer[1] * k)], fill=OUT, width=int(7 * k))
    # нос
    d.arc(((hx - 0.08 * r) * k, (hy + 0.12 * r) * k, (hx + 0.1 * r) * k, (hy + 0.3 * r) * k), 270, 110, fill=OUT, width=int(4 * k))
    my = hy + 0.5 * r
    if mood == "happy":
        box = ((hx - 0.38 * r) * k, (my - 0.22 * r) * k, (hx + 0.38 * r) * k, (my + 0.42 * r) * k)
        d.chord(box, 0, 180, fill=(120, 30, 40), outline=OUT, width=int(4 * k))
        d.chord(((hx - 0.2 * r) * k, (my + 0.05 * r) * k, (hx + 0.24 * r) * k, (my + 0.4 * r) * k), 0, 180, fill=(245, 120, 140))
        d.arc(box, 0, 180, fill=OUT, width=int(4 * k))
    elif mood == "sad":
        d.arc(((hx - 0.25 * r) * k, (my - 0.02 * r) * k, (hx + 0.25 * r) * k, (my + 0.3 * r) * k), 200, 340, fill=OUT, width=int(5 * k))
    elif mood == "shocked":
        _circ(d, hx, my + 0.08 * r, 0.14 * r, (120, 30, 40), k, 4)
    elif mood == "angry":
        d.line([((hx - 0.2 * r) * k, (my + 0.08 * r) * k), ((hx + 0.2 * r) * k, (my + 0.08 * r) * k)], fill=OUT, width=int(5 * k))
    else:
        d.arc(((hx - 0.25 * r) * k, (my - 0.25 * r) * k, (hx + 0.25 * r) * k, (my + 0.12 * r) * k), 25, 155, fill=OUT, width=int(5 * k))


POSES = {
    # (левая кисть, правая кисть) в локальных координатах 400×720
    "idle": ((70, 470), (330, 470)),
    "wave": ((80, 470), (330, 100)),
    "phone": ((70, 480), (290, 290)),
    "laptop": ((150, 420), (250, 420)),
    "fists": ((145, 330), (265, 330)),
    "passport": ((115, 430), (330, 470)),
    "point": ((70, 470), (380, 260)),
}


def _held(d, prop, lh, rh, k):
    if prop == "phone":
        _rect(d, (rh[0] + 2, rh[1] - 70, rh[0] + 40, rh[1] + 5), (90, 170, 250), k, 8)
    elif prop == "laptop":
        _poly(d, [(110, 380), (300, 360), (320, 445), (130, 470)], (190, 196, 206), k)
        _circ(d, 215, 415, 20, (240, 240, 245), k, 3)
    elif prop == "passport":
        _rect(d, (lh[0] - 50, lh[1] - 60, lh[0] + 40, lh[1] + 50), (40, 40, 48), k, 8)
        d.rectangle(((lh[0] - 30) * k, (lh[1] - 45) * k, (lh[0] + 25) * k, (lh[1] - 37) * k), fill=(255, 210, 31))
        _circ(d, lh[0] - 5, lh[1] + 5, 18, (40, 40, 48), k, 5)
    elif prop == "money":
        _rect(d, (rh[0] - 10, rh[1] - 75, rh[0] + 75, rh[1] - 25), (110, 200, 110), k, 6)
        d.text(((rh[0] + 32) * k, (rh[1] - 50) * k), "₽", font=font(30 * k), fill=(30, 110, 50), anchor="mm")


def draw_character(who, mood="neutral", pose="idle", prop=None, scale=1.0):
    lh, rh = POSES.get(pose, POSES["idle"])

    def fn(d, k):
        k = k * scale
        if who == "zhora":
            # ноги + кроссовки
            for x0 in (125, 205):
                _rect(d, (x0, 470, x0 + 72, 650), (30, 30, 36), k, 8)
                d.line([((x0 + 18) * k, 480 * k), ((x0 + 18) * k, 640 * k)], fill=(250, 250, 250), width=int(5 * k))
                d.line([((x0 + 54) * k, 480 * k), ((x0 + 54) * k, 640 * k)], fill=(250, 250, 250), width=int(5 * k))
                _rect(d, (x0 - 12, 635, x0 + 84, 680), (60, 62, 70), k, 20)
                d.arc(((x0 + 15) * k, 645 * k, (x0 + 60) * k, 690 * k), 200, 300, fill=(240, 240, 240), width=int(5 * k))
            # живот
            d.ellipse((92 * k, 300 * k, 308 * k, 520 * k), fill=SKIN, outline=OUT, width=int(4 * k))
            _circ(d, 200, 470, 9, (225, 160, 110), k, 3)
            # футболка
            _rect(d, (95, 245, 305, 430), (88, 90, 98), k, 40)
            d.ellipse((150 * k, 300 * k, 205 * k, 360 * k), fill=(110, 112, 120))
            if pose not in ("laptop", "fists"):
                _rect(d, (125, 465, 275, 490), (30, 30, 36), k, 6)
            # руки
            for sh, hand in (((95, 280), lh), ((305, 280), rh)):
                _limb(d, sh, hand, SKIN, 34, k)
                _circ(d, sh[0], sh[1], 34, (88, 90, 98), k)
                _circ(d, hand[0], hand[1], 24, SKIN, k)
            if prop:
                _held(d, prop, lh, rh, k)
                for hand in (lh, rh):
                    _circ(d, hand[0], hand[1], 24, SKIN, k)
            # голова
            hx, hy, r = 200, 150, 105
            for sx in (-1, 1):
                _circ(d, hx + sx * r, hy + 10, 20, SKIN, k)
            _circ(d, hx, hy, r, SKIN, k)
            hair = [(98, 140), (102, 85), (82, 80), (118, 60), (112, 30), (150, 45), (160, 12), (192, 40),
                    (218, 8), (240, 42), (275, 22), (275, 58), (312, 62), (298, 92), (306, 140),
                    (285, 100), (250, 88), (215, 98), (175, 84), (135, 100)]
            _poly(d, hair, (140, 90, 50), k)
            _face(d, hx, hy + 10, r, mood, k)
        else:  # max
            for x0 in (140, 207):
                _rect(d, (x0, 450, x0 + 55, 650), (40, 80, 170), k, 6)
                _rect(d, (x0 - 18, 630, x0 + 72, 680), (250, 250, 250), k, 22)
                d.line([((x0 + 2) * k, 655 * k), ((x0 + 48) * k, 650 * k)], fill=(225, 60, 60), width=int(7 * k))
            _rect(d, (112, 255, 288, 480), (245, 135, 35), k, 30)
            _rect(d, (130, 410, 270, 470), (225, 115, 25), k, 12)
            for x in (180, 220):
                d.line([(x * k, 270 * k), (x * k, 330 * k)], fill=(250, 250, 250), width=int(5 * k))
            for sh, hand in (((122, 280), lh), ((278, 280), rh)):
                _limb(d, sh, hand, (245, 135, 35), 40, k)
                _circ(d, hand[0], hand[1], 24, SKIN, k)
            if prop:
                _held(d, prop, lh, rh, k)
                for hand in (lh, rh):
                    _circ(d, hand[0], hand[1], 24, SKIN, k)
            hx, hy, r = 200, 175, 95
            for sx in (-1, 1):
                _circ(d, hx + sx * r, hy + 10, 18, SKIN, k)
            _circ(d, hx, hy, r, SKIN, k)
            _poly(d, [(108, 150), (120, 120), (290, 120), (296, 150), (270, 135), (240, 150), (210, 132),
                      (180, 150), (150, 132), (125, 155)], (140, 90, 50), k)
            # кепка
            d.pieslice((100 * k, 55 * k, 300 * k, 205 * k), 180, 360, fill=(225, 55, 50), outline=OUT, width=int(4 * k))
            _poly(d, [(265, 125), (355, 132), (350, 152), (260, 140)], (200, 40, 40), k)
            _circ(d, 200, 58, 13, (255, 255, 255), k, 3)
            _face(d, hx, hy + 12, r, mood, k)

    return sprite(400 * scale, 720 * scale, fn)


# ---------------------------------------------------------------- предметы
def draw_prop(p):
    t = p.get("type")
    w = p.get("w", 220)
    text = p.get("text", "")

    def txt(d, x, y, s, size, fill=OUT, stroke=0, sc=(255, 255, 255)):
        d.text((x * s, y * s), text if text else "", font=font(size * s), fill=fill, anchor="mm",
               stroke_width=int(stroke * s), stroke_fill=sc)

    if t == "card":
        h = w * 0.62
        def fn(d, s):
            _rect(d, (4, 4, w - 4, h - 4), (140, 110, 240), s, 22, 6)
            d.rectangle((6 * s, h * 0.22 * s, (w - 6) * s, h * 0.38 * s), fill=OUT)
            _rect(d, (w * 0.1, h * 0.55, w * 0.32, h * 0.75), (255, 210, 31), s, 6, 4)
            txt(d, w * 0.6, h * 0.72, s, w * 0.13, (255, 255, 255), 3, OUT)
    elif t == "food":
        h = w
        def fn(d, s):
            _rect(d, (6, 6, w - 6, h - 6), (205, 150, 90), s, 6, 6)
            _circ(d, w / 2, h / 2, w * 0.27, (220, 50, 50), s, 5)
            d.text((w / 2 * s, h / 2 * s), text or "FOOD", font=font(w * 0.12 * s), fill=(255, 255, 255), anchor="mm")
    elif t == "doc_x":
        h = w * 1.05
        def fn(d, s):
            _rect(d, (6, 6, w - 6, h - 6), (255, 255, 255), s, 12, 6)
            txt(d, w / 2, h * 0.14, s, w * 0.12)
            for i in range(4):
                y0 = h * (0.27 + i * 0.16)
                _rect(d, (w * 0.12, y0, w * 0.88, y0 + h * 0.1), (225, 228, 235), s, 10, 4)
            if p.get("cross", True):
                for a, b in (((0.15, 0.3), (0.85, 0.8)), ((0.85, 0.3), (0.15, 0.8))):
                    d.line([(w * a[0] * s, h * a[1] * s), (w * b[0] * s, h * b[1] * s)], fill=(235, 80, 70), width=int(w * 0.07 * s))
    elif t == "table":
        h = w * 0.78
        def fn(d, s):
            _rect(d, (6, 6, w - 6, h - 6), (255, 255, 255), s, 10, 7)
            d.rectangle((9 * s, 9 * s, (w - 9) * s, h * 0.2 * s), fill=(40, 150, 80))
            txt(d, w / 2, h * 0.11, s, w * 0.11, (255, 255, 255))
            for i in range(1, 5):
                y = h * (0.2 + i * 0.16)
                d.line([(6 * s, y * s), ((w - 6) * s, y * s)], fill=OUT, width=int(6 * s))
            for x in (0.4, 0.75):
                d.line([(w * x * s, h * 0.2 * s), (w * x * s, (h - 6) * s)], fill=OUT, width=int(6 * s))
    elif t == "shield":
        h = w * 1.15
        def fn(d, s):
            _poly(d, [(w / 2, 6), (w - 6, h * 0.16), (w - 12, h * 0.55), (w / 2, h - 6), (12, h * 0.55), (6, h * 0.16)], (40, 150, 80), s, 6)
            d.line([(w * 0.28 * s, h * 0.48 * s), (w * 0.45 * s, h * 0.64 * s), (w * 0.74 * s, h * 0.32 * s)],
                   fill=(255, 255, 255), width=int(w * 0.1 * s), joint="curve")
    elif t == "cloud":
        h = w * 0.9
        def fn(d, s):
            _poly(d, [(w * 0.52, h * 0.5), (w * 0.38, h * 0.78), (w * 0.5, h * 0.76), (w * 0.42, h * 0.98),
                      (w * 0.66, h * 0.66), (w * 0.53, h * 0.68), (w * 0.62, h * 0.5)], (255, 200, 30), s, 4)
            for cx, cy, r in ((0.3, 0.42, 0.2), (0.52, 0.3, 0.26), (0.74, 0.44, 0.2)):
                _circ(d, w * cx, h * cy, w * r, (128, 132, 145), s, 6)
            d.rounded_rectangle((w * 0.12 * s, h * 0.42 * s, w * 0.88 * s, h * 0.6 * s), radius=h * 0.09 * s,
                                fill=(128, 132, 145), outline=OUT, width=int(6 * s))
            for cx, cy, r in ((0.3, 0.42, 0.17), (0.52, 0.3, 0.23), (0.74, 0.44, 0.17)):
                d.ellipse((w * (cx - r) * s, h * cy * s - w * r * s, w * (cx + r) * s, h * cy * s + w * r * s), fill=(128, 132, 145))
            d.rectangle((w * 0.16 * s, h * 0.4 * s, w * 0.84 * s, h * 0.55 * s), fill=(128, 132, 145))
    elif t == "briefcase":
        h = w * 0.85
        def fn(d, s):
            _rect(d, (w * 0.32, h * 0.04, w * 0.68, h * 0.28), None, s, 18, 9)
            _rect(d, (6, h * 0.2, w - 6, h - 6), (40, 150, 80), s, 18, 6)
            _rect(d, (w * 0.44, h * 0.38, w * 0.56, h * 0.52), (255, 210, 31), s, 4, 4)
            txt(d, w / 2, h * 0.75, s, w * 0.12, (255, 255, 255))
            if p.get("check", True):
                _circ(d, w * 0.86, h * 0.16, w * 0.13, (40, 150, 80), s, 5)
                d.line([(w * 0.8 * s, h * 0.16 * s), (w * 0.85 * s, h * 0.22 * s), (w * 0.93 * s, h * 0.1 * s)],
                       fill=(255, 255, 255), width=int(w * 0.035 * s), joint="curve")
    elif t in ("arrow_up", "arrow_down"):
        h = w * 1.2
        col = (40, 150, 80) if t == "arrow_up" else (225, 60, 55)
        def fn(d, s):
            pts = [(w / 2, 6), (w - 6, h * 0.45), (w * 0.68, h * 0.45), (w * 0.68, h - 6), (w * 0.32, h - 6), (w * 0.32, h * 0.45), (6, h * 0.45)]
            if t == "arrow_down":
                pts = [(x, h - y) for x, y in pts]
            _poly(d, pts, col, s, 6)
    elif t == "coins":
        h = w
        def fn(d, s):
            for i in range(5):
                y = h * 0.82 - i * h * 0.13
                d.ellipse((w * 0.12 * s, (y - h * 0.08) * s, w * 0.88 * s, (y + h * 0.1) * s), fill=(220, 160, 20), outline=OUT, width=int(5 * s))
                d.ellipse((w * 0.12 * s, (y - h * 0.12) * s, w * 0.88 * s, (y + h * 0.06) * s), fill=(255, 205, 50), outline=OUT, width=int(5 * s))
            d.text((w / 2 * s, (h * 0.82 - 4 * h * 0.13 - h * 0.03) * s), "₽", font=font(w * 0.13 * s), fill=(180, 120, 10), anchor="mm")
    elif t == "piggy":
        h = w * 0.85
        def fn(d, s):
            for lx in (0.3, 0.62):
                _rect(d, (w * lx, h * 0.7, w * (lx + 0.12), h * 0.95), (245, 150, 175), s, 6, 5)
            _poly(d, [(w * 0.62, h * 0.22), (w * 0.7, h * 0.02), (w * 0.78, h * 0.26)], (245, 150, 175), s, 5)
            d.ellipse((w * 0.08 * s, h * 0.15 * s, w * 0.88 * s, h * 0.85 * s), fill=(250, 170, 190), outline=OUT, width=int(6 * s))
            _rect(d, (w * 0.84, h * 0.38, w * 0.98, h * 0.6), (245, 150, 175), s, 12, 5)
            for ny in (0.45, 0.53):
                d.ellipse((w * 0.89 * s, h * ny * s, w * 0.92 * s, (h * ny + w * 0.03) * s), fill=OUT)
            _circ(d, w * 0.7, h * 0.38, w * 0.035, OUT, s, 0)
            d.rounded_rectangle((w * 0.38 * s, h * 0.2 * s, w * 0.6 * s, h * 0.26 * s), radius=6 * s, fill=OUT)
    elif t == "calendar":
        h = w
        def fn(d, s):
            _rect(d, (6, h * 0.1, w - 6, h - 6), (255, 255, 255), s, 14, 6)
            d.rounded_rectangle((9 * s, h * 0.12 * s, (w - 9) * s, h * 0.32 * s), radius=10 * s, fill=(225, 60, 55))
            for x in (0.3, 0.7):
                _rect(d, (w * x - 8, 4, w * x + 8, h * 0.2), (90, 90, 100), s, 6, 4)
            d.text((w / 2 * s, h * 0.65 * s), text or "30", font=font(w * 0.32 * s), fill=OUT, anchor="mm")
    else:
        raise ValueError(f"неизвестный тип предмета: {t}")
    return sprite(w, h, fn)


def draw_label(text, size=64, color="white"):
    f = font(size * SS)
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    stroke = max(4, size // 9)
    l, t, r, b = tmp.textbbox((0, 0), text, font=f, stroke_width=stroke * SS)
    w, h = (r - l) // SS + 16, (b - t) // SS + 20

    def fn(d, s):
        d.text((w / 2 * s + 5 * s, h / 2 * s + 6 * s), text, font=f, fill=OUT, anchor="mm", stroke_width=stroke * s, stroke_fill=OUT)
        d.text((w / 2 * s, h / 2 * s), text, font=f, fill=LABEL_COLORS.get(color, color if isinstance(color, tuple) else (255, 255, 255)),
               anchor="mm", stroke_width=stroke * s, stroke_fill=OUT)
    return sprite(w, h, fn)


def draw_badge(b):
    w, h = 420, 84
    accent = BADGE_ACCENT.get(b.get("color", "blue"), (60, 110, 230))
    vcol = LABEL_COLORS.get(b.get("value_color", "white"), (255, 255, 255))

    def fn(d, s):
        d.rounded_rectangle((3 * s, 3 * s, (w - 3) * s, (h - 3) * s), radius=h / 2 * s, fill=(40, 42, 55), outline=accent, width=int(6 * s))
        cx = h / 2 + 4
        d.ellipse(((cx - 30) * s, (h / 2 - 30) * s, (cx + 30) * s, (h / 2 + 30) * s), fill=accent)
        d.text((cx * s, h / 2 * s), b.get("letter", "Ж"), font=font(34 * s), fill=(255, 255, 255), anchor="mm")
        d.text((92 * s, 28 * s), b.get("label", ""), font=font(17 * s), fill=(215, 218, 230), anchor="lm")
        val, vs = b.get("value", ""), 34
        while vs > 16 and d.textlength(val, font=font(vs * s)) > (w - 110) * s:
            vs -= 2
        d.text((92 * s, 56 * s), val, font=font(vs * s), fill=vcol, anchor="lm")
        d.line(((w - 110) * s, 26 * s, (w - 60) * s, 26 * s), fill=(255, 255, 255), width=int(4 * s))
    return sprite(w, h, fn)


def draw_caption(text, size=46, max_w=640):
    """Субтитр: *слово* — выделение жёлтым."""
    words = [(w.strip("*"), w.startswith("*")) for w in text.split()]
    f = font(size * SS)
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    space = tmp.textlength(" ", font=f)
    lines, cur, cur_w = [], [], 0
    for wd, hl in words:
        ww = tmp.textlength(wd, font=f)
        if cur and cur_w + space + ww > max_w * SS:
            lines.append((cur, cur_w))
            cur, cur_w = [], 0
        cur_w += (space if cur else 0) + ww
        cur.append((wd, hl, ww))
    if cur:
        lines.append((cur, cur_w))
    lh = size * 1.15
    w, h = max_w + 40, int(lh * len(lines) + 30)
    stroke = max(4, size // 9)

    def fn(d, s):
        y = 15 + lh / 2
        for ln, lw in lines:
            x = (w * s - lw) / 2
            for wd, hl, ww in ln:
                d.text((x, y * s), wd, font=f, anchor="lm", fill=(255, 210, 31) if hl else (255, 255, 255),
                       stroke_width=stroke * s, stroke_fill=OUT)
                x += ww + space
            y += lh
    return sprite(w, h, fn)


# ---------------------------------------------------------------- сцены
class Scene:
    def __init__(self, cfg):
        self.cfg = cfg
        self.duration = float(cfg.get("duration", 3.0))
        self.bg = make_background(cfg.get("bg", "blue"))
        self.chars = []
        for c in cfg.get("characters", []):
            sc = c.get("scale", 1.0)
            spr = draw_character(c["who"], c.get("mood", "neutral"), c.get("pose", "idle"), c.get("prop"), sc)
            self.chars.append((spr, c.get("x", W / 2), c.get("y", 300)))
        self.items = []  # (sprite, cx, cy, appear_time, rot)
        t0 = 0.35
        for i, p in enumerate(cfg.get("props", [])):
            self.items.append((draw_prop(p), p["x"], p["y"], p.get("at", t0 + 0.25 * i), p.get("rot", 0)))
        n = len(self.items)
        for i, lb in enumerate(cfg.get("labels", [])):
            spr = draw_label(lb["text"], lb.get("size", 64), lb.get("color", "white"))
            self.items.append((spr, lb["x"], lb["y"], lb.get("at", t0 + 0.25 * (n + i)), lb.get("rot", -3)))
        self.badge = draw_badge(cfg["badge"]) if cfg.get("badge") else None
        self.caption = draw_caption(cfg["caption"], cfg.get("caption_size", 46)) if cfg.get("caption") else None
        self.caption_y = cfg.get("caption_y", 1070)

    def pop_times(self):
        return [0.0] + [it[3] for it in self.items]

    def frame(self, t):
        im = self.bg.copy()
        for i, (spr, cx, top) in enumerate(self.chars):
            e = ease_out_back(t / 0.35)
            sc = 0.85 + 0.15 * e
            bob = math.sin(2 * math.pi * (t * 1.1 + i * 0.3)) * 5
            sx = 1 + 0.015 * math.sin(2 * math.pi * t * 1.1)
            s = spr.resize((max(1, int(spr.width * sc * sx)), max(1, int(spr.height * sc / sx))), Image.BILINEAR)
            im.paste(s, (int(cx - s.width / 2), int(top + spr.height - s.height + bob)), s)
        for spr, cx, cy, at, rot in self.items:
            if t < at:
                continue
            e = ease_out_back((t - at) / 0.35)
            if e <= 0.01:
                continue
            fl = math.sin(2 * math.pi * (t - at) * 0.7) * 4
            s = spr.rotate(rot + fl * 0.4, resample=Image.BICUBIC, expand=True) if (rot or fl) else spr
            s = s.resize((max(1, int(s.width * e)), max(1, int(s.height * e))), Image.BILINEAR)
            x = min(max(cx, spr.width / 2 + 8), W - spr.width / 2 - 8)  # не выходить за край
            im.paste(s, (int(x - s.width / 2), int(cy - s.height / 2 + fl)), s)
        if self.badge is not None:
            e = ease_out_back(t / 0.3)
            b = self.badge
            im.paste(b, (int(W / 2 - b.width / 2), int(150 - (1 - e) * 120)), b)
        if self.caption is not None:
            e = ease_out_back((t - 0.1) / 0.3)
            if e > 0.01:
                c = self.caption.resize((max(1, int(self.caption.width * e)), max(1, int(self.caption.height * e))), Image.BILINEAR)
                im.paste(c, (int(W / 2 - c.width / 2), int(self.caption_y - c.height / 2)), c)
        return im


# ---------------------------------------------------------------- звук
def make_sfx(scenes, fps, total, path, sr=44100):
    audio = np.zeros(int(total * sr) + sr, dtype=np.float32)

    def pop(t0, f0=500, f1=1100, dur=0.09, vol=0.25):
        n = int(dur * sr)
        tt = np.arange(n) / sr
        freq = f0 + (f1 - f0) * tt / dur
        sig = np.sin(2 * np.pi * np.cumsum(freq) / sr) * np.exp(-tt * 35) * vol
        i = int(t0 * sr)
        audio[i:i + n] += sig[: len(audio) - i]

    def whoosh(t0, dur=0.3, vol=0.12):
        n = int(dur * sr)
        noise = np.random.default_rng(int(t0 * 1000)).standard_normal(n)
        kern = np.ones(30) / 30
        sig = np.convolve(noise, kern, "same") * np.sin(np.linspace(0, np.pi, n)) * vol * 3
        i = int(t0 * sr)
        audio[i:i + n] += sig[: len(audio) - i].astype(np.float32)

    start = 0.0
    for sc in scenes:
        whoosh(start)
        for pt in sc.pop_times()[1:]:
            pop(start + pt)
        start += sc.duration
    audio = np.clip(audio[: int(total * sr)], -1, 1)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario")
    ap.add_argument("-o", "--out", default="out.mp4")
    ap.add_argument("--stills", help="папка для PNG-кадров каждой сцены")
    ap.add_argument("--audio", help="озвучка/музыка, будет смешана с SFX")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--no-sfx", action="store_true")
    ap.add_argument("--only", help="рендерить только сцены (через запятую, с 1)")
    a = ap.parse_args()

    with open(a.scenario, encoding="utf-8") as fh:
        data = json.load(fh)
    cfgs = data["scenes"] if isinstance(data, dict) else data
    if a.only:
        idx = [int(x) - 1 for x in a.only.split(",")]
        cfgs = [cfgs[i] for i in idx]
    scenes = [Scene(c) for c in cfgs]
    total = sum(s.duration for s in scenes)
    print(f"сцен: {len(scenes)}, длительность: {total:.1f} c", file=sys.stderr)

    if a.stills:
        os.makedirs(a.stills, exist_ok=True)
        for i, s in enumerate(scenes, 1):
            s.frame(s.duration * 0.85).save(os.path.join(a.stills, f"scene_{i:02d}.png"))

    tmpdir = tempfile.mkdtemp()
    sfx = os.path.join(tmpdir, "sfx.wav")
    make_sfx(scenes, a.fps, total, sfx)
    if a.no_sfx:
        make_sfx([], a.fps, total, sfx)

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(a.fps), "-i", "-", "-i", sfx]
    if a.audio:
        cmd += ["-i", a.audio, "-filter_complex", "[1:a][2:a]amix=inputs=2:duration=first:normalize=0[a]",
                "-map", "0:v", "-map", "[a]"]
    else:
        cmd += ["-map", "0:v", "-map", "1:a"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-b:a", "160k", "-shortest", "-movflags", "+faststart", a.out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    xfade = int(0.2 * a.fps)
    prev_last = None
    for si, s in enumerate(scenes):
        n = int(round(s.duration * a.fps))
        for fi in range(n):
            fr = s.frame(fi / a.fps)
            if prev_last is not None and fi < xfade:
                fr = Image.blend(prev_last, fr, (fi + 1) / (xfade + 1))
            proc.stdin.write(fr.tobytes())
        prev_last = s.frame((n - 1) / a.fps)
        print(f"  сцена {si + 1}/{len(scenes)} готова", file=sys.stderr)
    proc.stdin.close()
    if proc.wait() != 0:
        sys.exit("ffmpeg завершился с ошибкой")
    print(a.out)


if __name__ == "__main__":
    main()
