#!/usr/bin/env python3
"""
Фанатская мультипликация «Рик и Морти: Тень Прайма».

Всё рисуется процедурно (PIL), голоса синтезируются espeak-ng,
звуковые эффекты и музыка генерируются numpy. Результат — MP4 (H.264 + AAC).

Запуск:  python3 make_animation.py [выходной.mp4]
Нужно:   python3, numpy, pillow, ffmpeg, espeak-ng
"""
import math
import os
import random
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
FPS = 24
SR = 44100
GROUND = 640
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "rick_and_morty_ten_praima.mp4")
TMP = tempfile.mkdtemp(prefix="rm_anim_")
random.seed(7)
rng = np.random.default_rng(7)

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
f_sub = ImageFont.truetype(FONT, 30)
f_name = ImageFont.truetype(FONT, 26)
f_title = ImageFont.truetype(FONT, 78)
f_small = ImageFont.truetype(FONT, 28)

# ----------------------------------------------------------------------------
# ГОЛОСА
# ----------------------------------------------------------------------------
VOICES = {
    # espeak: голос, высота, скорость
    "rick":  dict(v="ru+m3", p=28, s=150, name="Рик", color=(126, 200, 227)),
    "morty": dict(v="ru+m1", p=88, s=165, name="Морти", color=(244, 208, 63)),
    "evil":  dict(v="ru+m4", p=50, s=120, name="Злой Морти", color=(190, 90, 255)),
    "prime": dict(v="ru+m7", p=12, s=128, name="Рик Прайм", color=(255, 70, 70)),
}


def load_wav(path):
    with wave.open(path) as w:
        sr = w.getframerate()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    if sr != SR:
        n = int(len(data) * SR / sr)
        data = np.interp(np.linspace(0, len(data) - 1, n), np.arange(len(data)), data)
    return data.astype(np.float32)


def tts(text, who):
    cfg = VOICES[who]
    path = os.path.join(TMP, f"tts_{abs(hash((text, who)))}.wav")
    subprocess.run(["espeak-ng", "-v", cfg["v"], "-p", str(cfg["p"]), "-s", str(cfg["s"]),
                    "-a", "180", "-w", path, text], check=True)
    a = load_wav(path)
    # обрежем тишину по краям
    idx = np.where(np.abs(a) > 0.01)[0]
    if len(idx):
        a = a[max(0, idx[0] - 200): idx[-1] + 400]
    if who in ("evil", "prime"):  # зловещая реверберация
        a = echo(a, 0.09, 0.35)
        a = echo(a, 0.23, 0.2)
    if who == "prime":  # металлический оттенок
        t = np.arange(len(a)) / SR
        a = a * (0.75 + 0.25 * np.sin(2 * np.pi * 45 * t))
    return a / (np.max(np.abs(a)) + 1e-6) * 0.9


def echo(a, delay, gain):
    d = int(delay * SR)
    out = np.concatenate([a, np.zeros(d, np.float32)])
    out[d:] += a * gain
    return out


def speech(text, who):
    """Текст может содержать '*бёрп*' — туда вставляется синтезированная отрыжка."""
    parts = text.split("*бёрп*")
    out = []
    for i, p in enumerate(parts):
        if p.strip(" .,"):
            out.append(tts(p.strip(), who))
        if i < len(parts) - 1:
            out.append(burp())
    return np.concatenate(out)


# ----------------------------------------------------------------------------
# ЗВУКОВЫЕ ЭФФЕКТЫ (синтез)
# ----------------------------------------------------------------------------
def tt(dur):
    return np.arange(int(dur * SR)) / SR


def lowpass(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x)).astype(np.float32)


def bandpass(x, lo, hi):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= ((f > lo) & (f < hi))
    return np.fft.irfft(X, len(x)).astype(np.float32)


def norm(x, g=1.0):
    return (x / (np.max(np.abs(x)) + 1e-9) * g).astype(np.float32)


def burp():
    t = tt(0.55)
    f0 = 85 + 25 * np.sin(2 * np.pi * 3 * t) + rng.normal(0, 8, len(t)).cumsum() * 0.02
    ph = np.cumsum(2 * np.pi * f0 / SR)
    saw = (ph / (2 * np.pi)) % 1 * 2 - 1
    rough = 1 + 0.6 * np.sign(np.sin(2 * np.pi * 31 * t))
    env = np.minimum(1, t / 0.04) * np.exp(-3 * t)
    x = saw * rough * env + rng.normal(0, 0.2, len(t)) * env
    x = bandpass(x, 60, 1400)
    return norm(x, 0.85)


def portal_sfx():
    t = tt(1.6)
    f = 200 + 900 * t / 1.6
    wob = np.sin(2 * np.pi * np.cumsum(f + 120 * np.sin(2 * np.pi * 9 * t)) / SR)
    noise = bandpass(rng.normal(0, 1, len(t)), 300, 3000)
    env = np.minimum(1, t / 0.3) * np.exp(-1.2 * t)
    x = (0.6 * wob + 0.5 * noise * (0.5 + 0.5 * np.sin(2 * np.pi * 14 * t))) * env
    # «бульк» в начале
    x[: int(0.15 * SR)] += np.sin(2 * np.pi * 120 * t[: int(0.15 * SR)]) * np.exp(-25 * t[: int(0.15 * SR)])
    return norm(x, 0.7)


def laser():
    t = tt(0.32)
    f = 2200 * np.exp(-8 * t) + 250
    x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.5 + np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR) * 0.5
    return norm(x * np.exp(-7 * t), 0.45)


def explosion():
    t = tt(1.8)
    n = rng.normal(0, 1, len(t))
    x = lowpass(n, 500) * np.exp(-2.6 * t) + lowpass(n, 90) * 2 * np.exp(-1.5 * t)
    x[: int(0.05 * SR)] += rng.normal(0, 1, int(0.05 * SR)) * 1.5
    return norm(x, 0.9)


