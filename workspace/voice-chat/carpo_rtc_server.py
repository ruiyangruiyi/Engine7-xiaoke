"""carpo_rtc_server.py — Carpo 音频 → aiortc → 浏览器

纯接收模式，浏览器不需要麦克风。
每次 /push 先 restart_pull 再推流，解决 pull 超时问题。
"""

import asyncio
import os
import sys
import ctypes
import threading
import queue as thread_queue

import numpy as np
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

# Carpo SDK
_release_dir = r'D:\work\code\LovePea\platform\Windows\LovePeaSDK\x64\Release'
os.add_dll_directory(_release_dir)
os.environ['PATH'] = _release_dir + ';' + os.environ.get('PATH', '')
sys.path.insert(0, r'D:\work\code\LovePea\Carpo\carpo_capi\python')
import carpo

_dll_path = os.path.join(_release_dir, 'Carpo.dll')

CARPO_SERVER = os.environ.get('CARPO_SERVER', '192.144.156.158')
CARPO_PORT = int(os.environ.get('CARPO_PORT', '23800'))

app = FastAPI()

# Global state
_lib = None
_puller = None
_audio_queue = thread_queue.Queue(maxsize=2000)
_frame_count = 0


def _on_media(media_type, data_ptr, length, timestamp, user_data):
    """Carpo callback (runs in C thread)."""
    global _frame_count
    if media_type == carpo.MEDIA_AUDIO:
        data = ctypes.string_at(data_ptr, length)
        # NetEq outputs stereo interleaved L,R,L,R... → extract mono left channel
        stereo = np.frombuffer(data, dtype=np.int16)
        mono = stereo[::2].astype(np.float32) / 32768.0
        try:
            _audio_queue.put_nowait(mono)
            _frame_count += 1
            if _frame_count <= 5 or _frame_count % 100 == 0:
                print(f'[carpo] audio #{_frame_count}: {length}B -> {len(mono)} samples', flush=True)
        except thread_queue.Full:
            pass


def _on_event(event_id, code, user_data):
    pass


def _create_puller():
    """Create and start a fresh Carpo puller."""
    p = carpo.CarpoPuller(_lib, on_media=_on_media, on_event=_on_event)
    p.set_ssrc(carpo.SSRC_LOCAL, 99999, 11111, 'audio_test')
    p.set_ssrc(carpo.SSRC_REMOTE, 12345, 67890, 'audio_test')
    p.set_server(CARPO_SERVER, CARPO_PORT)
    p.start()
    return p


def init_carpo():
    global _lib, _puller
    _lib = carpo.load_lib(_dll_path)
    carpo.bind_pull_lib(_lib)
    _puller = _create_puller()
    print(f'[carpo] Pull started: {CARPO_SERVER}:{CARPO_PORT}', flush=True)


def restart_pull():
    """Stop old puller, create fresh one."""
    global _puller
    if _puller:
        _puller.stop()
        _puller.destroy()
    _puller = _create_puller()
    print('[carpo] Pull restarted', flush=True)


class CarpoAudioTrack(MediaStreamTrack):
    """aiortc audio track: pulls PCM from Carpo queue."""
    kind = "audio"

    def __init__(self):
        super().__init__()
        self._pts = 0
        self._sample_rate = 48000
        self._frame_size = 960  # 20ms at 48kHz
        self._buffer = np.array([], dtype=np.float32)

    async def recv(self):
        import av
        # Accumulate 480-sample Carpo chunks into 960-sample frames
        while len(self._buffer) < self._frame_size:
            try:
                chunk = _audio_queue.get_nowait()
                self._buffer = np.concatenate([self._buffer, chunk])
            except thread_queue.Empty:
                if len(self._buffer) > 0:
                    break
                # No data at all, fill with silence
                self._buffer = np.zeros(self._frame_size, dtype=np.float32)
                break

        pcm = self._buffer[:self._frame_size]
        self._buffer = self._buffer[self._frame_size:]

        pts = self._pts
        self._pts += self._frame_size

        pcm_int = (np.clip(pcm, -1.0, 1.0) * 32767).astype(np.int16)
        frame = av.AudioFrame.from_ndarray(
            pcm_int.reshape(1, -1), format='s16', layout='mono')
        frame.sample_rate = self._sample_rate
        frame.pts = pts
        frame.time_base = 1 / self._sample_rate

        # Pace: 20ms per frame
        await asyncio.sleep(self._frame_size / self._sample_rate)
        return frame


