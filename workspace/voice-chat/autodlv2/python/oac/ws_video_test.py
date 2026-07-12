"""ws_video_test.py — Connect WebSocket, trigger generate, collect H.264 frames"""
import asyncio
import websockets
import paramiko
import time

AUTODL_HOST = 'connect.bjb1.seetacloud.com'
AUTODL_PORT = 40458
SSH_PASS = 'NIgDNE+SPYSM'
WS_URL = 'ws://localhost:8899/ws/video'


async def main():
    # SSH tunnel for WebSocket
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(AUTODL_HOST, port=AUTODL_PORT, username='root', password=SSH_PASS, timeout=15)

    # Trigger generate
    stdin, stdout, stderr = ssh.exec_command(
        'curl -s -X POST http://localhost:8899/generate -H "Content-Type: application/json" '
        '-d \'{"text": "WebSocket视频测试"}\' --max-time 60 &'
    )
    time.sleep(1)

    # Connect WebSocket via SSH tunnel
    transport = ssh.get_transport()
    channel = transport.open_channel('direct-tcpip', ('127.0.0.1', 8899), ('127.0.0.1', 0))

    # Create a simple raw WebSocket client (no external lib needed for basic test)
    # Instead, let's just use paramiko to forward and curl ws://
    print("[ws] Testing via websocat or direct...")

    # Just check that WebSocket endpoint is reachable
    stdin, stdout, stderr = ssh.exec_command(
        'timeout 10 python3 -c "'
        'import asyncio, websockets; '
        'async def test(): '
        '  async with websockets.connect(\\\"ws://localhost:8899/ws/video\\\") as ws: '
        '    for i in range(5): '
        '      data = await ws.recv(); '
        '      print(f\\\"frame {i}: {len(data)} bytes\\\"); '
        'asyncio.run(test())" '
        '2>&1'
    )
    time.sleep(12)
    print("WS result:", stdout.read().decode())
    print("WS err:", stderr.read().decode()[:500])

    ssh.close()


asyncio.run(main())
