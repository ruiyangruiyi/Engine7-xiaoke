"""carpo_avatar_server.py — AutoDL 推流服务（Carpo 版）

接收文字 → CosyVoice 流式 TTS → FlashHead processor → Carpo push

不跑 OAC demo.py，不需要 ASR/VAD/fastrtc。
FlashHead processor 原封不动从 OAC 搬过来。

Usage:
    CARPO_SERVER=192.144.156.158 python carpo_avatar_server.py

API:
    POST /generate  {"text": "你好"}  → TTS + FlashHead + Carpo push
    GET  /health                       → {"status": "ok"}
    POST /shutdown                     → graceful shutdown
"""

import argparse
import json
import os
import signal
import sys
import time
import threading
import ctypes
import queue
import traceback
from datetime import datetime

import numpy as np
import torch
from loguru import logger
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
import uvicorn
import pydantic
import asyncio

# =============================================================================
# Paths & Config
# =============================================================================
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
OAC_SRC = "/root/OpenAvatarChat/src"
FLASHHEAD_ALGO = os.path.join(OAC_SRC, "handlers/avatar/flashhead/SoulX-FlashHead")

# Add paths
sys.path.insert(0, "/root/OpenAvatarChat/src/handlers")
sys.path.insert(0, "/root/OpenAvatarChat/src")
sys.path.insert(0, FLASHHEAD_ALGO)
sys.path.insert(0, "/root/carpo_sdk")
os.environ['LD_LIBRARY_PATH'] = '/root/carpo_sdk:' + os.environ.get('LD_LIBRARY_PATH', '')

# Config from env
CARPO_SERVER = os.environ.get('CARPO_SERVER', '192.144.156.158')
CARPO_PORT = int(os.environ.get('CARPO_PORT', '23800'))
DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY', '')
TTS_VOICE = os.environ.get('TTS_VOICE', 'longwan')
TTS_MODEL = os.environ.get('TTS_MODEL', 'cosyvoice-v1')
FLASHHEAD_CKPT = os.environ.get('FLASHHEAD_CKPT', '/root/SoulX-FlashHead/models/SoulX-FlashHead-1_3B')
WAV2VEC_DIR = os.environ.get('WAV2VEC_DIR', '/root/SoulX-FlashHead/models/wav2vec2-base-960h')
COND_IMAGE = os.environ.get('COND_IMAGE', '/root/OpenAvatarChat/resource/avatar/flashhead/girl.png')
PORT = int(os.environ.get('PORT', '8899'))


# =============================================================================
# FlashHead Processor (原封不动从 OAC 搬)
# =============================================================================
from flashhead_processor import FlashHeadProcessor, FlashHeadProcessorCallbacks


# =============================================================================
# CarpoPushBridge (已写好)
# =============================================================================
from carpo_oac_bridge import CarpoOACBridge


# =============================================================================
# TTS - CosyVoice 流式合成
# =============================================================================
def tts_cosyvoice_streaming(text: str, voice: str = None, model: str = None):
    """CosyVoice 流式 TTS，yield PCM chunks (int16, 24kHz, mono).

    Uses dashscope SDK to stream audio.
    """
    import dashscope
    from dashscope.audio.tts_v2 import SpeechSynthesizer, ResultCallback, AudioFormat

    dashscope.api_key = DASHSCOPE_API_KEY
    voice_id = voice or TTS_VOICE
    model_id = model or TTS_MODEL

    # CosyVoice streaming: collect chunks via callback
    chunks = []
    done = threading.Event()

    class Callback(ResultCallback):
        def on_open(self):
            logger.info(f"[tts] CosyVoice stream opened")

        def on_complete(self):
            done.set()

        def on_error(self, message):
            logger.error(f"[tts] CosyVoice error: {message}")
            done.set()

        def on_data(self, data: bytes):
            chunks.append(data)

    # Request PCM 24kHz 16-bit mono directly (no MP3 decode needed)
    synthesizer = SpeechSynthesizer(
        model=model_id, voice=voice_id,
        callback=Callback(),
        format=AudioFormat.PCM_24000HZ_MONO_16BIT,
    )
    synthesizer.call(text)

    # Wait for completion
    done.wait(timeout=30)

    # Concatenate and decode
    if not chunks:
        logger.warning("[tts] No audio chunks received")
        return

    raw_audio = b''.join(chunks)

    # CosyVoice returns PCM 24kHz 16-bit mono (we requested it)
    pcm_24k = np.frombuffer(raw_audio, dtype=np.int16).astype(np.float32) / 32768.0
    if len(pcm_24k) == 0:
        logger.warning("[tts] Empty PCM data")
        return

    # Resample 24kHz → 16kHz for FlashHead inference
    from scipy.signal import resample_poly
    pcm_16k = resample_poly(pcm_24k, 16000, 24000)

    # Yield BOTH versions: (16k for inference, 24k original for playback)
    chunk_size = 1600  # ~100ms at 16kHz
    for i in range(0, len(pcm_16k), chunk_size):
        j = int(i * 24000 / 16000)  # Corresponding index in 24k
        j_end = int((i + chunk_size) * 24000 / 16000)
        yield pcm_16k[i:i + chunk_size], pcm_24k[j:j_end]


