"""Генератор видео «Пять фактов о космосе».

Озвучка: Piper TTS (пакет piper-tts из PyPI) с русским голосом ru-irinia-medium,
взятым из релиза GitHub: https://github.com/rhasspy/piper/releases/tag/v0.0.2

Запуск:
    python3 make_video.py --voice /путь/к/ru-irinia-medium.onnx
"""

import argparse
import math
import random
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
FPS = 30
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# (заголовок на экране, текст на экране, текст озвучки)
SCENES = [
    ("5 фактов о космосе", "Готовы удивиться?",
     "Пять удивительных фактов о космосе. Поехали!"),
    ("Факт 1. Венера", "Сутки на Венере длятся дольше, чем год:\n243 земных дня против 225",
     "Факт первый. День на Венере длиннее года. Планета делает один оборот вокруг "
     "своей оси за двести сорок три земных дня, а вокруг Солнца — всего за двести двадцать пять."),
    ("Факт 2. Нейтронные звёзды", "Чайная ложка их вещества\nвесит около миллиарда тонн",
     "Факт второй. Нейтронные звёзды невероятно плотные. Чайная ложка их вещества "
     "весила бы на Земле около миллиарда тонн."),
    ("Факт 3. Тишина", "В космосе нет звука:\nему не через что распространяться",
     "Факт третий. В космосе царит полная тишина. Звуку нужна среда — воздух или вода, "
     "а в космическом вакууме её почти нет."),
    ("Факт 4. Свет Солнца", "Солнечный свет летит до Земли\nоколо 8 минут 20 секунд",
     "Факт четвёртый. Свету Солнца нужно около восьми минут двадцати секунд, чтобы долететь до Земли. "
     "Так что мы всегда видим Солнце немного в прошлом."),
    ("Факт 5. Следы на Луне", "Следы астронавтов сохранятся\nмиллионы лет",
     "Факт пятый. Следы астронавтов на Луне могут сохраниться миллионы лет. "
     "Там нет ни ветра, ни воды, которые могли бы их стереть."),
    ("Спасибо за просмотр!", "Космос ждёт новых открытий",
     "Какой факт удивил вас больше всего? Спасибо за просмотр!"),
]


def background(seed: int) -> Image.Image:
    rnd = random.Random(seed)
    img = Image.new("RGB", (W, H))
    px = img.load()
    # вертикальный градиент от тёмно-синего к фиолетовому
    for y in range(H):
        t = y / H
        c = (int(5 + 25 * t), int(5 + 5 * t), int(25 + 40 * t))
        for x in range(W):
            px[x, y] = c
    # туманность
    neb = Image.new("RGB", (W, H), (0, 0, 0))
    nd = ImageDraw.Draw(neb)
    for _ in range(6):
        cx, cy = rnd.randint(0, W), rnd.randint(0, H)
        r = rnd.randint(250, 550)
        col = rnd.choice([(90, 30, 140), (30, 60, 150), (140, 40, 90), (20, 110, 140)])
        nd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)
    neb = neb.filter(ImageFilter.GaussianBlur(160))
    img = Image.blend(img, neb, 0.45)
    # звёзды
    d = ImageDraw.Draw(img)
    for _ in range(900):
        x, y = rnd.randint(0, W - 1), rnd.randint(0, H - 1)
        b = rnd.randint(120, 255)
        s = rnd.choice([0, 0, 0, 1, 1, 2])
        d.ellipse((x - s, y - s, x + s, y + s), fill=(b, b, min(255, b + 20)))
    return img


def draw_planet(img: Image.Image, seed: int) -> None:
    rnd = random.Random(seed * 7 + 1)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    r = 230
    cx, cy = W - 300, H - 260
    base = rnd.choice([(230, 160, 80), (90, 150, 230), (200, 90, 70), (170, 170, 190)])
    for i in range(r, 0, -2):
        k = i / r
        col = tuple(int(c * (0.35 + 0.65 * (1 - k) ** 0.5)) for c in base) + (255,)
        off = int((r - i) * 0.35)
        d.ellipse((cx - i - off, cy - i - off, cx + i - off, cy + i - off), fill=col)
    glow = layer.filter(ImageFilter.GaussianBlur(25))
    img.paste(glow, (0, 0), glow)
    img.paste(layer, (0, 0), layer)


def center_text(d, y, text, font, fill, spacing=18):
    box = d.multiline_textbbox((0, 0), text, font=font, align="center", spacing=spacing)
    w = box[2] - box[0]
    d.multiline_text(((W - w) / 2, y), text, font=font, fill=fill, align="center",
                     spacing=spacing, stroke_width=3, stroke_fill=(0, 0, 0))
    return box[3] - box[1]


def make_slide(i: int, title: str, body: str, path: Path) -> None:
    img = background(i + 42)
    if 0 < i < len(SCENES) - 1:
        draw_planet(img, i)
    d = ImageDraw.Draw(img)
    big = ImageFont.truetype(FONT_BOLD, 96 if i in (0, len(SCENES) - 1) else 80)
    reg = ImageFont.truetype(FONT_REG, 58)
    h1 = center_text(d, 300, title, big, (255, 220, 120))
    d.line(((W / 2 - 220), 330 + h1, (W / 2 + 220), 330 + h1), fill=(255, 220, 120), width=4)
    center_text(d, 380 + h1, body, reg, (240, 240, 255))
    img.save(path)


def run(cmd):
    subprocess.run(cmd, check=True)


def duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(path)],
                         check=True, capture_output=True, text=True).stdout
    return float(out.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True, help="путь к .onnx голосу Piper")
    ap.add_argument("--out", default="space_facts.mp4")
    ap.add_argument("--work", default="build")
    a = ap.parse_args()
    work = Path(a.work)
    work.mkdir(parents=True, exist_ok=True)

    clips = []
    for i, (title, body, voice_text) in enumerate(SCENES):
        png, wav, mp4 = work / f"s{i}.png", work / f"s{i}.wav", work / f"s{i}.mp4"
        make_slide(i, title, body, png)
        subprocess.run([sys.executable, "-m", "piper", "-m", a.voice, "-f", str(wav)],
                       input=voice_text, text=True, check=True, capture_output=True)
        dur = duration(wav) + 1.0  # пауза в конце сцены
        frames = math.ceil(dur * FPS)
        # плавный «наезд» камеры + появление/затухание
        vf = (f"scale=3840:-1,zoompan=z='min(zoom+0.0006,1.15)':d={frames}"
              f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},"
              f"fade=t=in:st=0:d=0.5,fade=t=out:st={dur - 0.5:.2f}:d=0.5,format=yuv420p")
        run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", str(png), "-i", str(wav),
             "-af", "adelay=300|300,apad", "-vf", vf, "-t", f"{dur:.2f}",
             "-c:v", "libx264", "-preset", "medium", "-crf", "22",
             "-c:a", "aac", "-b:a", "160k", "-ar", "44100", str(mp4)])
        clips.append(mp4)
        print(f"сцена {i + 1}/{len(SCENES)}: {dur:.1f} c")

    lst = work / "list.txt"
    lst.write_text("".join(f"file '{c.resolve()}'\n" for c in clips))
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c", "copy", "-movflags", "+faststart", a.out])
    print(f"готово: {a.out} ({duration(Path(a.out)):.1f} c)")


if __name__ == "__main__":
    main()
