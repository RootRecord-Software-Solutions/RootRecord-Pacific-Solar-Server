# ==============================================================================
# FILE: Security/Cameras/cam_server.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
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
from __future__ import annotations  # info: from __future__ import annotations

import hashlib  # info: import hashlib
import hmac  # info: import hmac
import json  # info: import json
import subprocess  # info: import subprocess
import sys  # info: import sys
import threading  # info: import threading
from http.cookies import SimpleCookie  # info: from http . cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer  # info: from http . server import BaseHTTPRequestHandler , ThreadingHTTPServer
from pathlib import Path  # info: from pathlib import Path
from urllib.parse import parse_qs, urlparse  # info: from urllib . parse import parse_qs , urlparse

ROOT = Path(__file__).resolve().parent  # info: set ROOT
sys.path.insert(0, str(ROOT))  # info: sys . path . insert ( 0 ,
from grab_frame import (  # noqa: E402
    DB_FRAMES,  # info: DB_FRAMES ,
    FramesBusy,  # info: FramesBusy ,
    crop_right_pct,  # info: crop_right_pct ,
    crop_right_px,  # info: crop_right_px ,
    grab_jpeg,  # info: grab_jpeg ,
    load_master_key,  # info: load_master_key ,
    rtsp_url,  # info: rtsp_url ,
)  # info: )

HOST = "127.0.0.1"  # info: set HOST
PORT = 8791  # info: set PORT
COOKIE_NAME = "aeyes_session"  # info: set COOKIE_NAME
COOKIE_MAX_AGE = 60 * 60 * 12  # info: set COOKIE_MAX_AGE

# Substream (stream=1) for live web — lighter on the DVR / LAN.
LIVE_STREAM = 1  # info: set LIVE_STREAM
LIVE_FPS = 8  # info: set LIVE_FPS
LIVE_Q = 7  # mjpeg quality 2–31 (lower = better)

# ====================================================
# SECTION: STILL_ROUTES
# What it does: Set STILL_ROUTES.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
STILL_ROUTES = {  # info: set STILL_ROUTES
    "current.jpg": 1,  # info: "current.jpg" : 1 ,
    "current_ch2.jpg": 2,  # info: "current_ch2.jpg" : 2 ,
    "current_ch3.jpg": 3,  # info: "current_ch3.jpg" : 3 ,
    "current_ch4.jpg": 4,  # info: "current_ch4.jpg" : 4 ,
}  # info: }

_last_jpeg: dict[int, bytes] = {}  # info: set _last_jpeg
_last_lock = threading.Lock()  # info: set _last_lock


# ====================================================
# SECTION: function _password
# What it does:  password.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _password() -> str:  # info: def _password
    return load_master_key("AEYES_PUBLIC_PASSWORD")  # info: return load_master_key ( "AEYES_PUBLIC_PASSWORD" )


# ====================================================
# SECTION: function _session_token
# What it does:  session token.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _session_token(password: str) -> str:  # info: def _session_token
    return hmac.new(  # info: return hmac . new (
        b"aeyes-public-v1",  # info: b"aeyes-public-v1" ,
        password.encode("utf-8"),  # info: password . encode ( "utf-8" ) ,
        hashlib.sha256,  # info: hashlib . sha256 ,
    ).hexdigest()  # info: ) . hexdigest ( )


# ====================================================
# SECTION: function _expected_token
# What it does:  expected token.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _expected_token() -> str:  # info: def _expected_token
    return _session_token(_password())  # info: return _session_token ( _password ( ) )


# ====================================================
# SECTION: function _disk_latest
# What it does:  disk latest.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _disk_latest(channel: int) -> bytes | None:  # info: def _disk_latest
    try:  # info: try :
        files = sorted(DB_FRAMES.glob(f"ch{channel}-*.jpg"), key=lambda p: p.stat().st_mtime)  # info: set files
        if not files:  # info: if not files :
            return None  # info: return None
        data = files[-1].read_bytes()  # info: set data
        return data if len(data) > 500 else None  # info: return data if len ( data ) >
    except OSError:  # info: except OSError :
        return None  # info: return None


# ====================================================
# SECTION: function _crop_vf
# What it does:  crop vf.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _crop_vf() -> str | None:  # info: def _crop_vf
    pct = crop_right_pct()  # info: set pct
    px = crop_right_px()  # info: set px
    if pct <= 0 and px <= 0:  # info: if pct <= 0 and px <= 0
        return None  # info: return None
    return f"crop=trunc((iw*(1-{pct})-{px})/2)*2:ih:0:0"  # info: return f" crop=trunc((iw*(1- { pct } )- {


# ====================================================
# SECTION: LOGIN_HTML
# What it does: Set LOGIN_HTML.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
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

