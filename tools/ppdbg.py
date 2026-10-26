"""Minimal client for the PPSSPP WebSocket debugger (stdlib only).

Usage:
    python3 -m tools.ppdbg [--port N] shot out.png
    python3 -m tools.ppdbg [--port N] press cross [--hold 0.1]
    python3 -m tools.ppdbg [--port N] read 0x08800000 256 out.bin
    python3 -m tools.ppdbg [--port N] call '{"event": "game.status"}'
"""
import argparse
import base64
import json
import os
import socket
import struct
import subprocess
import sys
import time


def encode_frame(payload, opcode=1, mask_key=None):
    mask_key = mask_key if mask_key is not None else os.urandom(4)
    n = len(payload)
    head = bytes([0x80 | opcode])
    if n < 126:
        head += bytes([0x80 | n])
    elif n < 1 << 16:
        head += bytes([0x80 | 126]) + struct.pack(">H", n)
    else:
        head += bytes([0x80 | 127]) + struct.pack(">Q", n)
    masked = bytes(b ^ mask_key[i & 3] for i, b in enumerate(payload))
    return head + mask_key + masked


def decode_frame(buf):
    """Returns (opcode, payload, bytes_consumed) or None if incomplete."""
    if len(buf) < 2:
        return None
    opcode = buf[0] & 0x0F
    masked = buf[1] & 0x80
    n = buf[1] & 0x7F
    p = 2
    if n == 126:
        if len(buf) < 4:
            return None
        n, = struct.unpack_from(">H", buf, 2)
        p = 4
    elif n == 127:
        if len(buf) < 10:
            return None
        n, = struct.unpack_from(">Q", buf, 2)
        p = 10
    key = b""
    if masked:
        if len(buf) < p + 4:
            return None
        key = buf[p:p + 4]
        p += 4
    if len(buf) < p + n:
        return None
    data = bytes(buf[p:p + n])
    if masked:
        data = bytes(b ^ key[i & 3] for i, b in enumerate(data))
    return opcode, data, p + n


def find_port():
    out = subprocess.run(["ss", "-ltnp"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if "PPSSPP" in line:
            return int(line.split()[3].rsplit(":", 1)[1])
    raise RuntimeError("PPSSPP debugger port not found (is RemoteDebuggerOnStartup enabled?)")


def find_window():
    out = subprocess.run(["xwininfo", "-root", "-tree"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if '"org.ppsspp.PPSSPP"' in line and ": (" in line:
            return line.split()[0]
    raise RuntimeError("PPSSPP window not found")


def capture_window(path):
    subprocess.run(["import", "-window", find_window(), path], check=True)


class Debugger:
    def __init__(self, port=None, host="127.0.0.1", timeout=30, attempts=4):
        # right after boot the server sometimes accepts but never answers the
        # upgrade; a fresh connection a few seconds later succeeds
        for i in range(attempts):
            try:
                self._connect(host, port or find_port(), handshake_timeout=30)
                break
            except (TimeoutError, ConnectionError):
                # the server serves one client at a time; a stuck socket
                # left open blocks every later attempt
                if getattr(self, "sock", None):
                    self.sock.close()
                if i == attempts - 1:
                    raise
                time.sleep(2)
        self.sock.settimeout(timeout)
        self.ticket = 0

    def _connect(self, host, port, handshake_timeout):
        self.sock = socket.create_connection((host, port), timeout=handshake_timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((f"GET /debugger HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\n"
                           f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
                           f"Sec-WebSocket-Version: 13\r\n\r\n").encode())
        resp = b""
        while b"\r\n\r\n" not in resp:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("handshake closed")
            resp += chunk
        head, self.buf = resp.split(b"\r\n\r\n", 1)
        if b" 101 " not in head.split(b"\r\n", 1)[0]:
            self.sock.close()
            raise ConnectionError(head.decode(errors="replace"))

    def _recv(self):
        while True:
            r = decode_frame(self.buf)
            if r:
                opcode, data, used = r
                self.buf = self.buf[used:]
                if opcode == 9:  # ping
                    self.sock.sendall(encode_frame(data, opcode=10))
                    continue
                if opcode == 8:
                    raise ConnectionError("debugger closed the connection")
                return json.loads(data)
            chunk = self.sock.recv(1 << 16)
            if not chunk:
                raise ConnectionError("connection closed")
            self.buf += chunk

    def call(self, event, **params):
        self.ticket += 1
        ticket = str(self.ticket)
        msg = dict(params, event=event, ticket=ticket)
        self.sock.sendall(encode_frame(json.dumps(msg).encode()))
        while True:
            r = self._recv()
            # some events (cpu.stepping, cpu.resume) answer with an untagged broadcast
            if r.get("ticket") == ticket or ("ticket" not in r and r.get("event") == event):
                if r.get("event") == "error":
                    raise RuntimeError(r.get("message"))
                return r

    def screenshot(self, path):
        # gpu.buffer.screenshot fails to download the framebuffer on this
        # backend ("Could not download output"), so capture the X11 window
        capture_window(path)

    def press(self, button, hold=0.1):
        self.call("input.buttons.send", buttons={button: True})
        time.sleep(hold)
        self.call("input.buttons.send", buttons={button: False})

    def read(self, address, size):
        r = self.call("memory.read", address=address, size=size)
        return base64.b64decode(r["base64"])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("shot"); s.add_argument("out")
    s = sub.add_parser("press"); s.add_argument("buttons", nargs="+"); s.add_argument("--hold", type=float, default=0.1); s.add_argument("--gap", type=float, default=0.4)
    s = sub.add_parser("read"); s.add_argument("addr"); s.add_argument("size"); s.add_argument("out")
    s = sub.add_parser("call"); s.add_argument("json")
    a = ap.parse_args(argv)
    dbg = Debugger(a.port)
    if a.cmd == "shot":
        dbg.screenshot(a.out)
    elif a.cmd == "press":
        for b in a.buttons:
            dbg.press(b, a.hold)
            time.sleep(a.gap)
    elif a.cmd == "read":
        with open(a.out, "wb") as f:
            f.write(dbg.read(int(a.addr, 0), int(a.size, 0)))
    else:
        msg = json.loads(a.json)
        print(json.dumps(dbg.call(msg.pop("event"), **msg), ensure_ascii=False)[:4000])


if __name__ == "__main__":
    sys.exit(main())
