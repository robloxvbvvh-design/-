# Распознавание речи (GigaAM v2 RNN-T через sherpa-onnx) -> words.json с таймкодами слов.
# Модель: https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-transducer-giga-am-v2-russian-2025-04-19.tar.bz2
# Вход: audio16.wav (ffmpeg -i audio.mp3 -ar 16000 -ac 1 audio16.wav)
import sherpa_onnx, soundfile as sf, json
import sys
d=sys.argv[1] if len(sys.argv)>1 else "sherpa-onnx-nemo-transducer-giga-am-v2-russian-2025-04-19/"
rec=sherpa_onnx.OfflineRecognizer.from_transducer(encoder=d+"encoder.int8.onnx",decoder=d+"decoder.onnx",joiner=d+"joiner.onnx",tokens=d+"tokens.txt",model_type="nemo_transducer",num_threads=4)
a,sr=sf.read("audio16.wav",dtype="float32")
cuts=[0,10.0,18.5,27.6,34.2,43.9,len(a)/sr]
words=[]
for i in range(len(cuts)-1):
    s=rec.create_stream(); off=cuts[i]
    s.accept_waveform(sr,a[int(cuts[i]*sr):int(cuts[i+1]*sr)]); rec.decode_stream(s)
    r=s.result; print(f"[{off:.1f}] {r.text}")
    cur=None
    for t,ts in zip(r.tokens,r.timestamps):
        if t==" ":
            if cur: words.append(cur); cur=None
            continue
        if cur is None: cur={"w":"","s":ts+off}
        cur["w"]+=t; cur["last"]=ts+off
    if cur: words.append(cur)
json.dump(words,open("words.json","w"),ensure_ascii=False,indent=0)
print(len(words))