# ====================================================
# SECTION: LIVE_HTML
# What it does: Set LIVE_HTML.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
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


# ====================================================
# SECTION: class Handler
# What it does: Handler.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class Handler(BaseHTTPRequestHandler):  # info: class Handler
    server_version = "AEyesCamServer/3.0"  # info: set server_version
    # Long-lived MJPEG connections
    timeout = 300  # info: set timeout

    def log_message(self, fmt: str, *args) -> None:  # info: def log_message
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))  # info: sys . stderr . write ( "%s - %s\n" %

    def _json(self, code: int, body: dict) -> None:  # info: def _json
        raw = json.dumps(body).encode("utf-8")  # info: set raw
        self.send_response(code)  # info: self . send_response ( code )
        self.send_header("Content-Type", "application/json")  # info: self . send_header ( "Content-Type" , "application/json" )
        self.send_header("Content-Length", str(len(raw)))  # info: self . send_header ( "Content-Length" , str (
        self.send_header("Cache-Control", "no-store")  # info: self . send_header ( "Cache-Control" , "no-store" )
        self.end_headers()  # info: self . end_headers ( )
        self.wfile.write(raw)  # info: self . wfile . write ( raw )

    def _html(self, code: int, body: str, *, extra_headers: list[tuple[str, str]] | None = None) -> None:  # info: def _html
        raw = body.encode("utf-8")  # info: set raw
        self.send_response(code)  # info: self . send_response ( code )
        self.send_header("Content-Type", "text/html; charset=utf-8")  # info: self . send_header ( "Content-Type" , "text/html; charset=utf-8" )
        self.send_header("Content-Length", str(len(raw)))  # info: self . send_header ( "Content-Length" , str (
        self.send_header("Cache-Control", "no-store")  # info: self . send_header ( "Cache-Control" , "no-store" )
        if extra_headers:  # info: if extra_headers :
            for k, v in extra_headers:  # info: for k , v in extra_headers :
                self.send_header(k, v)  # info: self . send_header ( k , v )
        self.end_headers()  # info: self . end_headers ( )
        self.wfile.write(raw)  # info: self . wfile . write ( raw )

    def _jpeg(self, data: bytes) -> None:  # info: def _jpeg
        self.send_response(200)  # info: self . send_response ( 200 )
        self.send_header("Content-Type", "image/jpeg")  # info: self . send_header ( "Content-Type" , "image/jpeg" )
        self.send_header("Content-Length", str(len(data)))  # info: self . send_header ( "Content-Length" , str (
        self.send_header("Cache-Control", "no-store")  # info: self . send_header ( "Cache-Control" , "no-store" )
        self.end_headers()  # info: self . end_headers ( )
        self.wfile.write(data)  # info: self . wfile . write ( data )

    def _cookies(self) -> SimpleCookie:  # info: def _cookies
        c = SimpleCookie()  # info: set c
        raw = self.headers.get("Cookie")  # info: set raw
        if raw:  # info: if raw :
            c.load(raw)  # info: c . load ( raw )
        return c  # info: return c

    def _authed(self) -> bool:  # info: def _authed
        try:  # info: try :
            expected = _expected_token()  # info: set expected
        except (FileNotFoundError, KeyError):  # info: except ( FileNotFoundError , KeyError ) :
            return False  # info: return False
        morsel = self._cookies().get(COOKIE_NAME)  # info: set morsel
        if not morsel:  # info: if not morsel :
            return False  # info: return False
        return hmac.compare_digest(morsel.value, expected)  # info: return hmac . compare_digest ( morsel . value

    def do_GET(self) -> None:  # info: def do_GET
        parsed = urlparse(self.path)  # info: set parsed
        path = parsed.path.rstrip("/") or "/"  # info: set path

        if path in ("/health", ""):  # info: if path in ( "/health" , "" )
            self._json(200, {"ok": True, "service": "a-eyes-cam-server"})  # info: self . _json ( 200 , { "ok"
            return  # info: return

        name = path.lstrip("/")  # info: set name
        if name in STILL_ROUTES:  # info: if name in STILL_ROUTES :
            self._still(STILL_ROUTES[name])  # info: self . _still ( STILL_ROUTES [ name ]
            return  # info: return

        if path in ("/aeyes",):  # info: if path in ( "/aeyes" , ) :
            if self._authed():  # info: if self . _authed ( ) :
                self._html(200, LIVE_HTML)  # info: self . _html ( 200 , LIVE_HTML )
            else:  # info: else :
                self._html(200, LOGIN_HTML.replace("__ERR__", ""))  # info: self . _html ( 200 , LOGIN_HTML .
            return  # info: return

        if path == "/aeyes/logout":  # info: if path == "/aeyes/logout" :
            self._html(  # info: self . _html (
                302,  # info: 302 ,
                "",  # info: "" ,
                extra_headers=[  # info: set extra_headers
                    ("Location", "/aeyes"),  # info: call (
                    ("Set-Cookie", f"{COOKIE_NAME}=; Path=/aeyes; Max-Age=0; HttpOnly; SameSite=Lax"),  # info: call (
                ],  # info: ] ,
            )  # info: )
            return  # info: return

        if path.startswith("/aeyes/live/ch") and path.endswith(".mjpeg"):  # info: if path . startswith ( "/aeyes/live/ch" ) and
            if not self._authed():  # info: if not self . _authed ( ) :
                self._json(401, {"ok": False, "error": "unauthorized"})  # info: self . _json ( 401 , { "ok"
                return  # info: return
            try:  # info: try :
                ch = int(path.split("/ch")[-1].split(".")[0])  # info: set ch
            except ValueError:  # info: except ValueError :
                self._json(404, {"ok": False, "error": "not_found"})  # info: self . _json ( 404 , { "ok"
                return  # info: return
            if ch not in (1, 2, 3, 4):  # info: if ch not in ( 1 , 2
                self._json(404, {"ok": False, "error": "not_found"})  # info: self . _json ( 404 , { "ok"
                return  # info: return
            self._mjpeg_live(ch)  # info: self . _mjpeg_live ( ch )
            return  # info: return

        if path.startswith("/aeyes/live/ch") and path.endswith(".jpg"):  # info: if path . startswith ( "/aeyes/live/ch" ) and
            if not self._authed():  # info: if not self . _authed ( ) :
                self._json(401, {"ok": False, "error": "unauthorized"})  # info: self . _json ( 401 , { "ok"
                return  # info: return
            try:  # info: try :
                ch = int(path.split("/ch")[-1].split(".")[0])  # info: set ch
            except ValueError:  # info: except ValueError :
                self._json(404, {"ok": False, "error": "not_found"})  # info: self . _json ( 404 , { "ok"
                return  # info: return
            if ch not in (1, 2, 3, 4):  # info: if ch not in ( 1 , 2
                self._json(404, {"ok": False, "error": "not_found"})  # info: self . _json ( 404 , { "ok"
                return  # info: return
            self._still(ch)  # info: self . _still ( ch )
            return  # info: return

        self._json(404, {"ok": False, "error": "not_found"})  # info: self . _json ( 404 , { "ok"

    def do_POST(self) -> None:  # info: def do_POST
        parsed = urlparse(self.path)  # info: set parsed
        path = parsed.path.rstrip("/") or "/"  # info: set path
        if path != "/aeyes/login":  # info: if path != "/aeyes/login" :
            self._json(404, {"ok": False, "error": "not_found"})  # info: self . _json ( 404 , { "ok"
            return  # info: return

        length = int(self.headers.get("Content-Length") or 0)  # info: set length
        raw = self.rfile.read(length) if length > 0 else b""  # info: set raw
        form = parse_qs(raw.decode("utf-8", errors="replace"))  # info: set form
        submitted = (form.get("password") or [""])[0]  # info: set submitted

        try:  # info: try :
            expected_pw = _password()  # info: set expected_pw
        except (FileNotFoundError, KeyError) as e:  # info: except ( FileNotFoundError , KeyError ) as e
            self._html(  # info: self . _html (
                500,  # info: 500 ,
                LOGIN_HTML.replace("__ERR__", f'<div class="err">Server misconfigured: {e}</div>'),  # info: LOGIN_HTML . replace ( "__ERR__" , f' <div class="err">Server misconfigured:
            )  # info: )
            return  # info: return

        if not hmac.compare_digest(submitted, expected_pw):  # info: if not hmac . compare_digest ( submitted ,
            self._html(401, LOGIN_HTML.replace("__ERR__", '<div class="err">Wrong password.</div>'))  # info: self . _html ( 401 , LOGIN_HTML .
            return  # info: return

        token = _session_token(expected_pw)  # info: set token
        self._html(  # info: self . _html (
            302,  # info: 302 ,
            "",  # info: "" ,
            extra_headers=[  # info: set extra_headers
                ("Location", "/aeyes"),  # info: call (
                (  # info: call (
                    "Set-Cookie",  # info: "Set-Cookie" ,
                    f"{COOKIE_NAME}={token}; Path=/aeyes; Max-Age={COOKIE_MAX_AGE}; HttpOnly; SameSite=Lax",  # info: f" { COOKIE_NAME } = { token }
                ),  # info: ) ,
            ],  # info: ] ,
        )  # info: )

    def _mjpeg_live(self, channel: int) -> None:  # info: def _mjpeg_live
        """Pipe continuous MJPEG from RTSP to the browser (true live)."""  # info: """Pipe continuous MJPEG from RTSP to the browser (true live)."""
        url = rtsp_url(channel, LIVE_STREAM)  # info: set url
        cmd = [  # info: set cmd
            "ffmpeg", "-hide_banner", "-loglevel", "error",  # info: "ffmpeg" , "-hide_banner" , "-loglevel" , "error" ,
            "-rtsp_transport", "tcp",  # info: "-rtsp_transport" , "tcp" ,
            "-i", url,  # info: "-i" , url ,
            "-an",  # info: "-an" ,
            "-r", str(LIVE_FPS),  # info: "-r" , str ( LIVE_FPS ) ,
        ]  # info: ]
        vf = _crop_vf()  # info: set vf
        if vf:  # info: if vf :
            cmd += ["-vf", vf]  # info: set cmd
        # mpjpeg = multipart JPEG stream browsers understand in <img src>
        cmd += ["-f", "mpjpeg", "-q:v", str(LIVE_Q), "pipe:1"]  # info: set cmd

        try:  # info: try :
            proc = subprocess.Popen(  # info: set proc
                cmd,  # info: cmd ,
                stdout=subprocess.PIPE,  # info: set stdout
                stderr=subprocess.PIPE,  # info: set stderr
                bufsize=0,  # info: set bufsize
            )  # info: )
        except OSError as e:  # info: except OSError as e :
            self._json(503, {"ok": False, "error": f"ffmpeg start failed: {e}"})  # info: self . _json ( 503 , { "ok"
            return  # info: return

        try:  # info: try :
            self.send_response(200)  # info: self . send_response ( 200 )
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=ffmpeg")  # info: self . send_header ( "Content-Type" , "multipart/x-mixed-replace; boundary=ffmpeg" )
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")  # info: self . send_header ( "Cache-Control" , "no-cache, no-store, must-revalidate" )
            self.send_header("Pragma", "no-cache")  # info: self . send_header ( "Pragma" , "no-cache" )
            self.send_header("Connection", "close")  # info: self . send_header ( "Connection" , "close" )
            self.end_headers()  # info: self . end_headers ( )

            assert proc.stdout is not None  # info: assert proc . stdout is not None
            while True:  # info: while True :
                chunk = proc.stdout.read(4096)  # info: set chunk
                if not chunk:  # info: if not chunk :
                    break  # info: break
                self.wfile.write(chunk)  # info: self . wfile . write ( chunk )
                self.wfile.flush()  # info: self . wfile . flush ( )
        except (BrokenPipeError, ConnectionResetError):  # info: except ( BrokenPipeError , ConnectionResetError ) :
            pass  # client closed tab / navigated away
        finally:  # info: finally :
            try:  # info: try :
                proc.kill()  # info: proc . kill ( )
            except OSError:  # info: except OSError :
                pass  # info: pass
            try:  # info: try :
                proc.wait(timeout=2)  # info: proc . wait ( timeout = 2 )
            except Exception:  # info: except Exception :
                pass  # info: pass

    def _still(self, channel: int) -> None:  # info: def _still
        data: bytes | None = None  # info: set data
        try:  # info: try :
            path = grab_jpeg(channel=channel)  # info: set path
            data = path.read_bytes()  # info: set data
            if data and len(data) > 500:  # info: if data and len ( data ) >
                with _last_lock:  # info: with _last_lock :
                    _last_jpeg[channel] = data  # info: _last_jpeg [ channel ] = data
        except FramesBusy:  # info: except FramesBusy :
            data = None  # info: set data
        except Exception:  # info: except Exception :
            data = None  # info: set data

        if not data:  # info: if not data :
            with _last_lock:  # info: with _last_lock :
                data = _last_jpeg.get(channel)  # info: set data
        if not data:  # info: if not data :
            data = _disk_latest(channel)  # info: set data
            if data:  # info: if data :
                with _last_lock:  # info: with _last_lock :
                    _last_jpeg[channel] = data  # info: _last_jpeg [ channel ] = data

        if data:  # info: if data :
            self._jpeg(data)  # info: self . _jpeg ( data )
            return  # info: return
        self._json(503, {"ok": False, "error": f"Ch{channel} unavailable"})  # info: self . _json ( 503 , { "ok"


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> None:  # info: def main
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)  # info: set httpd
    # Allow reuse after quick restart
    httpd.allow_reuse_address = True  # info: httpd . allow_reuse_address = True
    print(f"a-eyes cam server listen={HOST}:{PORT} (live MJPEG)", flush=True)  # info: call print
    httpd.serve_forever()  # info: httpd . serve_forever ( )


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    main()  # info: call main