def thunder():
    t = tt(2.8)
    n = rng.normal(0, 1, len(t))
    crack = (rng.random(len(t)) > 0.995) * rng.normal(0, 3, len(t)) * np.exp(-4 * t)
    x = lowpass(n, 160) * 3 * np.exp(-1.1 * t) * (1 + 0.5 * np.sin(2 * np.pi * 3 * t)) + lowpass(crack, 3000)
    return norm(x, 0.95)


def whoosh(dur=0.9):
    t = tt(dur)
    n = rng.normal(0, 1, len(t))
    env = np.sin(np.pi * t / dur) ** 2
    x = bandpass(n, 400, 2500) * env
    return norm(x, 0.55)


def beeps():
    out = []
    for i in range(4):
        t = tt(0.12)
        out.append(np.sin(2 * np.pi * 1320 * t) * np.exp(-12 * t) * 0.35)
        out.append(np.zeros(int(0.18 * SR)))
    return np.concatenate(out).astype(np.float32)


def thud():
    t = tt(0.5)
    x = np.sin(2 * np.pi * (70 * np.exp(-3 * t)) * t) * np.exp(-9 * t) + lowpass(rng.normal(0, 1, len(t)), 400) * np.exp(-14 * t) * 0.6
    return norm(x, 0.8)


def drone_hit():
    t = tt(3.0)
    x = sum(np.sin(2 * np.pi * f * t) for f in (41.2, 61.7, 82.4, 87.3)) * np.exp(-0.8 * t)
    x += bandpass(rng.normal(0, 1, len(t)), 50, 200) * np.exp(-1.2 * t) * 0.6
    return norm(x * np.minimum(1, t / 0.05), 0.75)


SFX = {"burp": burp, "portal": portal_sfx, "laser": laser, "boom": explosion,
       "thunder": thunder, "whoosh": whoosh, "beeps": beeps, "thud": thud, "hit": drone_hit}

# ----------------------------------------------------------------------------
# СЦЕНАРИЙ
# ----------------------------------------------------------------------------
# chars: (вид, x, направление взгляда 1=вправо, -1=влево)
SHOTS = [
    dict(bg="title", dur=5.0, sfx=[(0.2, "hit"), (2.2, "portal")], music="theme"),
    dict(bg="garage", chars=[("rick", 420, 1), ("morty", 820, -1)], dur=2.0, sfx=[(0.2, "beeps")], fx=["device"], music="calm"),
    dict(bg="garage", chars=[("rick", 420, 1), ("morty", 820, -1)], line=("morty", "Рик! Рик, что это за сигнал на твоём приборе?"), fx=["device"], music="calm"),
    dict(bg="garage", chars=[("rick", 420, 1), ("morty", 820, -1)], line=("rick", "Это, Морти... *бёрп* ...это сигнатура Рика Прайма. Он где-то рядом."), fx=["device"], music="calm"),
    dict(bg="garage", chars=[("rick", 420, 1), ("morty", 820, -1)], line=("morty", "Тот самый Рик Прайм? Который... ну, ты знаешь?"), music="tense"),
    dict(bg="garage", chars=[("rick", 420, 1), ("morty", 820, -1)], line=("rick", "Да. Хватай пушку, Морти. Мы идём."), sfx=[(-0.1, "portal")], fx=["portal_open"], music="tense"),
    dict(bg="garage", chars=[("rick", 420, 1), ("morty", 820, 1)], dur=2.4, sfx=[(0.6, "whoosh")], fx=["portal", "enter_portal"], music="tense"),
    dict(bg="tunnel", dur=2.2, sfx=[(0.0, "whoosh"), (1.0, "whoosh")], music="tense"),
    dict(bg="fortress", chars=[("rick", 330, 1), ("morty", 520, 1)], dur=2.0, sfx=[(0.0, "thud"), (0.9, "hit")], fx=["evil_appear"], extra_chars=[("evil", 960, -1)], music="dark"),
    dict(bg="fortress", chars=[("rick", 330, 1), ("morty", 520, 1), ("evil", 960, -1)], line=("evil", "Ну здравствуй, Рик. Я ждал тебя."), music="dark"),
    dict(bg="fortress", chars=[("rick", 330, 1), ("morty", 520, 1), ("evil", 960, -1)], line=("morty", "Э-это же я? С повязкой на глазу?"), music="dark"),
    dict(bg="fortress", chars=[("rick", 330, 1), ("morty", 520, 1), ("evil", 960, -1)], line=("evil", "Я не ты, Морти. Я тот, кто вырвался из бесконечного круга."), music="dark"),
    dict(bg="fortress", chars=[("rick", 330, 1), ("morty", 520, 1), ("evil", 960, -1)], dur=2.4, sfx=[(0.3, "thunder")], fx=["prime_appear"], extra_chars=[("prime", 1140, -1)], music="dark"),
    dict(bg="fortress", chars=[("rick", 330, 1), ("morty", 520, 1), ("evil", 900, -1), ("prime", 1110, -1)], line=("prime", "Как трогательно. Две копии, которые думают, что что-то решают."), music="dark"),
    dict(bg="fortress", chars=[("rick", 330, 1), ("morty", 520, 1), ("evil", 900, -1), ("prime", 1110, -1)], line=("rick", "Прайм. Сегодня всё закончится."), music="battle"),
    dict(bg="fortress", chars=[("rick", 330, 1), ("morty", 520, 1), ("evil", 900, -1), ("prime", 1110, -1)], line=("prime", "Ты говоришь это в каждой реальности, Рик."), music="battle"),
    dict(bg="battle", chars=[("rick", 260, 1), ("morty", 120, 1), ("evil", 760, -1), ("prime", 1080, -1)], dur=6.0, fx=["battle"],
         sfx=[(0.3, "laser"), (0.7, "laser"), (1.0, "boom"), (1.6, "laser"), (2.0, "laser"), (2.3, "laser"), (2.6, "boom"),
              (3.4, "laser"), (3.7, "laser"), (4.1, "boom"), (4.6, "laser"), (5.0, "laser"), (5.2, "boom")], music="battle"),
    dict(bg="battle", chars=[("rick", 260, 1), ("morty", 120, 1), ("evil", 760, -1), ("prime", 1080, -1)], line=("evil", "Уходите. Он мой."), fx=["battle_light"], music="battle"),
    dict(bg="battle", chars=[("rick", 260, -1), ("morty", 120, 1), ("evil", 760, -1), ("prime", 1080, -1)], line=("rick", "Морти, в портал! Быстро!"), sfx=[(0.0, "portal"), (0.8, "boom")], fx=["battle_light", "escape_portal"], music="battle"),
    dict(bg="tunnel", dur=1.8, sfx=[(0.0, "whoosh")], music="tense"),
    dict(bg="garage", chars=[("rick", 520, 1), ("morty", 760, -1)], dur=1.8, sfx=[(0.35, "thud"), (0.55, "thud")], fx=["portal", "fall_in"], music="calm"),
    dict(bg="garage", chars=[("rick", 520, 1), ("morty", 760, -1)], line=("morty", "Рик... мы вообще выиграли?"), music="calm"),
    dict(bg="garage", chars=[("rick", 520, 1), ("morty", 760, -1)], line=("rick", "Мы выжили, Морти. В нашей семье это одно и то же. *бёрп*"), music="calm"),
    dict(bg="end", dur=5.0, sfx=[(0.3, "hit")], music="theme"),
]

