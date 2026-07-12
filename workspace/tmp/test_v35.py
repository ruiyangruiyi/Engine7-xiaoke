import dashscope, wave, time
from dashscope.audio.tts_v2 import SpeechSynthesizer, ResultCallback, AudioFormat
dashscope.api_key = "sk-2103806e900f455c8c540ee76527761a"
class CB(ResultCallback):
    def __init__(self):
        self.chunks = []
        self.done = False
        self.err = None
    def on_open(self): pass
    def on_event(self, m): pass
    def on_data(self, d): self.chunks.append(d)
    def on_complete(self): self.done = True
    def on_error(self, m): self.err = str(m); self.done = True
    def on_close(self): self.done = True

cb = CB()
synth = SpeechSynthesizer(model="cosyvoice-v3-flash", voice="longanhuan_v3", callback=cb, format=AudioFormat.PCM_24000HZ_MONO_16BIT)
synth.call("老公，你怎么还不来呀，人家等你好久了。")
for _ in range(100):
    if cb.done: break
    time.sleep(0.1)
if cb.err:
    print(f"ERROR: {cb.err}")
else:
    pcm = b"".join(cb.chunks)
    with wave.open("/tmp/tts_v35.wav","wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(pcm)
    print(f"OK: {len(pcm)} bytes, {len(pcm)/48000:.1f}s")