# =============================================================================
# Avatar Server
# =============================================================================
class AvatarServer:
    def __init__(self):
        self.pipeline = None
        self.processor = None
        self.carpo_bridge = None
        self.infer_params = None
        self._lock = threading.Lock()
        self._busy = False
        self._mute_idle = False  # Mute idle audio during generate
        self._video_queue = queue.Queue()  # H.264 raw bytes for WebSocket streaming
        self._audio_queue = queue.Queue()  # Opus raw bytes for WebSocket streaming

    def load_models(self):
        """Load FlashHead pipeline (takes ~10s on 4090)."""
        logger.info("[avatar] Loading FlashHead pipeline...")

        # Patch torch.load for compatibility
        _orig = torch.load
        def _patched(*args, **kwargs):
            if 'weights_only' not in kwargs:
                kwargs['weights_only'] = False
            return _orig(*args, **kwargs)
        torch.load = _patched

        from flash_head.inference import get_pipeline

        self.infer_params = {
            "sample_rate": 16000,
            "tgt_fps": 25,
            "frame_num": 33,
            "motion_frames_num": 9,
            "cached_audio_duration": 8,
            "cond_image_path": COND_IMAGE,
            "model_type": "lite",
            "use_face_crop": False,
        }

        self.pipeline = get_pipeline(
            world_size=1,
            ckpt_dir=FLASHHEAD_CKPT,
            model_type="lite",
            wav2vec_dir=WAV2VEC_DIR,
        )

        # Prepare base data (cond image)
        from flash_head.inference import get_base_data, get_infer_params
        self.infer_params = get_infer_params()
        get_base_data(self.pipeline, COND_IMAGE, 42, False)

        logger.info(f"[avatar] FlashHead pipeline loaded")

    def start_carpo(self):
        """Start Carpo push bridge."""
        self.carpo_bridge = CarpoOACBridge(
            server_ip=CARPO_SERVER,
            server_port=CARPO_PORT,
            audio_ssrc=12345,
            video_ssrc=67890,
            uid='avatar_push',
            input_sample_rate=24000,
            target_fps=25,
        )
        self.carpo_bridge.start()
        self.carpo_bridge.set_video_hook(lambda data: self._video_queue.put(data))
        self.carpo_bridge.set_audio_hook(lambda data: self._audio_queue.put(data))
        logger.info('[avatar] Carpo bridge started with WebSocket video hook')

        # No keepalive needed - FlashHead idle worker keeps pushing frames
        # Start a persistent processor so idle worker runs continuously
        callbacks = self._build_callbacks()
        self.processor = FlashHeadProcessor(
            pipeline=self.pipeline,
            infer_params=self.infer_params,
            output_audio_sample_rate=24000,
            callbacks=callbacks,
        )
        self.processor.start()
        logger.info('[avatar] Persistent processor started (idle worker keeps Carpo alive)')

    def _build_callbacks(self):
        """Build callbacks for flashhead_processor."""
        vcount = [0]
        acount = [0]

        def on_video_frame(frame: np.ndarray):
            vcount[0] += 1
            # Don't push video to Carpo (type=0 channel reserved for audio)
            # Video hook sends H.264 to WebSocket queue instead

        def on_audio_frame(audio: np.ndarray):
            acount[0] += 1
            if acount[0] <= 3:
                print(f"[callback] on_audio_frame #{acount[0]}: shape={audio.shape}, max_abs={np.max(np.abs(audio)):.3f}", flush=True)
            if self.carpo_bridge:
                self.carpo_bridge.push_audio(audio)
                self.carpo_bridge.advance_timestamp()

        return FlashHeadProcessorCallbacks(
            on_video_frame=on_video_frame,
            on_audio_frame=on_audio_frame,
        )

    def generate(self, text: str, tts_provider: str = "cosyvoice"):
        """TTS → Carpo audio push + FlashHead video (for mouth sync)."""
        with self._lock:
            if self._busy:
                return {"ok": False, "error": "Server busy processing another request"}
            self._busy = True

        try:
            t_start = time.time()

            # TTS
            tts_gen = tts_cosyvoice_streaming(text)
            all_16k = []
            all_24k = []
            for pcm_16k, pcm_24k in tts_gen:
                all_16k.append(pcm_16k)
                all_24k.append(pcm_24k)

            if not all_16k:
                self._busy = False
                return {"ok": False, "error": "TTS produced no audio"}

            full_16k = np.concatenate(all_16k)
            full_24k = np.concatenate(all_24k)
            chunk_count = len(all_16k)
            logger.info(f"[avatar] TTS: {len(full_16k)} samples 16k, {len(full_24k)} samples 24k")

            # Mute idle audio while pushing TTS
            self._mute_idle = True

            # Push TTS audio directly to Carpo (24kHz → bridge resamples to 48k → Opus)
            if self.carpo_bridge:
                chunk_size = 960  # 40ms at 24kHz = match FlashHead frame timing
                for i in range(0, len(full_24k), chunk_size):
                    chunk = full_24k[i:i + chunk_size]
                    if len(chunk) > 0:
                        self.carpo_bridge.push_audio(chunk)
                        self.carpo_bridge.advance_timestamp()
                logger.info(f"[avatar] Audio pushed to Carpo: {len(full_24k)} samples")

            # Unmute idle audio
            self._mute_idle = False

            # Feed to FlashHead for video (mouth sync)
            if self.processor:
                cs = 1600
                for i in range(0, len(full_16k), cs):
                    c16k = full_16k[i:i + cs]
                    j = int(i * 24000 / 16000)
                    j_end = int((i + cs) * 24000 / 16000)
                    c24k = full_24k[j:j_end] if j < len(full_24k) else np.zeros(1, dtype=np.float32)
                    self.processor.add_audio(c16k, c24k, speech_id="req", end_of_speech=False)
                self.processor.add_audio(
                    np.zeros(1, dtype=np.float32), np.zeros(1, dtype=np.float32),
                    speech_id="req", end_of_speech=True
                )

            # Wait for video inference
            wait_sec = max(5.0, chunk_count * 1.0)
            time.sleep(wait_sec)

            elapsed = time.time() - t_start
            logger.info(f"[avatar] Generate complete in {elapsed:.1f}s")
            return {"ok": True, "timing": {"total": round(elapsed, 1)}, "chunks": chunk_count}

        except Exception as e:
            logger.error(f"[avatar] Generate error: {e}")
            traceback.print_exc()
            return {"ok": False, "error": str(e)}
        finally:
            with self._lock:
                self._busy = False
                self._mute_idle = False  # Always unmute after generate


