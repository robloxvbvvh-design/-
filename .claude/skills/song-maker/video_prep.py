#!/usr/bin/env python3
"""Готовит видео к написанию песни: лист кадров, длительность и темп (BPM) звука."""
import argparse
import json
import os
import subprocess
import tempfile

import numpy as np
from PIL import Image


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type",
         "-of", "json", path], capture_output=True, text=True, check=True).stdout
    info = json.loads(out)
    kinds = {s["codec_type"] for s in info.get("streams", [])}
    return float(info["format"]["duration"]), "audio" in kinds


def contact_sheet(path, duration, out, n=9):
    with tempfile.TemporaryDirectory() as tmp:
        frames = []
        for i in range(n):
            t = duration * (i + 0.5) / n
            f = os.path.join(tmp, f"{i}.jpg")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", path,
                            "-frames:v", "1", "-vf", "scale=480:-2", f], check=True)
            if os.path.exists(f):
                frames.append(Image.open(f).convert("RGB"))
        if not frames:
            raise SystemExit("не удалось достать кадры из видео")
        w, h = frames[0].size
        cols = 3
        rows = (len(frames) + cols - 1) // cols
        sheet = Image.new("RGB", (w * cols, h * rows), (0, 0, 0))
        for i, fr in enumerate(frames):
            sheet.paste(fr.resize((w, h)), ((i % cols) * w, (i // cols) * h))
        sheet.save(out, quality=88)


def tempo(path):
    """Грубая оценка BPM по огибающей громкости (автокорреляция)."""
    sr = 22050
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar",
                          str(sr), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    if x.size < sr * 3:
        return None, None
    hop = 512
    frames = x[: x.size // hop * hop].reshape(-1, hop)
    env = np.sqrt((frames ** 2).mean(axis=1))
    loud = float(20 * np.log10(env.mean() + 1e-9))
    onset = np.maximum(0, np.diff(env))
    onset -= onset.mean()
    ac = np.correlate(onset, onset, mode="full")[onset.size - 1:]
    fps = sr / hop
    lo, hi = int(fps * 60 / 180), int(fps * 60 / 70)
    if hi >= ac.size:
        return None, loud
    lag = lo + int(np.argmax(ac[lo:hi]))
    return round(60 * fps / lag), round(loud, 1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("outdir")
    a = p.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    duration, has_audio = probe(a.video)
    sheet = os.path.join(a.outdir, "frames.jpg")
    contact_sheet(a.video, duration, sheet)
    bpm, loud = tempo(a.video) if has_audio else (None, None)
    print(json.dumps({"duration_sec": round(duration, 1), "has_audio": has_audio,
                      "bpm_guess": bpm, "loudness_db": loud, "frames": sheet},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