# ----------------------------------------------------------------------------
# ПОСТРОЕНИЕ ТАЙМЛАЙНА + ЗВУКА
# ----------------------------------------------------------------------------
PRE, POST = 0.35, 0.55
t0 = 0.0
for sh in SHOTS:
    sh["start"] = t0
    if "line" in sh:
        who, text = sh["line"]
        sh["voice"] = speech(text, who)
        sh["vstart"] = PRE
        sh["dur"] = PRE + len(sh["voice"]) / SR + POST
        # огибающая для синхронизации губ
        v = sh["voice"]
        hop = SR // FPS
        env = np.array([np.sqrt(np.mean(v[i:i + hop] ** 2)) for i in range(0, len(v), hop)])
        sh["env"] = env / (env.max() + 1e-9)
    t0 += sh["dur"]
TOTAL = t0
NS = int(TOTAL * SR) + SR
voice_track = np.zeros(NS, np.float32)
sfx_track = np.zeros(NS, np.float32)


def place(track, clip, t):
    i = max(0, int(t * SR))
    j = min(len(track), i + len(clip))
    track[i:j] += clip[: j - i]


for sh in SHOTS:
    if "voice" in sh:
        place(voice_track, sh["voice"], sh["start"] + sh["vstart"])
    for (dt, name) in sh.get("sfx", []):
        place(sfx_track, SFX[name](), sh["start"] + max(0, dt))


# ---- музыка (оригинальная, синтезированная)
def synth_music():
    m = np.zeros(NS, np.float32)
    beat = 60 / 112
    for sh in SHOTS:
        s, d, mood = sh["start"], sh["dur"], sh.get("music", "calm")
        n = int(d * SR)
        t = np.arange(n) / SR + s
        if mood == "theme":
            # «космический» мотив: арпеджио + терменвокс с вибрато
            notes = [220, 261.6, 329.6, 392, 440, 392, 329.6, 261.6]
            step = 0.22
            idx = ((t / step).astype(int)) % len(notes)
            f = np.array(notes)[idx]
            ph = np.cumsum(2 * np.pi * f / SR)
            local = (t % step)
            arp = np.sign(np.sin(ph)) * np.exp(-6 * local) * 0.12
            ther_f = 440 * (1 + 0.012 * np.sin(2 * np.pi * 6 * t)) * np.where((t // 1.76) % 2 == 0, 1, 0.84)
            ther = np.sin(np.cumsum(2 * np.pi * ther_f / SR)) * 0.12
            pad = (np.sin(2 * np.pi * 110 * t) + np.sin(2 * np.pi * 164.8 * t)) * 0.06
            seg = arp + ther + pad
        elif mood == "calm":
            seg = (np.sin(2 * np.pi * 110 * t) + 0.6 * np.sin(2 * np.pi * 138.6 * t) + 0.5 * np.sin(2 * np.pi * 164.8 * t)) * 0.04 * (0.7 + 0.3 * np.sin(2 * np.pi * 0.25 * t))
        elif mood == "tense":
            pulse = np.exp(-10 * (t % (beat / 2)))
            seg = np.sin(2 * np.pi * 55 * t) * 0.09 * pulse + np.sin(2 * np.pi * 233 * t) * 0.025 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.5 * t))
        elif mood == "dark":
            seg = (np.sin(2 * np.pi * 41.2 * t) + 0.7 * np.sin(2 * np.pi * 43.65 * t) + 0.3 * np.sin(2 * np.pi * 98 * t)) * 0.07
            seg += np.sin(2 * np.pi * 659 * t) * 0.012 * (np.sin(2 * np.pi * 0.3 * t) > 0.6)
        else:  # battle
            b = beat / 1.25
            kick = np.sin(2 * np.pi * 55 * np.exp(-25 * (t % b)) * (t % b) * 4) * np.exp(-12 * (t % b)) * 0.35
            bass_notes = np.array([55, 55, 65.4, 49])
            bf = bass_notes[((t / (b * 2)).astype(int)) % 4]
            bass = ((np.cumsum(bf / SR) % 1) * 2 - 1) * 0.08 * np.exp(-4 * (t % (b / 2)))
            hat = rng.normal(0, 1, n) * np.exp(-60 * ((t + b / 2) % b)) * 0.05
            seg = kick + bass + hat
        fade = np.minimum(1, np.minimum(np.arange(n), n - np.arange(n)) / (0.08 * SR))
        i = int(s * SR)
        m[i:i + n] += (seg * fade).astype(np.float32)[: len(m) - i]
    return lowpass(m, 6000)


