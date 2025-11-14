#!/usr/bin/env python3
"""
Serve the latest image from a folder via web server with automatic refresh.

Run example:
  python3 serve_latest_image.py --dir /data/outgoing --pattern "*.tif" --host 0.0.0.0 --port 8080
"""

from __future__ import annotations
import argparse
import fnmatch
import io
import logging
import mimetypes
import os
import sys
import threading
import time
from dataclasses import dataclass
from typing import Optional, List, Tuple

# Pillow for TIFF->PNG conversion
try:
    from PIL import Image
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# Watchdog for event-driven file watching
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except Exception:
    WATCHDOG_AVAILABLE = False

from flask import Flask, abort, make_response, render_template_string, send_file, request

app = Flask(__name__)

WEB_FRIENDLY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

# ----------------------------- utilities ---------------------------------

def is_match(name: str, patterns: List[str]) -> bool:
    if not patterns:
        return True
    return any(fnmatch.fnmatch(name, p) for p in patterns)

def latest_file(root: str, patterns: List[str]) -> Optional[str]:
    latest_path = None
    latest_mtime = -1.0
    try:
        for entry in os.scandir(root):
            if not entry.is_file():
                continue
            if entry.name.startswith("."):
                continue
            if not is_match(entry.name, patterns):
                continue
            try:
                st = entry.stat()
            except FileNotFoundError:
                continue
            if st.st_mtime > latest_mtime:
                latest_mtime = st.st_mtime
                latest_path = entry.path
    except FileNotFoundError:
        return None
    return latest_path

def file_is_stable(path: str, stable_for: float, check_every: float = 0.4) -> bool:
    """Return True if size/mtime unchanged for stable_for seconds."""
    end_time = None
    last: Optional[Tuple[int, float]] = None
    while True:
        try:
            st = os.stat(path)
        except FileNotFoundError:
            return False
        cur = (st.st_size, st.st_mtime)
        if cur == last:
            if end_time is None:
                end_time = time.time() + stable_for
            if time.time() >= end_time:
                return True
        else:
            last = cur
            end_time = None
        time.sleep(check_every)

def is_web_friendly(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in WEB_FRIENDLY_EXT

def format_time(ts: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))

# ----------------------------- shared state ---------------------------------

@dataclass
class Latest:
    path: Optional[str] = None
    mtime: float = 0.0
    size: int = 0

STATE_LOCK = threading.Lock()
LATEST = Latest()

# Simple cache for converted images
IMAGE_CACHE = {}

def get_cached_image(path: str) -> bytes:
    """Return PNG bytes of the image, using cache if available."""
    try:
        mtime = os.path.getmtime(path)
    except Exception:
        raise FileNotFoundError(f"Cannot access {path}")

    key = (path, mtime)
    if key in IMAGE_CACHE:
        return IMAGE_CACHE[key]

    img = Image.open(path)
    if img.mode not in ("RGB", "RGBA", "L"):
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    IMAGE_CACHE.clear()  # Keep only latest
    IMAGE_CACHE[key] = buf.getvalue()
    return IMAGE_CACHE[key]

def update_latest_from_dir(directory: str, patterns: List[str], debounce: float) -> None:
    p = latest_file(directory, patterns)
    if not p or not os.path.isfile(p):
        return
    if not file_is_stable(p, debounce):
        return
    try:
        st = os.stat(p)
    except FileNotFoundError:
        return
    with STATE_LOCK:
        LATEST.path = p
        LATEST.mtime = st.st_mtime
        LATEST.size = st.st_size
    logging.info("Latest -> %s (%.0f bytes, %s)", os.path.basename(p), st.st_size,
                 format_time(st.st_mtime))

# ----------------------------- Watcher ---------------------------------

class Handler(FileSystemEventHandler):
    def __init__(self, directory: str, patterns: List[str], debounce: float):
        super().__init__()
        self.directory = directory
        self.patterns = patterns
        self.debounce = debounce
        self._trigger_lock = threading.Lock()
        self._last_trigger = 0.0

    def on_any_event(self, event: FileSystemEvent):
        if event.is_directory:
            return
        name = os.path.basename(event.src_path)
        if name.startswith("."):
            return
        if not is_match(name, self.patterns):
            return
        now = time.time()
        with self._trigger_lock:
            if now - self._last_trigger < 0.3:
                return
            self._last_trigger = now
        threading.Thread(target=update_latest_from_dir,
                         args=(self.directory, self.patterns, self.debounce),
                         daemon=True).start()

class Watcher:
    def __init__(self, directory, patterns, debounce, poll_interval=0.0):
        self.directory = directory
        self.patterns = patterns
        self.debounce = debounce
        self.poll_interval = poll_interval
        self.stop_event = threading.Event()
        self.observer: Optional[Observer] = None
        self.poll_thread: Optional[threading.Thread] = None

    def start(self):
        if WATCHDOG_AVAILABLE:
            self.observer = Observer()
            self.observer.schedule(Handler(self.directory, self.patterns, self.debounce),
                                   self.directory, recursive=False)
            self.observer.start()
            logging.info("Watching %s (event-driven)", self.directory)
        if self.poll_interval > 0:
            self.poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
            self.poll_thread.start()
            logging.info("Polling %s every %.2fs", self.directory, self.poll_interval)

    def _poll_loop(self):
        last_seen = None
        last_mtime = -1.0
        while not self.stop_event.is_set():
            p = latest_file(self.directory, self.patterns)
            if p:
                try:
                    m = os.stat(p).st_mtime
                except FileNotFoundError:
                    m = -1
                if p != last_seen or m > last_mtime:
                    last_seen, last_mtime = p, m
                    update_latest_from_dir(self.directory, self.patterns, self.debounce)
            self.stop_event.wait(self.poll_interval)

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)
        if self.poll_thread:
            self.stop_event.set()
            self.poll_thread.join(timeout=5)

