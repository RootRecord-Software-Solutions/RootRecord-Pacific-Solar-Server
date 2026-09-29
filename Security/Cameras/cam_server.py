#!/usr/bin/env python3
"""a-eyes local camera server — true live MJPEG + password web UI.

Binds 127.0.0.1:8791 only. Public path is proxied by rootserver_poller at
https://rootserver.rootrecord.cloud/aeyes (tunnel → :8799 → here).

Routes:
  GET  /health
  GET  /current.jpg | /current_ch2.jpg | …   still snapshot (local)
  GET  /aeyes  /aeyes/                       login or live 4-channel grid
  POST /aeyes/login
  GET  /aeyes/logout
  GET  /aeyes/live/ch{1-4}.mjpeg             continuous live MJPEG (auth)
  GET  /aeyes/live/ch{1-4}.jpg               one-shot still (auth, fallback)

Password: AEYES_PUBLIC_PASSWORD in /home/rootrecord/master/master-key.env
"""
from __future__ import annotations

import hashlib
import hmac
import json
import subprocess
import sys
import threading
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from grab_frame import (  # noqa: E402
    DB_FRAMES,
    FramesBusy,
    crop_right_pct,
    crop_right_px,
    grab_jpeg,
    load_master_key,
    rtsp_url,
)

HOST = "127.0.0.1"
PORT = 8791
COOKIE_NAME = "aeyes_session"
COOKIE_MAX_AGE = 60 * 60 * 12

# Substream (stream=1) for live web — lighter on the DVR / LAN.
LIVE_STREAM = 1
LIVE_FPS = 8
LIVE_Q = 7  # mjpeg quality 2–31 (lower = better)

STILL_ROUTES = {
    "current.jpg": 1,
    "current_ch2.jpg": 2,
    "current_ch3.jpg": 3,
    "current_ch4.jpg": 4,
}

_last_jpeg: dict[int, bytes] = {}
_last_lock = threading.Lock()


def _password() -> str:
    return load_master_key("AEYES_PUBLIC_PASSWORD")