music = synth_music()
# «приглушение» музыки во время речи
duck = np.convolve(np.abs(voice_track) > 0.02, np.ones(SR // 5) / (SR // 5), mode="same")
mix = voice_track * 0.95 + sfx_track * 0.7 + music * (1 - 0.55 * np.clip(duck * 3, 0, 1))
mix = np.tanh(mix * 1.1) * 0.92
mix = mix[: int(TOTAL * SR)]
wav_path = os.path.join(TMP, "mix.wav")
with wave.open(wav_path, "w") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())

# ----------------------------------------------------------------------------
# РИСОВАНИЕ
# ----------------------------------------------------------------------------
SKIN = (250, 222, 196)
OUTL = (25, 20, 30)


def ell(d, cx, cy, rx, ry, fill, w=3, outline=OUTL):
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=fill, outline=outline, width=w)


def draw_rick(d, x, y, s, mouth, face, t, prime=False):
    coat = (225, 230, 232) if not prime else (95, 95, 105)
    shirt = (126, 200, 227) if not prime else (40, 40, 48)
    hair = (168, 216, 234) if not prime else (205, 214, 220)
    bob = math.sin(t * 2.2) * 2 * s
    y = y + bob
    # ноги
    for sx in (-1, 1):
        d.rectangle((x + sx * 30 * s - 13 * s, y - 135 * s, x + sx * 30 * s + 13 * s, y - 12 * s), fill=(110, 76, 60), outline=OUTL, width=3)
        ell(d, x + sx * 30 * s + face * 8 * s, y - 8 * s, 22 * s, 10 * s, (40, 30, 30))
    # халат
    d.polygon([(x - 62 * s, y - 112 * s), (x + 62 * s, y - 112 * s), (x + 48 * s, y - 305 * s), (x - 48 * s, y - 305 * s)], fill=coat, outline=OUTL, width=3)
    d.polygon([(x - 24 * s, y - 305 * s), (x + 24 * s, y - 305 * s), (x + 14 * s, y - 150 * s), (x - 14 * s, y - 150 * s)], fill=shirt, outline=OUTL, width=2)
    # руки
    for sx in (-1, 1):
        sw = math.sin(t * 3 + sx) * 6 * s
        d.line([(x + sx * 48 * s, y - 295 * s), (x + sx * 64 * s + sw, y - 180 * s)], fill=OUTL, width=int(28 * s))
        d.line([(x + sx * 48 * s, y - 295 * s), (x + sx * 64 * s + sw, y - 180 * s)], fill=coat, width=int(22 * s))
        ell(d, x + sx * 64 * s + sw, y - 172 * s, 12 * s, 12 * s, SKIN)
    # шея
    d.rectangle((x - 13 * s, y - 330 * s, x + 13 * s, y - 300 * s), fill=SKIN, outline=OUTL, width=2)
    cx, cy = x + face * 6 * s, y - 385 * s
    # волосы-шипы
    pts = []
    for i in range(23):
        a = math.radians(-25 + i * 230 / 22)
        r = (100 if i % 2 == 0 else 58) * s
        pts.append((cx - face * 10 * s + r * math.cos(a) * 0.95, cy + 5 * s - r * math.sin(a)))
    d.polygon(pts, fill=hair, outline=OUTL, width=3)
    ell(d, cx, cy, 46 * s, 62 * s, SKIN)
    # глаза
    pc = (230, 20, 20) if prime else (0, 0, 0)
    for ex in (-19, 19):
        ell(d, cx + ex * s, cy - 6 * s, 15 * s, 15 * s, (255, 255, 255), 2)
        ell(d, cx + ex * s + face * 4 * s, cy - 6 * s, 3.5 * s, 3.5 * s, pc, 1, pc)
        d.arc((cx + ex * s - 14 * s, cy + 2 * s, cx + ex * s + 14 * s, cy + 18 * s), 20, 160, fill=(170, 140, 120), width=2)  # мешки
    # моно-бровь
    bw = [(cx - 38 * s, cy - 26 * s)]
    for i in range(1, 8):
        bw.append((cx - 38 * s + i * 76 * s / 7, cy - 26 * s + (4 if i % 2 else -3) * s + (6 * s if prime and 2 < i < 6 else 0)))
    d.line(bw, fill=(120, 150, 165) if not prime else (60, 60, 70), width=int(7 * s))
    # нос
    d.line([(cx + face * 2 * s, cy + 4 * s), (cx + face * 10 * s, cy + 20 * s), (cx, cy + 22 * s)], fill=OUTL, width=2)
    # рот
    my = cy + 40 * s
    if mouth > 0.15:
        h = 4 + mouth * 18
        ell(d, cx, my, 26 * s, h * s, (90, 20, 30), 3)
        d.line([(cx - 20 * s, my - h * s * 0.4), (cx + 20 * s, my - h * s * 0.4)], fill=(255, 255, 255), width=int(4 * s))
    else:
        if prime:
            d.line([(cx - 28 * s, my + 2 * s), (cx, my + 4 * s), (cx + 28 * s, my - 8 * s)], fill=OUTL, width=3)
        else:
            d.line([(cx - 28 * s, my), (cx + 28 * s, my + 2 * s)], fill=OUTL, width=3)
    if prime:  # шрам
        d.line([(cx + 22 * s, cy - 40 * s), (cx + 34 * s, cy + 20 * s)], fill=(170, 60, 60), width=3)
        for k in range(4):
            yy = cy - 30 * s + k * 14 * s
            d.line([(cx + 23 * s + k * 3 * s, yy), (cx + 33 * s + k * 3 * s, yy - 3 * s)], fill=(170, 60, 60), width=2)


