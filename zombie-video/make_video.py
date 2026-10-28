"""Рисует мультик «Побег от зомби» и собирает его в MP4 через ffmpeg."""
import math
import random
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
FPS = 30
DURATION = 20
GROUND = 600
SPEED = 330            # скорость бегуна, пикселей мира в секунду
RUNNER_SCREEN_X = 760  # где бегун стоит на экране, пока камера едет за ним
HOUSE_X = 15.5 * SPEED + RUNNER_SCREEN_X  # бегун добегает до дома на 15.5 с
CRATES = [1500, 2600, 3500, 4300]
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

random.seed(7)
STARS = [(random.randrange(W), random.randrange(GROUND - 250), random.random()) for _ in range(120)]


def skyline(seed, count, min_h, max_h):
    rng = random.Random(seed)
    x, out = 0, []
    while len(out) < count:
        w = rng.randint(90, 180)
        h = rng.randint(min_h, max_h)
        windows = [(wx, wy, rng.random() < 0.35)
                   for wx in range(12, w - 20, 26) for wy in range(16, h - 20, 34)]
        out.append((x, w, h, windows))
        x += w + rng.randint(4, 30)
    return out, x


FAR, FAR_LEN = skyline(1, 40, 140, 320)
NEAR, NEAR_LEN = skyline(2, 40, 90, 220)


def runner_world_x(t):
    return min(t * SPEED, HOUSE_X - RUNNER_SCREEN_X + 40) + RUNNER_SCREEN_X - 0


def camera_x(t):
    return min(t * SPEED, HOUSE_X - RUNNER_SCREEN_X - 220)


def jump_height(x):
    """Высота прыжка над ящиком: парабола, пока персонаж рядом с ним."""
    for c in CRATES:
        d = x - c
        if -110 < d < 110:
            return 120 * (1 - (d / 110) ** 2)
    return 0


def limb(draw, a, b, color, width):
    draw.line([a, b], fill=color, width=width)
    r = width // 2
    for p in (a, b):
        draw.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=color)


def leg(draw, hip, phase, color, length=46, width=11):
    thigh = math.radians(90 + 35 * math.sin(phase))
    shin = thigh + math.radians(max(0, 70 * math.sin(phase + 1.4)))
    knee = (hip[0] + length * math.cos(thigh) * 0.55, hip[1] + length * math.sin(thigh) * 0.55)
    foot = (knee[0] - length * math.cos(shin + 0.4) * 0.5, knee[1] + length * 0.5)
    limb(draw, hip, knee, color, width)
    limb(draw, knee, foot, color, width)


def draw_runner(draw, x, y, t, scared):
    phase = t * 14
    bob = abs(math.sin(phase)) * -6
    hip = (x, y - 52 + bob)
    neck = (x + 14, y - 112 + bob)
    back, front = (40, 60, 120), (60, 90, 170)
    leg(draw, hip, phase + math.pi, back)
    limb(draw, neck, (neck[0] - 26 * math.sin(phase), neck[1] + 30), (200, 150, 110), 9)
    limb(draw, hip, neck, (220, 60, 50), 22)  # футболка
    leg(draw, hip, phase, front)
    limb(draw, neck, (neck[0] + 26 * math.sin(phase), neck[1] + 30), (230, 180, 140), 9)
    head = (neck[0] + 6, neck[1] - 20)
    draw.ellipse([head[0] - 16, head[1] - 16, head[0] + 16, head[1] + 16], fill=(235, 190, 150))
    draw.chord([head[0] - 17, head[1] - 18, head[0] + 17, head[1] + 6], 180, 360, fill=(60, 40, 30))
    draw.ellipse([head[0] + 5, head[1] - 4, head[0] + 11, head[1] + 2], fill="white")
    draw.ellipse([head[0] + 7, head[1] - 2, head[0] + 10, head[1] + 1], fill="black")
    if scared:
        draw.ellipse([head[0] + 4, head[1] + 6, head[0] + 12, head[1] + 13], fill=(90, 20, 20))
        for i in range(3):  # капли пота
            sx = head[0] - 22 - i * 8
            sy = head[1] - 14 + i * 5 + (t * 60 % 10)
            draw.ellipse([sx - 3, sy - 4, sx + 3, sy + 4], fill=(150, 200, 255))


def draw_zombie(draw, x, y, t, seed):
    phase = t * 7 + seed
    bob = math.sin(phase * 2) * 4
    hip = (x, y - 50 + bob)
    neck = (x + 10, y - 108 + bob)
    skin = (110, 170, 90)
    leg(draw, hip, phase * 0.8 + math.pi, (60, 50, 70), width=12)
    limb(draw, hip, neck, (90, 80, 60), 24)  # рваная одежда
    leg(draw, hip, phase * 0.8, (80, 70, 90), width=12)
    for k in (0, 1):  # руки вытянуты вперёд
        sway = math.sin(phase + k) * 6
        limb(draw, (neck[0], neck[1] + 8 + k * 6), (neck[0] + 52, neck[1] + 4 + k * 10 + sway), skin, 9)
    head = (neck[0] + 4 + math.sin(phase) * 3, neck[1] - 20)
    draw.ellipse([head[0] - 17, head[1] - 17, head[0] + 17, head[1] + 17], fill=skin)
    for ex in (2, 10):
        draw.ellipse([head[0] + ex - 3, head[1] - 6, head[0] + ex + 3, head[1]], fill=(255, 60, 40))
    draw.line([head[0] + 2, head[1] + 9, head[0] + 13, head[1] + 7], fill=(40, 20, 20), width=3)


