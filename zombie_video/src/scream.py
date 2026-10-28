import sys, numpy as np, soundfile as sf
sr = 44100
voice, vsr = sf.read(sys.argv[1], dtype="float32")
assert vsr == sr
start, dur, total = (float(sys.argv[3]), 2.6, float(sys.argv[4])) if len(sys.argv) > 4 else (34.7, 2.6, 38.6)
t = np.arange(int(dur * sr)) / sr
f0 = 520 + 260 * np.minimum(t / 0.4, 1) - 120 * np.maximum(t - 1.6, 0) + 25 * np.sin(2 * np.pi * 6.5 * t)
ph = 2 * np.pi * np.cumsum(f0) / sr
sig = sum((1 / k) * np.sin(k * ph) for k in range(1, 12))
# vowel "А" formants via simple resonant emphasis + breath noise
noise = np.random.default_rng(1).standard_normal(len(t)) * 0.15
sig = sig + noise
env = np.minimum(t / 0.08, 1) * np.clip((dur - t) / 0.9, 0, 1)
sig = np.tanh(sig * 1.6) * env
# echo for a "corridor" feel
out = sig.copy()
for d, g in ((0.11, 0.45), (0.23, 0.3), (0.37, 0.18)):
    n = int(d * sr); out[n:] += g * sig[:-n]
out = out / np.max(np.abs(out)) * 0.8
mix = np.zeros(int(total * sr), dtype=np.float32)
mix[:len(voice)] += voice
s0 = int(start * sr); mix[s0:s0 + len(out)] += out.astype(np.float32)
mix = mix / max(1.0, np.max(np.abs(mix)) / 0.98)
sf.write(sys.argv[2], mix, sr)
