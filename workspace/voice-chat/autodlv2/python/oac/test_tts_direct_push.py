#!/usr/bin/env python3
"""test_tts_direct_push.py — TTS directly to Carpo, NO FlashHead

If audio is clear: problem is in flashhead_processor
If audio is distorted: problem is in CarpoPushBridge/Carpo link
"""
import os, sys, time, ctypes, threading
import numpy as np

sys.path.insert(0, '/root/carpo_sdk')
os.environ['LD_LIBRARY_PATH'] = '/root/carpo_sdk:' + os.environ.get('LD_LIBRARY_PATH', '')

import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer, ResultCallback, AudioFormat
from scipy.signal import resample_poly
import av

# Carpo SDK
lib = ctypes.CDLL('/root/carpo_sdk/libcarpo.so')
PUSH_EVENT_CB = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int, ctypes.c_void_p)

lib.carpo_push_create.argtypes = [PUSH_EVENT_CB, ctypes.c_void_p]
lib.carpo_push_create.restype = ctypes.c_void_p
lib.carpo_push_set_ssrc.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_char_p]
lib.carpo_push_set_ssrc.restype = ctypes.c_int
lib.carpo_push_set_server.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint16]
lib.carpo_push_set_server.restype = ctypes.c_int
lib.carpo_push_set_video_br.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int]
lib.carpo_push_start.argtypes = [ctypes.c_void_p]
lib.carpo_push_start.restype = ctypes.c_int
lib.carpo_push_send.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_uint8), ctypes.c_uint32, ctypes.c_uint64]
lib.carpo_push_send.restype = ctypes.c_int
lib.carpo_push_stop.argtypes = [ctypes.c_void_p]
lib.carpo_push_destroy.argtypes = [ctypes.c_void_p]

CARPO_SERVER = os.environ.get('CARPO_SERVER', '192.144.156.158')
dashscope.api_key = os.environ.get('DASHSCOPE_API_KEY', '')

# 1. Create Carpo pusher
pusher = lib.carpo_push_create(PUSH_EVENT_CB(lambda e,c,u: None), None)
lib.carpo_push_set_ssrc(pusher, 12345, 67890, b'direct_tts')
lib.carpo_push_set_server(pusher, CARPO_SERVER.encode(), 23800)
lib.carpo_push_set_video_br(pusher, 800000, 400000, 1200000)
lib.carpo_push_start(pusher)
print(f'[push] started to {CARPO_SERVER}:23800')

# 2. TTS
chunks = []
done = [False]
class CB(ResultCallback):
    def on_open(self): print('[tts] opened')
    def on_complete(self): done[0] = True
    def on_error(self, m): print(f'[tts] error: {m}'); done[0] = True
    def on_data(self, data): chunks.append(data)

print('[tts] synthesizing...')
syn = SpeechSynthesizer(model='cosyvoice-v1', voice='longwan',
                        callback=CB(), format=AudioFormat.PCM_24000HZ_MONO_16BIT)
syn.call('你好翀哥，这是直接从TTS推到Carpo的测试，没有经过FlashHead')
time.sleep(5)

raw = b''.join(chunks)
pcm_24k = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
print(f'[tts] {len(pcm_24k)} samples at 24kHz')

# 3. Resample 24k → 48k
pcm_48k = resample_poly(pcm_24k, 48000, 24000)
pcm_48k_int = (np.clip(pcm_48k, -1.0, 1.0) * 32767).astype(np.int16)
print(f'[resample] {len(pcm_48k_int)} samples at 48kHz')

# 4. Opus encode + push
enc = av.CodecContext.create('libopus', 'w')
enc.sample_rate = 48000; enc.layout = 'mono'; enc.format = 's16'; enc.open()

frame_size = 960  # 20ms at 48kHz
ts = 0
sent = 0
for i in range(0, len(pcm_48k_int), frame_size):
    chunk = pcm_48k_int[i:i + frame_size]
    if len(chunk) < frame_size:
        chunk = np.pad(chunk, (0, frame_size - len(chunk)))
    frame = av.AudioFrame.from_ndarray(chunk.reshape(1, -1), format='s16', layout='mono')
    frame.sample_rate = 48000
    for pkt in enc.encode(frame):
        raw_pkt = bytes(pkt)
        buf = (ctypes.c_uint8 * len(raw_pkt)).from_buffer_copy(raw_pkt)
        lib.carpo_push_send(pusher, 0, buf, len(raw_pkt), ts)
        sent += 1
    ts += 20

# Flush
for pkt in enc.encode(None):
    raw_pkt = bytes(pkt)
    buf = (ctypes.c_uint8 * len(raw_pkt)).from_buffer_copy(raw_pkt)
    lib.carpo_push_send(pusher, 0, buf, len(raw_pkt), ts)

print(f'[push] sent {sent} Opus frames')
time.sleep(2)

lib.carpo_push_stop(pusher)
lib.carpo_push_destroy(pusher)
print('[done] Pull this on local machine to compare with raw TTS')