def draw_city(draw, cam, t):
    for i in range(GROUND):  # градиент неба
        k = i / GROUND
        draw.line([0, i, W, i], fill=(int(10 + 30 * k), int(10 + 20 * k), int(35 + 50 * k)))
    for sx, sy, b in STARS:
        a = int(140 + 115 * math.sin(t * 3 + b * 10) * b)
        draw.point((sx, sy), fill=(a, a, a))
    draw.ellipse([1020, 70, 1120, 170], fill=(245, 240, 210))
    draw.ellipse([1045, 60, 1135, 150], fill=(25, 20, 50))
    for layer, length, k, base in ((FAR, FAR_LEN, 0.25, (30, 30, 55)), (NEAR, NEAR_LEN, 0.55, (20, 20, 38))):
        off = -(cam * k) % length
        for rep in (0, 1):
            for bx, bw, bh, windows in layer:
                x0 = bx + off - length * rep
                if x0 > W or x0 + bw < 0:
                    continue
                draw.rectangle([x0, GROUND - bh, x0 + bw, GROUND], fill=base)
                for wx, wy, lit in windows:
                    c = (250, 210, 100) if lit else (45, 45, 70)
                    draw.rectangle([x0 + wx, GROUND - bh + wy, x0 + wx + 12, GROUND - bh + wy + 16], fill=c)
    draw.rectangle([0, GROUND, W, H], fill=(45, 40, 45))
    for i in range(-1, W // 120 + 2):  # разметка дороги
        x = i * 120 - cam % 120
        draw.rectangle([x, GROUND + 55, x + 60, GROUND + 63], fill=(200, 190, 120))


def draw_house(draw, x, door_open):
    draw.rectangle([x, GROUND - 260, x + 300, GROUND], fill=(110, 70, 55))
    draw.polygon([(x - 30, GROUND - 260), (x + 150, GROUND - 360), (x + 330, GROUND - 260)], fill=(70, 40, 40))
    draw.rectangle([x + 190, GROUND - 200, x + 270, GROUND - 130], fill=(250, 220, 120))
    draw.rectangle([x + 40, GROUND - 160, x + 130, GROUND], fill=(30, 20, 15))
    if not door_open:
        draw.rectangle([x + 40, GROUND - 160, x + 130, GROUND], fill=(150, 90, 50))
        draw.ellipse([x + 112, GROUND - 85, x + 122, GROUND - 75], fill=(230, 200, 80))


def text(draw, msg, size, y, alpha, color=(255, 255, 255)):
    if alpha <= 0:
        return
    font = ImageFont.truetype(FONT, size)
    box = draw.textbbox((0, 0), msg, font=font)
    x = (W - (box[2] - box[0])) / 2
    c = tuple(int(v * alpha) for v in color)
    draw.text((x + 4, y + 4), msg, font=font, fill=(0, 0, 0))
    draw.text((x, y), msg, font=font, fill=c)


def frame(t):
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    cam = camera_x(t)
    draw_city(draw, cam, t)

    rx = runner_world_x(t)
    is_inside = rx >= HOUSE_X + 80
    draw_house(draw, HOUSE_X - cam, door_open=not (is_inside and t > 16.3))

    for c in CRATES:
        sx = c - cam
        if -80 < sx < W + 80:
            draw.rectangle([sx - 32, GROUND - 60, sx + 32, GROUND], fill=(150, 100, 50), outline=(90, 55, 25), width=5)
            draw.line([sx - 32, GROUND - 60, sx + 32, GROUND], fill=(90, 55, 25), width=5)

    # Зомби отстают от бегуна; отставание дышит, чтобы погоня казалась напряжённой.
    for i, base_gap in enumerate((330, 470, 600)):
        gap = base_gap + 70 * math.sin(t * 0.9 + i)
        zx = min(rx - gap, HOUSE_X - 30 - i * 70)
        sx = zx - cam
        if -100 < sx < W + 100:
            draw_zombie(draw, sx, GROUND - jump_height(zx) * 0.5, t, i * 2.1)

    if not is_inside:
        draw_runner(draw, rx - cam, GROUND - jump_height(rx), t, scared=True)

    text(draw, "ПОБЕГ ОТ ЗОМБИ", 76, 230, min(1, t / 0.6) * max(0, min(1, (3 - t) / 0.6)), (240, 70, 60))
    text(draw, "БЕГИ!!!", 64, 120, max(0, min(1, (t - 6) / 0.3)) * max(0, min(1, (8 - t) / 0.3)))
    text(draw, "Они догоняют...", 48, 120, max(0, min(1, (t - 11) / 0.3)) * max(0, min(1, (13 - t) / 0.3)))
    text(draw, "СПАССЯ!", 96, 200, max(0, min(1, (t - 16.8) / 0.5)), (120, 240, 120))
    return img


def main(out):
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE,
    )
    for n in range(DURATION * FPS):
        ff.stdin.write(frame(n / FPS).tobytes())
    ff.stdin.close()
    sys.exit(ff.wait())


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "zombie_chase.mp4")