def draw_morty(d, x, y, s, mouth, face, t, evil=False):
    shirt = (244, 208, 63) if not evil else (32, 44, 70)
    pants = (30, 90, 168) if not evil else (20, 20, 28)
    bob = math.sin(t * 2.6 + 1) * 2 * s
    y = y + bob
    for sx in (-1, 1):
        d.rectangle((x + sx * 20 * s - 13 * s, y - 95 * s, x + sx * 20 * s + 13 * s, y - 10 * s), fill=pants, outline=OUTL, width=3)
        ell(d, x + sx * 20 * s + face * 6 * s, y - 6 * s, 19 * s, 9 * s, (255, 255, 255) if not evil else (60, 60, 60))
    d.rounded_rectangle((x - 48 * s, y - 205 * s, x + 48 * s, y - 88 * s), radius=int(18 * s), fill=shirt, outline=OUTL, width=3)
    for sx in (-1, 1):
        sw = math.sin(t * 3.4 + sx) * 5 * s
        d.line([(x + sx * 42 * s, y - 190 * s), (x + sx * 56 * s + sw, y - 110 * s)], fill=OUTL, width=int(20 * s))
        d.line([(x + sx * 42 * s, y - 190 * s), (x + sx * 56 * s + sw, y - 110 * s)], fill=SKIN, width=int(15 * s))
        ell(d, x + sx * 56 * s + sw, y - 105 * s, 10 * s, 10 * s, SKIN)
        d.ellipse((x + sx * 44 * s - 16 * s, y - 200 * s, x + sx * 44 * s + 16 * s, y - 170 * s), fill=shirt, outline=OUTL, width=2)
    cx, cy = x + face * 5 * s, y - 268 * s
    ell(d, cx, cy - 10 * s, 70 * s, 62 * s, (120, 74, 40))  # волосы
    ell(d, cx, cy + 6 * s, 64 * s, 54 * s, SKIN)
    # глаза
    for i, ex in enumerate((-24, 24)):
        ex_x = cx + ex * s
        if evil and i == 0:
            ell(d, ex_x, cy - 2 * s, 20 * s, 18 * s, (10, 10, 10), 2)
            d.line([(cx - 64 * s, cy - 22 * s), (ex_x, cy - 4 * s), (cx + 64 * s, cy - 26 * s)], fill=(10, 10, 10), width=4)
            continue
        ell(d, ex_x, cy - 2 * s, 20 * s, 20 * s, (255, 255, 255), 2)
        ell(d, ex_x + face * 4 * s, cy - 2 * s, 3.5 * s, 3.5 * s, (0, 0, 0), 1, (0, 0, 0))
        if evil:  # прищур
            d.chord((ex_x - 21 * s, cy - 23 * s, ex_x + 21 * s, cy + 9 * s), 180, 360, fill=SKIN, outline=OUTL, width=2)
    d.arc((cx - 6 * s, cy + 6 * s, cx + 6 * s, cy + 16 * s), 0, 180, fill=OUTL, width=2)
    my = cy + 30 * s
    if mouth > 0.15:
        h = 3 + mouth * 13
        ell(d, cx, my, 15 * s, h * s, (110, 30, 40), 3)
    elif evil:
        d.line([(cx - 16 * s, my + 2 * s), (cx + 16 * s, my - 3 * s)], fill=OUTL, width=3)
    else:
        d.arc((cx - 14 * s, my - 8 * s, cx + 14 * s, my + 4 * s), 20, 160, fill=OUTL, width=3)


def draw_char(d, kind, x, y, mouth, face, t):
    if kind == "rick":
        draw_rick(d, x, y, 1.0, mouth, face, t)
    elif kind == "prime":
        draw_rick(d, x, y, 1.05, mouth, face, t, prime=True)
    elif kind == "morty":
        draw_morty(d, x, y, 1.0, mouth, face, t)
    else:
        draw_morty(d, x, y, 1.0, mouth, face, t, evil=True)


# --- фоны (кэшируются)
_bg_cache = {}


