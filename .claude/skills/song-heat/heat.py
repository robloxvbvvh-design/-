#!/usr/bin/env python3
"""Рисует «термометр» по строкам песни: где градусы растут — красная плашка."""
import argparse
import re

from PIL import Image, ImageDraw, ImageFont

# Основа слова -> сколько градусов прибавляет
HOT = {
    "грет": 12, "грей": 12, "нагре": 14, "жар": 15, "жара": 15, "горяч": 14,
    "гори": 13, "горит": 13, "огон": 15, "огн": 15, "пламя": 15, "плав": 16,
    "полимер": 18, "скорее": 10, "быстр": 8, "кипи": 16, "пар": 6, "печ": 10,
    "солнц": 8, "тепл": 8, "пыла": 12, "искр": 9, "fire": 15, "hot": 14,
    "heat": 14, "burn": 14,
}
COLD = {
    "лед": -12, "лёд": -12, "холод": -12, "мороз": -14, "снег": -10,
    "зим": -8, "стыл": -8, "остыв": -10, "cold": -12, "ice": -12,
}

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def line_heat(line):
    words = re.findall(r"[\wёЁ]+", line.lower())
    delta = 0
    for w in words:
        for stem, val in {**HOT, **COLD}.items():
            if w.startswith(stem):
                delta += val
                break
    delta += 3 * line.count("!")
    caps = [w for w in re.findall(r"[\wёЁ]+", line) if len(w) > 2 and w.isupper()]
    delta += 4 * len(caps)
    return delta


def temperatures(lines, start):
    temps, t = [], start
    for line in lines:
        d = line_heat(line)
        # без горячих слов песня понемногу остывает
        t = max(-10, min(200, t + d if d else t - 2))
        temps.append(t)
    return temps


def color_for(t):
    # синий -> жёлтый -> красный
    k = max(0.0, min(1.0, (t + 10) / 130))
    if k < 0.5:
        a = k / 0.5
        return (int(60 + 195 * a), int(130 + 90 * a), int(230 - 180 * a))
    a = (k - 0.5) / 0.5
    return (255, int(220 - 190 * a), int(50 - 20 * a))


def fit(draw, text, font, width):
    if draw.textlength(text, font=font) <= width:
        return text
    while text and draw.textlength(text + "…", font=font) > width:
        text = text[:-1]
    return text + "…"


def render(lines, temps, out, title):
    W, row, pad, head = 1100, 54, 30, 90 if title else 30
    text_w, bar_x, bar_w = 560, 610, 260
    H = head + row * len(lines) + pad
    img = Image.new("RGB", (W, H), (22, 22, 30))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT, 22)
    fb = ImageFont.truetype(FONT_BOLD, 20)
    ft = ImageFont.truetype(FONT_BOLD, 34)
    if title:
        d.text((pad, 25), title, font=ft, fill=(255, 255, 255))

    top = max(temps) if temps else 0
    peak = temps.index(top) if temps else -1
    for i, (line, t) in enumerate(zip(lines, temps)):
        y = head + i * row
        if i % 2:
            d.rectangle([0, y, W, y + row], fill=(28, 28, 38))
        d.text((pad, y + 14), fit(d, line, f, text_w), font=f, fill=(235, 235, 240))

        # термометр
        d.rounded_rectangle([bar_x, y + 14, bar_x + bar_w, y + 40], 13, fill=(50, 50, 62))
        fill = int(bar_w * max(0.04, min(1.0, (t + 10) / 130)))
        d.rounded_rectangle([bar_x, y + 14, bar_x + fill, y + 40], 13, fill=color_for(t))
        d.text((bar_x + bar_w + 12, y + 15), f"{t}°", font=fb, fill=(255, 255, 255))

        # красная плашка там, где градусы поднялись
        prev = temps[i - 1] if i else None
        label = None
        if i == peak and top > (temps[0] if len(temps) > 1 else -999):
            label = "ПИК ▲"
        elif prev is not None and t > prev:
            label = f"▲ +{t - prev}°"
        if label:
            lx = bar_x + bar_w + 75
            lw = int(d.textlength(label, font=fb)) + 24
            d.rounded_rectangle([lx, y + 10, lx + lw, y + 44], 8, fill=(220, 30, 40))
            d.text((lx + 12, y + 15), label, font=fb, fill=(255, 255, 255))
    img.save(out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("lyrics")
    p.add_argument("out")
    p.add_argument("--title", default="")
    p.add_argument("--start", type=int, default=20)
    a = p.parse_args()
    with open(a.lyrics, encoding="utf-8") as fh:
        lines = [l.strip() for l in fh if l.strip()]
    temps = temperatures(lines, a.start)
    render(lines, temps, a.out, a.title)
    ups = sum(1 for i in range(1, len(temps)) if temps[i] > temps[i - 1])
    if temps:
        print(f"peak={max(temps)} line={temps.index(max(temps)) + 1} rises={ups}")


if __name__ == "__main__":
    main()
