#!/usr/bin/env python3
"""Синтезирует простой минус (аккорды + бас + бочка/хэт) и при желании кладёт его на видео."""
import argparse
import subprocess
import wave

import numpy as np

SR = 44100
NOTES = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6,
         "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11, "H": 11}


def chord_freqs(name):
    """'Am' -> частоты трезвучия, 'C' -> мажор, 'G7' -> с септимой."""
    root = name[:2] if name[:2] in NOTES else name[:1]
    rest = name[len(root):]
    steps = [0, 3, 7] if rest.startswith("m") and not rest.startswith("maj") else [0, 4, 7]
    if "7" in rest:
        steps.append(11 if "maj" in rest else 10)
    base = 220 * 2 ** ((NOTES[root] - 9) / 12)
    return [base * 2 ** (s / 12) for s in steps], base / 2


def tone(freq, dur, kind="pad"):
    t = np.arange(int(SR * dur)) / SR
    if kind == "pad":
        w = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t)
        env = np.minimum(1, t / 0.05) * np.exp(-t * 0.8)
    else:
        w = np.sign(np.sin(2 * np.pi * freq * t)) * 0.5 + np.sin(2 * np.pi * freq * t)
        env = np.exp(-t * 6)
    return w * env


def kick(dur):
    t = np.arange(int(SR * dur)) / SR
    return np.sin(2 * np.pi * (50 + 100 * np.exp(-t * 30)) * t) * np.exp(-t * 12)


def hat(dur, rng):
    t = np.arange(int(SR * dur)) / SR
    return rng.uniform(-1, 1, t.size) * np.exp(-t * 60) * 0.25


def build(chords, bpm, seconds):
    beat = 60 / bpm
    bar = beat * 4
    total = int(SR * seconds)
    out = np.zeros(total + SR * 2)
    rng = np.random.default_rng(1)
    pos, i = 0.0, 0
    while pos < seconds:
        freqs, bass = chord_freqs(chords[i % len(chords)])
        s = int(pos * SR)
        pad = sum(tone(f, bar) for f in freqs) * 0.12
        out[s:s + pad.size] += pad
        for b in range(4):
            bs = int((pos + b * beat) * SR)
            k = kick(beat) * 0.6 if b % 2 == 0 else kick(beat) * 0.35
            out[bs:bs + k.size] += k
            bl = tone(bass, beat * 0.9, "bass") * 0.18
            out[bs:bs + bl.size] += bl
            for half in (0, 0.5):
                hs = int((pos + (b + half) * beat) * SR)
                h = hat(beat / 2, rng)
                out[hs:hs + h.size] += h
        pos += bar
        i += 1
    out = out[:total]
    fade = min(total, SR * 2)
    out[-fade:] *= np.linspace(1, 0, fade)
    return out / (np.abs(out).max() + 1e-9) * 0.9


def main():
    p = argparse.ArgumentParser()
    p.add_argument("out_wav")
    p.add_argument("--chords", required=True, help="например: Am,F,C,G")
    p.add_argument("--bpm", type=int, default=100)
    p.add_argument("--seconds", type=float, default=60)
    p.add_argument("--video", help="положить минус на это видео")
    p.add_argument("--video-out")
    p.add_argument("--mix", type=float, default=0.35, help="громкость оригинального звука видео")
    a = p.parse_args()

    audio = build([c.strip() for c in a.chords.split(",") if c.strip()], a.bpm, a.seconds)
    with wave.open(a.out_wav, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((audio * 32767).astype("<i2").tobytes())
    print("wav:", a.out_wav)

    if a.video and a.video_out:
        has_audio = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
             "stream=index", "-of", "csv=p=0", a.video],
            capture_output=True, text=True).stdout.strip()
        if has_audio:
            fc = f"[0:a]volume={a.mix}[o];[1:a]volume=1[m];[o][m]amix=inputs=2:duration=first[a]"
            cmd = ["ffmpeg", "-v", "error", "-y", "-i", a.video, "-i", a.out_wav,
                   "-filter_complex", fc, "-map", "0:v", "-map", "[a]"]
        else:
            cmd = ["ffmpeg", "-v", "error", "-y", "-i", a.video, "-i", a.out_wav,
                   "-map", "0:v", "-map", "1:a", "-shortest"]
        subprocess.run(cmd + ["-c:v", "copy", "-c:a", "aac", a.video_out], check=True)
        print("video:", a.video_out)


if __name__ == "__main__":
    main()