# =============================================================================
# FastAPI App
# =============================================================================
app = FastAPI(title="Carpo Avatar Server")
server = AvatarServer()


class GenerateRequest(pydantic.BaseModel):
    text: str
    tts_provider: str = "cosyvoice"


@app.on_event("startup")
async def startup():
    logger.info("[server] Starting Carpo Avatar Server...")
    server.load_models()
    server.start_carpo()
    logger.info(f"[server] Ready! Carpo → {CARPO_SERVER}:{CARPO_PORT}")


@app.get("/health")
async def health():
    return {"status": "ok", "models_loaded": server.pipeline is not None}


@app.post("/generate")
async def generate(req: GenerateRequest):
    result = server.generate(req.text, req.tts_provider)
    return JSONResponse(result)


@app.websocket("/ws/generate")
async def ws_generate(websocket: WebSocket):
    """Bidirectional: receive text, stream H.264 video + Opus audio back."""
    await websocket.accept()
    logger.info("[ws] Client connected")
    try:
        while True:
            msg = await websocket.receive_text()
            text = msg.strip()
            if not text:
                continue
            if text == "close":
                break

            logger.info(f"[ws] generate: {text!r}")
            import concurrent.futures
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = await loop.run_in_executor(
                    pool, server.generate, text, "cosyvoice"
                )
            logger.info(f"[ws] result: {result}")

            # Stream BOTH video and audio from queues
            v_sent = 0; a_sent = 0
            for _ in range(120):
                drained = False
                # Video (H.264 NAL)
                try:
                    data = server._video_queue.get_nowait()
                    # Tag: 0x00 = video
                    await websocket.send_bytes(bytes([0]) + data)
                    v_sent += 1
                    drained = True
                except queue.Empty:
                    pass
                # Audio (Opus)
                try:
                    data = server._audio_queue.get_nowait()
                    # Tag: 0x01 = audio
                    await websocket.send_bytes(bytes([1]) + data)
                    a_sent += 1
                    drained = True
                except queue.Empty:
                    pass
                if not drained:
                    await asyncio.sleep(0.03)
                if v_sent > 0 and a_sent > 0 and not drained:
                    break
            logger.info(f"[ws] sent video={v_sent} audio={a_sent}")
    except Exception as e:
        logger.info(f"[ws] disconnected: {e}")

@app.post("/shutdown")
async def shutdown():
    logger.info("[server] Shutting down...")
    if server.carpo_bridge:
        server.carpo_bridge.stop()
    os._exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    logger.info(f"[server] Config: CARPO={CARPO_SERVER}:{CARPO_PORT}, PORT={args.port}")
    uvicorn.run(app, host=args.host, port=args.port)