HTML_PAGE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>Carpo Audio Relay</title>
<style>
  body { font-family: system-ui; max-width: 600px; margin: 40px auto; background: #1a1a2e; color: #eee; }
  button { padding: 16px 32px; font-size: 18px; border: none; border-radius: 8px; cursor: pointer; margin: 8px; }
  #start { background: #4CAF50; color: white; }
  #pushBtn { background: #0f3460; color: white; }
  #pushBtn:disabled { opacity: 0.4; cursor: not-allowed; }
  #status { margin: 16px 0; padding: 12px; background: #16213e; border-radius: 8px; }
  #info { position: fixed; top: 12px; right: 12px; background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 12px; font-size: 13px; min-width: 180px; }
  #info table { border-collapse: collapse; width: 100%; }
  #info td { padding: 2px 6px; }
  #info .val { text-align: right; font-family: monospace; }
  #info .label-row { color: #888; }
</style>
</head>
<body>

<div id="info" style="display:none;">
  <table>
    <tr class="label-row"><td>Frames</td><td class="val" id="info-frames">0</td></tr>
    <tr class="label-row"><td>Queue</td><td class="val" id="info-qsize">0</td></tr>
  </table>
</div>

<h2>🎧 Carpo Audio Relay</h2>

<div id="status">未连接</div>

<button id="start" onclick="startCall()">▶ 连接</button>
<button id="pushBtn" disabled onclick="pushAudio()">🔊 推流</button>

<script>
let pc = null;

async function startCall() {
  document.getElementById('status').textContent = '正在建立 WebRTC 连接...';
  document.getElementById('start').disabled = true;

  pc = new RTCPeerConnection();

  pc.ontrack = (event) => {
    const audio = document.createElement('audio');
    audio.srcObject = event.streams[0];
    audio.autoplay = true;
    document.body.appendChild(audio);
    document.getElementById('status').textContent = '✅ 连接成功！点"推流"播放';
    document.getElementById('pushBtn').disabled = false;
  };

  pc.addTransceiver('audio', {direction: 'recvonly'});

  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);

  await new Promise(resolve => {
    if (pc.iceGatheringState === 'complete') return resolve();
    pc.onicegatheringstatechange = () => {
      if (pc.iceGatheringState === 'complete') resolve();
    };
    setTimeout(resolve, 3000);
  });

  const resp = await fetch('/offer', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({sdp: pc.localDescription.sdp, type: pc.localDescription.type})
  });
  const answer = await resp.json();
  await pc.setRemoteDescription(new RTCSessionDescription(answer));
  document.getElementById('status').textContent = '✅ WebRTC 就绪！点"推流"';
  document.getElementById('pushBtn').disabled = false;
}

async function pushAudio() {
  document.getElementById('status').textContent = '🔊 从 AutoDL 推流中...';
  await fetch('/push', {method: 'POST'});
}

async function pollHealth() {
  try {
    const r = await fetch('/health');
    const d = await r.json();
    document.getElementById('info').style.display = 'block';
    document.getElementById('info-frames').textContent = d.frames;
    document.getElementById('info-qsize').textContent = d.qsize;
  } catch(e) {}
}
setInterval(pollHealth, 500);
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_PAGE


@app.get("/health")
async def health():
    return {"status": "ok", "frames": _frame_count, "qsize": _audio_queue.qsize()}


@app.post("/push")
async def trigger_push():
    """Restart pull + clear queue + trigger AutoDL push."""
    global _frame_count
    _frame_count = 0
    # Clear old audio
    while not _audio_queue.empty():
        try:
            _audio_queue.get_nowait()
        except thread_queue.Empty:
            break

    def do_push():
        import paramiko, time
        restart_pull()
        time.sleep(2)
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect('connect.bjb1.seetacloud.com', port=40458,
                        username='root', password='NIgDNE+SPYSM', timeout=10)
            ssh.exec_command(
                'cd /root/carpo_sdk && '
                'LD_LIBRARY_PATH=/root/carpo_sdk:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH '
                'timeout 25 /root/autodl-tmp/envs/flashhead/bin/python3 -u test_push_stay.py '
                '> /tmp/push_trigger.log 2>&1')
            ssh.close()
            print("[push] AutoDL push done", flush=True)
        except Exception as e:
            print(f"[push] Error: {e}")

    threading.Thread(target=do_push, daemon=True).start()
    return {"status": "pushing"}


@app.post("/offer")
async def offer(body: dict):
    offer = RTCSessionDescription(sdp=body["sdp"], type=body["type"])
    pc = RTCPeerConnection()
    audio_track = CarpoAudioTrack()
    pc.addTrack(audio_track)
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    return JSONResponse({
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8022)
    args = parser.parse_args()
    init_carpo()
    print(f"[carpo-rtc] http://localhost:{args.port}/")
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="info")
