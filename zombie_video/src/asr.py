import json, sys
import numpy as np, soundfile as sf, sherpa_onnx
d = sys.argv[1]
rec = sherpa_onnx.OfflineRecognizer.from_transducer(
    encoder=f"{d}/encoder.onnx", decoder=f"{d}/decoder.onnx", joiner=f"{d}/joiner.onnx",
    tokens=f"{d}/tokens.txt", num_threads=4, decoding_method="modified_beam_search")
audio, sr = sf.read(sys.argv[2], dtype="float32")
# split on silence-ish chunks of 20s with offsets to stay within model limits
words = []
chunk = 15 * sr
i = 0
# find cut points at quiet places
def quiet_cut(pos):
    lo, hi = max(0, pos - 2*sr), min(len(audio), pos + 2*sr)
    win = int(0.05*sr)
    best, bp = 1e9, pos
    for p in range(lo, hi - win, win//2):
        e = float(np.mean(audio[p:p+win]**2))
        if e < best: best, bp = e, p + win//2
    return bp
start = 0
while start < len(audio):
    end = len(audio) if len(audio) - start < chunk + 3*sr else quiet_cut(start + chunk)
    s = rec.create_stream(); s.accept_waveform(sr, audio[start:end]); rec.decode_stream(s)
    r = s.result
    off = start / sr
    for tok, t in zip(r.tokens, r.timestamps):
        if tok.startswith(("▁"," ")) or not words:
            words.append({"w": tok.lstrip("▁ "), "s": off + t})
        else:
            words[-1]["w"] += tok
    start = end
json.dump(words, open(sys.argv[3], "w"), ensure_ascii=False)
print(" ".join(w["w"] for w in words))
for w in words: print(f'{w["s"]:.2f} {w["w"]}')