# ----------------------------- Web App ---------------------------------

INDEX_HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Latest Image</title>
<style>
body { font-family: system-ui, sans-serif; margin:1.2rem; }
img { max-width: 100%; height:auto; display:block; }
.meta { color:#555; font-size:0.95rem; margin-bottom:0.8rem; }
.bar { display:flex; gap:1rem; align-items:center; margin-bottom:0.5rem }
button { padding:0.35rem 0.7rem; }
code { background:#f2f2f2; padding:0.15rem 0.35rem; border-radius:6px; }
</style>
</head>
<body>
<h1>Latest Image</h1>
<div class="meta">
{% if latest %}
  <div>File: <code>{{ latest.name }}</code></div>
  <div>Size: {{ latest.size }} bytes</div>
  <div>Modified: {{ latest.mtime_str }}</div>
{% else %}
  <div>No image found yet.</div>
{% endif %}
</div>
<div class="bar">
  <button onclick="forceRefresh()">Refresh</button>
  <label>Auto-refresh
    <select id="interval" onchange="setIntervalFromSelect()">
      <option value="0">Off</option>
      <option value="1">1s</option>
      <option value="3" selected>3s</option>
      <option value="5">5s</option>
      <option value="10">10s</option>
    </select>
  </label>
  {% if latest %}
  <a href="/download">Download original</a>
  {% endif %}
</div>

{% if latest %}
<img id="preview" src="/image?v={{ latest.version }}" alt="Latest image preview">
{% endif %}

<script>
let timer = null;
function refreshImage() {
  const img = document.getElementById('preview');
  if (!img) return;
  const u = new URL(img.src, window.location);
  u.searchParams.set('v', Date.now().toString());
  img.src = u.toString();
}
function forceRefresh() { refreshImage(); }
function setIntervalFromSelect() {
  const sel = document.getElementById('interval');
  const s = parseInt(sel.value, 10);
  if (timer) { clearInterval(timer); timer = null; }
  if (s > 0) { timer = setInterval(refreshImage, s*1000); }
}
setIntervalFromSelect();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    with STATE_LOCK:
        if not LATEST.path:
            latest = None
        else:
            latest = {
                "name": os.path.basename(LATEST.path),
                "size": LATEST.size,
                "mtime_str": format_time(LATEST.mtime),
                "version": int(LATEST.mtime),
            }
    return render_template_string(INDEX_HTML, latest=latest)

@app.route("/image")
def image():
    with STATE_LOCK:
        p = LATEST.path
        mtime = LATEST.mtime
    if not p or not os.path.isfile(p):
        abort(404, "No image available")

    if is_web_friendly(p):
        guessed = mimetypes.guess_type(p)[0] or "application/octet-stream"
        resp = make_response(send_file(p, mimetype=guessed, as_attachment=False, conditional=True))
    else:
        if not PIL_AVAILABLE:
            resp = send_file(p, as_attachment=False)
        else:
            try:
                data = get_cached_image(p)
                resp = make_response(data)
                resp.headers["Content-Type"] = "image/png"
            except Exception as e:
                logging.warning("Conversion failed: %s", e)
                resp = send_file(p, as_attachment=False)

    # Disable caching
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    resp.headers["ETag"] = f"W/{int(mtime)}"
    return resp

@app.route("/download")
def download():
    with STATE_LOCK:
        p = LATEST.path
    if not p or not os.path.isfile(p):
        abort(404, "No file available")
    return send_file(p, as_attachment=True)

# ----------------------------- CLI / main -------------------------------

def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="Serve latest image from folder via web server")
    ap.add_argument("--dir", default=r"D:\debug\test", help="Folder to monitor.")
    ap.add_argument("--pattern", action="append", default=[], help="Glob pattern(s), e.g. --pattern '*.tif'")
    ap.add_argument("--debounce", type=float, default=1.5, help="Seconds file must remain unchanged before use")
    ap.add_argument("--poll-interval", type=float, default=0.0, help="Enable polling fallback at this interval (seconds)")
    ap.add_argument("--host", default="127.0.0.1", help="Web server host")
    ap.add_argument("--port", type=int, default=8080, help="Web server port")
    ap.add_argument("--log-level", default="INFO", choices=["DEBUG","INFO","WARNING","ERROR"], help="Logging level")
    return ap.parse_args(argv)

def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(asctime)s %(levelname)s: %(message)s")

    directory = os.path.abspath(args.dir)
    os.makedirs(directory, exist_ok=True)
    if not os.path.isdir(directory):
        logging.error("Directory does not exist: %s", directory)
        sys.exit(2)
    patterns = args.pattern or []

    # Init latest
    update_latest_from_dir(directory, patterns, args.debounce)

    watcher = Watcher(directory, patterns, args.debounce, args.poll_interval)
    watcher.start()
    try:
        logging.info("Serving on http://%s:%d", args.host, args.port)
        app.run(host=args.host, port=args.port, threaded=True)
    finally:
        watcher.stop()

if __name__ == "__main__":
    main()
