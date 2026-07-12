import paramiko, sys, base64, time

HOST = "connect.bjm1.seetacloud.com"
PORT = 40458
USER = "root"
PWD = "NIgDNE+SPYSM"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Retry connection - autodl instances sometimes refuse on first attempt
for attempt in range(5):
    try:
        ssh.connect(HOST, port=PORT, username=USER, password=PWD, timeout=30, banner_timeout=30, auth_timeout=30)
        break
    except Exception as e:
        print(f"Attempt {attempt+1} failed: {e}")
        if attempt == 4:
            raise
        time.sleep(3)

def run(cmd, timeout=60):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', 'replace')
    err = stderr.read().decode('utf-8', 'replace')
    return out, err

# Step 1: backup current file
out, err = run("cp /root/carpo_sdk/carpo_oac_bridge.py /root/carpo_sdk/carpo_oac_bridge.py.bak.$(date +%s)")
print("BACKUP:", repr(out), repr(err))

# Step 2: read current push_video method to find it
out, err = run("grep -n 'def push_video\\|def advance_timestamp' /root/carpo_sdk/carpo_oac_bridge.py")
print("GREP:", repr(out), repr(err))

# Step 3: write a Python script on remote that does the replacement
new_push = r'''    def push_video(self, frame_bgr):
        if not self._running:
            return
        try:
            import av
            from fractions import Fraction
            frame = av.VideoFrame.from_ndarray(frame_bgr, format='bgr24')
            frame.pts = self._frame_count
            frame.time_base = Fraction(1, self._fps)
            with self._lock:
                ts = self._ts_ms
                pkts = list(self._h264_enc.encode(frame))
                if pkts:
                    sc = bytes([0, 0, 0, 1])
                    for pkt in pkts:
                        raw = bytes(pkt)
                        nals = []
                        pos = 0
                        while pos < len(raw) - 4:
                            if raw[pos:pos+4] == sc:
                                nxt = raw.find(sc, pos+4)
                                if nxt > 0:
                                    nals.append(raw[pos:nxt])
                                    pos = nxt
                                else:
                                    nals.append(raw[pos:])
                                    pos = len(raw)
                            else:
                                pos += 1
                        if not nals:
                            nals = [raw]
                        for nal in nals:
                            nt = nal[4] & 0x1f if len(nal) > 4 else -1
                            buf = (ctypes.c_uint8 * len(nal)).from_buffer_copy(nal)
                            self._lib.carpo_push_send(self._pusher, 1, buf, len(nal), ts)
                            if self._frame_count < 10:
                                print(f"[bridge] NAL type={nt} size={len(nal)}", flush=True)
                        if self._video_hook:
                            self._video_hook(raw)
                    if self._frame_count < 5:
                        print(f"[bridge] video frame #{self._frame_count}: {len(pkts)} pkts, {len(nals)} NALs", flush=True)
                elif self._frame_count < 5:
                    print(f"[bridge] video frame #{self._frame_count}: no pkts (buffering)", flush=True)
            self._frame_count += 1
        except Exception as e:
            print(f"[bridge] video push error frame #{self._frame_count}: {e}", flush=True)
'''

# Build the remote python replacement script
remote_repl = '''
import re
path = "/root/carpo_sdk/carpo_oac_bridge.py"
with open(path, "r", encoding="utf-8") as f:
    src = f.read()

NEW = ''' + repr(new_push) + '''

# Replace from "def push_video" up to (not including) "def advance_timestamp"
pat = re.compile(r"    def push_video\\(self.*?(?=\\n    def advance_timestamp)", re.DOTALL)
m = pat.search(src)
if not m:
    print("NOMATCH")
    raise SystemExit(1)
print("FOUND at", m.start(), "-", m.end(), "len", m.end()-m.start())
new_src = src[:m.start()] + NEW + src[m.end():]
with open(path, "w", encoding="utf-8") as f:
    f.write(new_src)
print("WROTE", len(new_src), "bytes")
'''

# base64 encode to avoid escaping issues
b64 = base64.b64encode(remote_repl.encode('utf-8')).decode('ascii')
remote_wrapper = 'echo "' + b64 + '" | base64 -d > /tmp/_fix_bridge.py && /root/autodl-tmp/envs/flashhead/bin/python3 /tmp/_fix_bridge.py'
out, err = run(remote_wrapper)
print("REPL:", repr(out), repr(err))

# Step 4: verify the change
out, err = run("grep -n 'def push_video\\|def advance_timestamp\\|NAL type\\|carpo_push_send' /root/carpo_sdk/carpo_oac_bridge.py")
print("VERIFY:", repr(out), repr(err))

# Step 5: restart carpo_avatar
out, err = run("pkill -f carpo_avatar; sleep 1; nohup bash /root/start_carpo_avatar.sh > /tmp/avatar_server.log 2>&1 &")
print("RESTART:", repr(out), repr(err))

# Step 6: wait 35 seconds
print("WAITING 35s...")
time.sleep(35)

# Step 7: check log
out, err = run("grep 'bridge' /tmp/avatar_server.log | head -15")
print("LOG:", repr(out), repr(err))

# Also check for errors
out, err = run("tail -20 /tmp/avatar_server.log")
print("TAIL:", repr(out), repr(err))

ssh.close()
print("DONE")