def bg_garage():
    im = Image.new("RGB", (W, H), (120, 128, 118))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 470), fill=(140, 146, 132))
    d.rectangle((0, 470, W, H), fill=(92, 92, 96))
    for x in range(0, W, 160):
        d.line([(x, 470), (x - 80, H)], fill=(80, 80, 85), width=2)
    # гаражные ворота
    d.rectangle((40, 90, 300, 470), fill=(170, 170, 160), outline=OUTL, width=4)
    for yy in range(130, 470, 45):
        d.line([(40, yy), (300, yy)], fill=(130, 130, 125), width=3)
    # верстак
    d.rectangle((560, 380, 1000, 410), fill=(130, 90, 60), outline=OUTL, width=3)
    for xx in (580, 980):
        d.rectangle((xx - 8, 410, xx + 8, 520), fill=(100, 70, 45), outline=OUTL, width=2)
    # полки с хламом
    for yy in (170, 260):
        d.rectangle((600, yy, 980, yy + 12), fill=(110, 80, 55), outline=OUTL, width=2)
        for k in range(6):
            c = [(200, 60, 60), (60, 160, 90), (60, 110, 200), (220, 200, 70), (150, 90, 200), (90, 200, 200)][k]
            xx = 620 + k * 60
            if k % 2:
                d.rectangle((xx, yy - 50, xx + 35, yy), fill=c, outline=OUTL, width=2)
            else:
                ell(d, xx + 18, yy - 22, 18, 22, c)
    # лампа
    d.line([(W // 2, 0), (W // 2, 50)], fill=OUTL, width=3)
    d.polygon([(W // 2 - 40, 80), (W // 2 + 40, 80), (W // 2 + 15, 50), (W // 2 - 15, 50)], fill=(60, 60, 60))
    ell(d, W // 2, 82, 14, 8, (255, 250, 200), 1)
    # летающая тарелка-корабль на заднем плане
    ell(d, 1140, 420, 110, 30, (160, 160, 170))
    ell(d, 1140, 395, 50, 30, (150, 220, 240))
    return im


def bg_fortress():
    im = Image.new("RGB", (W, H), (10, 6, 20))
    d = ImageDraw.Draw(im)
    for i in range(0, 470, 4):
        c = int(20 + i * 0.12)
        d.rectangle((0, i, W, i + 4), fill=(c, 8, c + 18))
    r = random.Random(3)
    for _ in range(160):
        x, y = r.randrange(W), r.randrange(440)
        b = r.randrange(120, 255)
        d.point((x, y), fill=(b, b, b))
    # гигантская крепость-башня
    d.polygon([(560, 470), (720, 470), (690, 120), (640, 60), (590, 120)], fill=(30, 26, 44), outline=(90, 60, 140), width=3)
    ell(d, 640, 150, 30, 30, (120, 255, 140), 2, (40, 120, 60))
    for k in range(-3, 4):
        if k:
            x = 640 + k * 150
            h = 260 + abs(k) * 40
            d.polygon([(x - 40, 470), (x + 40, 470), (x + 22, h), (x - 22, h)], fill=(24, 20, 36), outline=(70, 50, 110), width=2)
    # пол-платформа
    d.rectangle((0, 470, W, H), fill=(36, 32, 48))
    for x in range(-600, W + 600, 90):
        d.line([(x, H), (W // 2 + (x - W // 2) * 0.25, 470)], fill=(60, 52, 80), width=2)
    for y in (500, 540, 590, 650):
        d.line([(0, y), (W, y)], fill=(60, 52, 80), width=2)
    return im


def bg_battle():
    im = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    for i in range(0, 470, 4):
        d.rectangle((0, i, W, i + 4), fill=(80 + i // 5, 10 + i // 12, 20))
    r = random.Random(5)
    for _ in range(14):
        x = r.randrange(W)
        h = r.randrange(120, 300)
        d.polygon([(x - 50, 470), (x + 50, 470), (x + 20, 470 - h), (x - 10, 470 - h + 40)], fill=(30, 10, 14))
    d.rectangle((0, 470, W, H), fill=(44, 22, 26))
    for k in range(8):
        x = r.randrange(W)
        d.line([(x, 470), (x + r.randrange(-90, 90), H)], fill=(255, 120, 40), width=2)
    return im


def bg(name):
    if name not in _bg_cache:
        _bg_cache[name] = {"garage": bg_garage, "fortress": bg_fortress, "battle": bg_battle}[name]()
    return _bg_cache[name].copy()


def portal(ov, cx, cy, rad, t):
    d = ImageDraw.Draw(ov)
    if rad < 2:
        return
    for k in range(10, 0, -1):
        rr = rad * (1 + k * 0.06)
        d.ellipse((cx - rr * 0.6, cy - rr, cx + rr * 0.6, cy + rr), fill=(80, 255, 120, int(14 * (11 - k))))
    d.ellipse((cx - rad * 0.6, cy - rad, cx + rad * 0.6, cy + rad), fill=(70, 220, 90, 255))
    for k in range(7):
        f = 1 - k / 7
        rr = rad * f
        off = math.sin(t * 5 + k) * 6 * f
        col = (140 + k * 15, 255, 140 + k * 10, 255) if k % 2 else (40, 170 + k * 10, 60, 255)
        d.ellipse((cx - rr * 0.6 + off, cy - rr, cx + rr * 0.6 + off, cy + rr), outline=col, width=max(2, int(rad / 20)))
    # спиральные искры
    for k in range(18):
        a = t * 4 + k * 2 * math.pi / 18
        rr = rad * (0.25 + 0.7 * ((k * 37) % 10) / 10)
        x, y = cx + math.cos(a) * rr * 0.6, cy + math.sin(a) * rr
        d.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(220, 255, 210, 255))


def aura(ov, cx, cy, rx, ry, col, t):
    d = ImageDraw.Draw(ov)
    for k in range(12, 0, -1):
        f = 1 + k * 0.05 + 0.02 * math.sin(t * 6 + k)
        d.ellipse((cx - rx * f, cy - ry * f, cx + rx * f, cy + ry * f), fill=col + (int(9 + 3 * (12 - k)),))


def subtitle(im, who, text):
    d = ImageDraw.Draw(im, "RGBA")
    cfg = VOICES[who]
    clean = text.replace("*бёрп*", "*отрыжка*")
    words, lines, cur = clean.split(), [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if d.textlength(trial, font=f_sub) > W - 200:
            lines.append(cur)
            cur = wd
        else:
            cur = trial
    lines.append(cur)
    h = 50 + 40 * len(lines)
    y0 = H - h - 16
    d.rounded_rectangle((70, y0, W - 70, H - 16), radius=16, fill=(0, 0, 0, 170))
    d.text((95, y0 + 10), cfg["name"] + ":", font=f_name, fill=cfg["color"])
    for i, ln in enumerate(lines):
        d.text((95, y0 + 46 + i * 40), ln, font=f_sub, fill=(255, 255, 255))


def centered(d, y, text, font, fill, stroke=0, sfill=(0, 0, 0)):
    w = d.textlength(text, font=font)
    d.text(((W - w) / 2, y), text, font=font, fill=fill, stroke_width=stroke, stroke_fill=sfill)


def render_frame(sh, lt, gt):
    """sh — кадр сценария, lt — время внутри кадра, gt — глобальное время"""
    name = sh["bg"]
    dur = sh["dur"]
    fx = sh.get("fx", [])
    if name in ("title", "end"):
        im = Image.new("RGB", (W, H), (8, 10, 24))
        d = ImageDraw.Draw(im)
        r = random.Random(1)
        for _ in range(220):
            x, y = r.randrange(W), r.randrange(H)
            sp = r.uniform(20, 120)
            xx = (x - gt * sp) % W
            b = r.randrange(100, 255)
            d.point((xx, y), fill=(b, b, b))
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        rad = min(1, lt / 1.5) * 230
        portal(ov, W // 2, H // 2 - 20, rad, gt)
        im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
        d = ImageDraw.Draw(im)
        a = min(1, max(0, (lt - 1.2) / 0.8))
        if name == "title":
            if a > 0:
                c = (int(250 * a), int(250 * a), int(120 * a))
                centered(d, 230, "РИК И МОРТИ", f_title, c, 6, (20, 120, 40))
                centered(d, 330, "ТЕНЬ ПРАЙМА", f_title, (int(255 * a), int(70 * a), int(70 * a)), 6, (30, 0, 0))
                centered(d, 450, "фанатская анимация", f_small, (int(200 * a),) * 3, 2)
        else:
            if a > 0:
                centered(d, 270, "ПРОДОЛЖЕНИЕ СЛЕДУЕТ...", ImageFont.truetype(FONT, 60), (int(250 * a), int(250 * a), int(120 * a)), 5, (20, 120, 40))
                centered(d, 380, "Фанатская работа. Не официальный контент Adult Swim.", f_small, (int(200 * a),) * 3, 2)
                centered(d, 420, "Голоса: синтез речи · Звук и музыка: сгенерированы", f_small, (int(170 * a),) * 3, 2)
        fade = min(1, lt / 0.4, (dur - lt) / 0.4)
        return Image.eval(im, lambda v: int(v * max(0, fade)))

    if name == "tunnel":
        im = Image.new("RGB", (W, H), (0, 20, 0))
        d = ImageDraw.Draw(im)
        for k in range(26, 0, -1):
            z = (k - lt * 14) % 26 + 0.3
            rr = 900 / z
            col = (40 + (k * 30) % 150, 255 - (k * 13) % 120, 80 + (k * 20) % 120)
            off = math.sin(lt * 3 + k * 0.4) * 40
            d.ellipse((W / 2 - rr * 1.3 + off, H / 2 - rr + off / 2, W / 2 + rr * 1.3 + off, H / 2 + rr + off / 2), outline=col, width=max(2, int(30 / z)))
        # падающие Рик и Морти в туннеле
        sc = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dd = ImageDraw.Draw(sc)
        draw_rick(dd, 560 + math.sin(lt * 4) * 30, 560, 0.75, 0.6, 1, lt * 3)
        draw_morty(dd, 760 + math.cos(lt * 4) * 30, 500, 0.75, 0.9, -1, lt * 3)
        sc = sc.rotate(math.sin(lt * 2) * 20, center=(W // 2, H // 2))
        im = Image.alpha_composite(im.convert("RGBA"), sc).convert("RGB")
        return im

    im = bg(name).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))   # свечение позади персонажей
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))   # эффекты поверх
    chars = list(sh.get("chars", []))
    speaker = sh["line"][0] if "line" in sh else None
    mouth_val = 0.0
    if speaker:
        vi = int((lt - sh["vstart"]) * FPS)
        if 0 <= vi < len(sh["env"]):
            mouth_val = float(sh["env"][vi])
            mouth_val = mouth_val if mouth_val > 0.12 else 0
    shake = 0
    flash = 0

    portal_x, portal_y = 1080, 400
    if "portal_open" in fx:
        portal(ov, portal_x, portal_y, min(1, lt / 0.8) * 170, gt)
    if "portal" in fx:
        portal(ov, portal_x if "fall_in" not in fx else 1060, portal_y, 170 if "fall_in" not in fx else max(0, 170 - max(0, lt - 1.2) * 300), gt)

    # анимация позиций
    pos = {}
    for kind, x, face in chars:
        pos[kind] = [x, GROUND, face, 1.0]
    if "enter_portal" in fx:
        k = min(1, lt / 1.8)
        pos["rick"][0] = 420 + (portal_x - 420) * k ** 1.5
        pos["morty"][0] = 820 + (portal_x - 820) * min(1, k * 1.4) ** 1.5
        for c in ("rick", "morty"):
            if pos[c][0] > portal_x - 40:
                pos[c][3] = 0
    if "fall_in" in fx:
        for c, x0 in (("rick", 520), ("morty", 760)):
            delay = 0 if c == "rick" else 0.2
            k = min(1, max(0, (lt - delay) / 0.35))
            pos[c][0] = 1060 + (x0 - 1060) * k
            pos[c][1] = 400 + (GROUND - 400) * k ** 2 if k < 1 else GROUND
            if lt < delay:
                pos[c][3] = 0
        shake = 6 if 0.3 < lt < 0.7 else 0
    if "evil_appear" in fx:
        k = min(1, max(0, (lt - 0.5) / 0.8))
        chars.append(("evil", 960, -1))
        pos["evil"] = [960, GROUND, -1, k]
        aura(ov, 960, GROUND - 160, 120, 200, (150, 50, 255), gt)
        flash = 0.5 if 0.9 < lt < 1.05 else 0
    if "prime_appear" in fx:
        k = min(1, max(0, (lt - 0.45) / 0.5))
        chars.append(("prime", 1140, -1))
        pos["prime"] = [1140, GROUND, -1, k]
        pos["evil"][0] = 960 - 60 * min(1, lt / 1.0)
        aura(ov, 1140, GROUND - 220, 130, 260, (255, 40, 40), gt)
        d = ImageDraw.Draw(fg)
        if 0.25 < lt < 0.6:  # молния
            pts = [(1140, 0)]
            r = random.Random(int(lt * 30))
            yy = 0
            while yy < GROUND - 200:
                yy += 60
                pts.append((1140 + r.randint(-50, 50), yy))
            d.line(pts, fill=(255, 255, 255, 255), width=8)
            d.line(pts, fill=(255, 120, 120, 255), width=3)
            flash = 0.8
            shake = 10
    for c in ("evil", "prime"):
        if c in pos and "evil_appear" not in fx and "prime_appear" not in fx:
            aura(ov, pos[c][0], GROUND - (160 if c == "evil" else 220), 110 if c == "evil" else 130, 200 if c == "evil" else 260,
                 (150, 50, 255) if c == "evil" else (255, 40, 40), gt)

    if "battle" in fx or "battle_light" in fx:
        d = ImageDraw.Draw(fg)
        shots_t = [0.3, 0.7, 1.6, 2.0, 2.3, 3.4, 3.7, 4.6, 5.0] if "battle" in fx else [0.4, 1.1, 1.7]
        for i, st in enumerate(shots_t):
            if st <= lt < st + 0.25:
                k = (lt - st) / 0.25
                if i % 2 == 0:  # Рик стреляет в Прайма
                    x1, y1, x2, y2, col = 330, GROUND - 175, 1010, GROUND - 230, (90, 255, 120)
                else:          # Прайм стреляет в Рика
                    x1, y1, x2, y2, col = 1010, GROUND - 175, 330, GROUND - 230, (255, 60, 60)
                hx, hy = x1 + (x2 - x1) * k, y1 + (y2 - y1) * k
                tx, ty = x1 + (x2 - x1) * max(0, k - 0.35), y1 + (y2 - y1) * max(0, k - 0.35)
                d.line([(tx, ty), (hx, hy)], fill=col + (120,), width=18)
                d.line([(tx, ty), (hx, hy)], fill=(255, 255, 255, 255), width=5)
        booms = [1.0, 2.6, 4.1, 5.2] if "battle" in fx else [0.2]
        if "escape_portal" in fx:
            booms = [0.8]
        for i, bt in enumerate(booms):
            if bt <= lt < bt + 0.9:
                k = (lt - bt) / 0.9
                bx = [620, 900, 450, 700][i % 4]
                by = GROUND - 60
                for j in range(5):
                    rr = (40 + j * 35) * (0.3 + k)
                    col = [(255, 255, 220), (255, 230, 90), (255, 150, 40), (220, 70, 20), (90, 60, 60)][j]
                    d.ellipse((bx - rr, by - rr * 0.8, bx + rr, by + rr * 0.8), fill=col + (int(255 * (1 - k) * (1 - j * 0.12)),))
                shake = max(shake, int(14 * (1 - k)))
                if k < 0.1:
                    flash = 0.6
        # Злой Морти — энергетический щит
        aura(ov, pos["evil"][0], GROUND - 150, 140, 190, (120, 180, 255), gt)
    if "escape_portal" in fx:
        portal(ov, 150, 420, min(1, lt / 0.6) * 170, gt)
        k = max(0, min(1, (lt - 0.5) / 1.2))
        pos["rick"][0] = 260 - 110 * k
        pos["morty"][0] = 120 + 30 * k
        if lt > 1.8:
            pos["morty"][3] = max(0, 1 - (lt - 1.8) * 3)

    im = Image.alpha_composite(im, ov)
    chl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for kind, *_ in chars:
        x, y, face, alpha = pos[kind]
        if alpha <= 0:
            continue
        layer = chl if alpha >= 1 else Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(layer)
        m = mouth_val if kind == speaker else 0
        draw_char(dl, kind, x, y, m, face, gt + hash(kind) % 7)
        if alpha < 1:
            a = layer.getchannel("A").point(lambda v: int(v * alpha))
            layer.putalpha(a)
            chl = Image.alpha_composite(chl, layer)
    im = Image.alpha_composite(im, chl)
    if "device" in fx:  # прибор в руке Рика
        d = ImageDraw.Draw(im)
        x, y = pos["rick"][0] + 70, GROUND - 200
        d.rounded_rectangle((x - 18, y - 40, x + 18, y + 10), radius=6, fill=(60, 60, 70), outline=OUTL, width=3)
        on = int(gt * 3) % 2
        ell(d, x, y - 20, 10, 10, (255, 40, 40) if on else (120, 20, 20), 2)
        d.line([(x, y - 40), (x, y - 70)], fill=OUTL, width=3)
    if "enter_portal" in fx or "portal" in fx:  # передняя кромка портала поверх персонажей
        pass
    im = Image.alpha_composite(im, fg)
    if flash:
        im = Image.blend(im, Image.new("RGBA", (W, H), (255, 255, 255, 255)), flash * 0.6)
    im = im.convert("RGB")
    if shake:
        dx, dy = random.randint(-shake, shake), random.randint(-shake, shake)
        base = Image.new("RGB", (W, H), (0, 0, 0))
        base.paste(im, (dx, dy))
        im = base
    if speaker and sh["vstart"] - 0.1 <= lt:
        subtitle(im, speaker, sh["line"][1])
    # плавные переходы между локациями
    return im


# ----------------------------------------------------------------------------
# РЕНДЕР
# ----------------------------------------------------------------------------
def main():
    nframes = int(TOTAL * FPS)
    print(f"Длительность: {TOTAL:.1f} c, кадров: {nframes}", flush=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav_path,
           "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-ac", "2", "-shortest", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    si = 0
    for f in range(nframes):
        gt = f / FPS
        while si < len(SHOTS) - 1 and gt >= SHOTS[si + 1]["start"]:
            si += 1
        sh = SHOTS[si]
        im = render_frame(sh, gt - sh["start"], gt)
        p.stdin.write(im.tobytes())
        if f % 240 == 0:
            print(f"  кадр {f}/{nframes}", flush=True)
    p.stdin.close()
    p.wait()
    print("Готово:", OUT)


if __name__ == "__main__":
    main()