def _session_token(password: str) -> str:
    return hmac.new(
        b"aeyes-public-v1",
        password.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _expected_token() -> str:
    return _session_token(_password())


def _disk_latest(channel: int) -> bytes | None:
    try:
        files = sorted(DB_FRAMES.glob(f"ch{channel}-*.jpg"), key=lambda p: p.stat().st_mtime)
        if not files:
            return None
        data = files[-1].read_bytes()
        return data if len(data) > 500 else None
    except OSError:
        return None


def _crop_vf() -> str | None:
    pct = crop_right_pct()
    px = crop_right_px()
    if pct <= 0 and px <= 0:
        return None
    return f"crop=trunc((iw*(1-{pct})-{px})/2)*2:ih:0:0"


LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>a-eyes</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center;
         font-family: system-ui, sans-serif; background: #0b0f14; color: #e8eef5; }
  form { background: #141a22; padding: 2rem; border-radius: 12px; width: min(360px, 92vw);
         border: 1px solid #243041; }
  h1 { margin: 0 0 0.25rem; font-size: 1.25rem; }
  p { margin: 0 0 1.25rem; color: #8b9bb0; font-size: 0.9rem; }
  input { width: 100%; padding: 0.7rem 0.85rem; border-radius: 8px; border: 1px solid #2c3b50;
          background: #0b0f14; color: #e8eef5; font-size: 1rem; }
  button { margin-top: 0.9rem; width: 100%; padding: 0.7rem; border: 0; border-radius: 8px;
           background: #2f6fed; color: #fff; font-weight: 600; cursor: pointer; }
  button:hover { background: #3b7cff; }
  .err { color: #ff8b8b; font-size: 0.85rem; margin-top: 0.75rem; }
</style>
</head>
<body>
  <form method="post" action="/aeyes/login">
    <h1>a-eyes</h1>
    <p>Enter the public password to view live cameras.</p>
    <input type="password" name="password" placeholder="Password" autofocus required/>
    <button type="submit">View cameras</button>
    __ERR__
  </form>
</body>
</html>
"""

LIVE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>a-eyes live</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; background: #0b0f14; color: #e8eef5; font-family: system-ui, sans-serif; }
  header { display: flex; align-items: center; justify-content: space-between;
           padding: 0.75rem 1rem; border-bottom: 1px solid #1c2533; }
  header h1 { margin: 0; font-size: 1.05rem; font-weight: 600; }
  header a { color: #8b9bb0; text-decoration: none; font-size: 0.85rem; }
  header a:hover { color: #e8eef5; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; padding: 0.5rem; }
  @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
  .cell { background: #141a22; border: 1px solid #243041; border-radius: 10px; overflow: hidden; }
  .label { padding: 0.4rem 0.65rem; font-size: 0.8rem; color: #8b9bb0;
           border-bottom: 1px solid #1c2533; }
  .cell img { display: block; width: 100%; height: auto; background: #000; min-height: 160px;
              object-fit: contain; }
</style>
</head>
<body>
  <header>
    <h1>a-eyes — live</h1>
    <a href="/aeyes/logout">Log out</a>
  </header>
  <div class="grid">
    <div class="cell"><div class="label">Channel 1 · live</div>
      <img src="/aeyes/live/ch1.mjpeg" alt="ch1"/></div>
    <div class="cell"><div class="label">Channel 2 · live</div>
      <img src="/aeyes/live/ch2.mjpeg" alt="ch2"/></div>
    <div class="cell"><div class="label">Channel 3 · live</div>
      <img src="/aeyes/live/ch3.mjpeg" alt="ch3"/></div>
    <div class="cell"><div class="label">Channel 4 · live</div>
      <img src="/aeyes/live/ch4.mjpeg" alt="ch4"/></div>
  </div>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    server_version = "AEyesCamServer/3.0"
    # Long-lived MJPEG connections
    timeout = 300

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _json(self, code: int, body: dict) -> None:
        raw = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _html(self, code: int, body: str, *, extra_headers: list[tuple[str, str]] | None = None) -> None:
        raw = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        if extra_headers:
            for k, v in extra_headers:
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(raw)

    def _jpeg(self, data: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _cookies(self) -> SimpleCookie:
        c = SimpleCookie()
        raw = self.headers.get("Cookie")
        if raw:
            c.load(raw)
        return c

    def _authed(self) -> bool:
        try:
            expected = _expected_token()
        except (FileNotFoundError, KeyError):
            return False
        morsel = self._cookies().get(COOKIE_NAME)
        if not morsel:
            return False
        return hmac.compare_digest(morsel.value, expected)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path in ("/health", ""):
            self._json(200, {"ok": True, "service": "a-eyes-cam-server"})
            return

        name = path.lstrip("/")
        if name in STILL_ROUTES:
            self._still(STILL_ROUTES[name])
            return

        if path in ("/aeyes",):
            if self._authed():
                self._html(200, LIVE_HTML)
            else:
                self._html(200, LOGIN_HTML.replace("__ERR__", ""))
            return

        if path == "/aeyes/logout":
            self._html(
                302,
                "",
                extra_headers=[
                    ("Location", "/aeyes"),
                    ("Set-Cookie", f"{COOKIE_NAME}=; Path=/aeyes; Max-Age=0; HttpOnly; SameSite=Lax"),
                ],
            )
            return

        if path.startswith("/aeyes/live/ch") and path.endswith(".mjpeg"):
            if not self._authed():
                self._json(401, {"ok": False, "error": "unauthorized"})
                return
            try:
                ch = int(path.split("/ch")[-1].split(".")[0])
            except ValueError:
                self._json(404, {"ok": False, "error": "not_found"})
                return
            if ch not in (1, 2, 3, 4):
                self._json(404, {"ok": False, "error": "not_found"})
                return
            self._mjpeg_live(ch)
            return

        if path.startswith("/aeyes/live/ch") and path.endswith(".jpg"):
            if not self._authed():
                self._json(401, {"ok": False, "error": "unauthorized"})
                return
            try:
                ch = int(path.split("/ch")[-1].split(".")[0])
            except ValueError:
                self._json(404, {"ok": False, "error": "not_found"})
                return
            if ch not in (1, 2, 3, 4):
                self._json(404, {"ok": False, "error": "not_found"})
                return
            self._still(ch)
            return

        self._json(404, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path != "/aeyes/login":
            self._json(404, {"ok": False, "error": "not_found"})
            return

        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length > 0 else b""
        form = parse_qs(raw.decode("utf-8", errors="replace"))
        submitted = (form.get("password") or [""])[0]

        try:
            expected_pw = _password()
        except (FileNotFoundError, KeyError) as e:
            self._html(
                500,
                LOGIN_HTML.replace("__ERR__", f'<div class="err">Server misconfigured: {e}</div>'),
            )
            return

        if not hmac.compare_digest(submitted, expected_pw):
            self._html(401, LOGIN_HTML.replace("__ERR__", '<div class="err">Wrong password.</div>'))
            return

        token = _session_token(expected_pw)
        self._html(
            302,
            "",
            extra_headers=[
                ("Location", "/aeyes"),
                (
                    "Set-Cookie",
                    f"{COOKIE_NAME}={token}; Path=/aeyes; Max-Age={COOKIE_MAX_AGE}; HttpOnly; SameSite=Lax",
                ),
            ],
        )

    def _mjpeg_live(self, channel: int) -> None:
        """Pipe continuous MJPEG from RTSP to the browser (true live)."""
        url = rtsp_url(channel, LIVE_STREAM)
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-rtsp_transport", "tcp",
            "-i", url,
            "-an",
            "-r", str(LIVE_FPS),
        ]
        vf = _crop_vf()
        if vf:
            cmd += ["-vf", vf]
        # mpjpeg = multipart JPEG stream browsers understand in <img src>
        cmd += ["-f", "mpjpeg", "-q:v", str(LIVE_Q), "pipe:1"]

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
            )
        except OSError as e:
            self._json(503, {"ok": False, "error": f"ffmpeg start failed: {e}"})
            return

        try:
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=ffmpeg")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()

            assert proc.stdout is not None
            while True:
                chunk = proc.stdout.read(4096)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass  # client closed tab / navigated away
        finally:
            try:
                proc.kill()
            except OSError:
                pass
            try:
                proc.wait(timeout=2)
            except Exception:
                pass

    def _still(self, channel: int) -> None:
        data: bytes | None = None
        try:
            path = grab_jpeg(channel=channel)
            data = path.read_bytes()
            if data and len(data) > 500:
                with _last_lock:
                    _last_jpeg[channel] = data
        except FramesBusy:
            data = None
        except Exception:
            data = None

        if not data:
            with _last_lock:
                data = _last_jpeg.get(channel)
        if not data:
            data = _disk_latest(channel)
            if data:
                with _last_lock:
                    _last_jpeg[channel] = data

        if data:
            self._jpeg(data)
            return
        self._json(503, {"ok": False, "error": f"Ch{channel} unavailable"})


def main() -> None:
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    # Allow reuse after quick restart
    httpd.allow_reuse_address = True
    print(f"a-eyes cam server listen={HOST}:{PORT} (live MJPEG)", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
