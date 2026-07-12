#!/usr/bin/env python3
"""loop_tts_demo.py — 循环 TTS demo (AutoDL 上跑)

循环调 CosyVoice 流式 TTS，push 到 Carpo server。Pull 端能稳定拉到。

用法 (在 268 上):
    export DASHSCOPE_API_KEY="sk-..."
    source /root/autodl-tmp/envs/flashhead/bin/activate
    python3 /root/carpo_sdk/_loop_tts_demo.py --text "你好 这是一个循环测试"
"""
import os, sys, time, argparse, logging, threading, queue
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger("loop_tts")

sys.path.insert(0, '/root/carpo_sdk')
os.environ['LD_LIBRARY_PATH'] = '/root/carpo_sdk:' + os.environ.get('LD_LIBRARY_PATH', '')

# 从 carpo_avatar_server 复用现成 TTS 函数
sys.path.insert(0, '/root/OpenAvatarChat/src')
try:
    from handlers.avatar.flashhead.carpo_avatar_server import (
        tts_cosyvoice_streaming,
        TTS_VOICE, TTS_MODEL, DASHSCOPE_API_KEY,
        CarpoOACBridge,
    )
except Exception:
    # 单独路径：不复用，inline 调用
    from carpo_oac_bridge import CarpoOACBridge
    import dashscope
    from dashscope.audio.tts_v2 import SpeechSynthesizer
    DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY', '')
    TTS_VOICE = os.environ.get('TTS_VOICE', 'longxiaochun')
    TTS_MODEL = os.environ.get('TTS_MODEL', 'cosyvoice-v1')

    def tts_cosyvoice_streaming(text, voice=None, model=None):
        dashscope.api_key = DASHSCOPE_API_KEY
        voice_id = voice or TTS_VOICE
        model_id = model or TTS_MODEL
        chunks = []
        done = threading.Event()

        class CB(SpeechSynthesizer.Callback):
            def on_complete(self): done.set()
            def on_error(self, m): log.error(f"TTS: {m}"); done.set()
            def on_data(self, data): chunks.append(data)

        syn = SpeechSynthesizer(model=model_id, voice=voice_id, callback=CB())
        syn.call(text)
        done.wait(timeout=30)
        if not chunks: return
        raw = b''.join(chunks)
        pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        if len(pcm) > 0:
            chunk_size = 960  # 20ms @48k
            for i in range(0, len(pcm), chunk_size):
                yield pcm[i:i + chunk_size]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--server', default='192.144.156.158')
    p.add_argument('--port', type=int, default=23800)
    p.add_argument('--text', default='你好，这是一个循环测试。')
    p.add_argument('--voice', default=None)
    p.add_argument('--interval', type=float, default=0.5)
    p.add_argument('--input-sr', type=int, default=24000, help='CosyVoice 原生 24k')
    args = p.parse_args()

    bridge = CarpoOACBridge(
        server_ip=args.server, server_port=args.port,
        audio_ssrc=12345, video_ssrc=67890,
        uid='loop_tts_demo', input_sample_rate=args.input_sr, target_fps=25,
    )
    bridge.start()
    log.info(f"Pusher started, looping TTS text={args.text!r} sr={args.input_sr}")

    cycle = 0
    try:
        while True:
            cycle += 1
            t0 = time.time()
            for chunk in tts_cosyvoice_streaming(args.text, voice=args.voice):
                # CosyVoice 输出 24kHz int16，转 float32 给 bridge input_sr=24k
                if chunk.dtype != np.float32:
                    chunk = chunk.astype(np.float32) / 32768.0
                bridge.push_audio(chunk)
            time.sleep(max(0.0, args.interval))
            log.info(f"cycle={cycle} tts={(time.time()-t0):.2f}s")
    except KeyboardInterrupt:
        log.info("loop stop")
    finally:
        bridge.stop()


if __name__ == '__main__':
    main()
