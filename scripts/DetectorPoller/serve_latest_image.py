#!/usr/bin/env python3
"""
Serve the latest image from a folder via a simple web server.

- Event-driven folder watch with watchdog (low CPU); optional polling fallback.
- Debounces writes to ensure files are fully written before use.
- Index page shows the current "latest" image and refreshes the <img> automatically.
- /image serves a browser-friendly stream (TIFF can be auto-converted to PNG if Pillow is 
available).
- /download serves the original file as-is.

Run:
  python3.11 serve_latest_image.py --dir /data/outgoing --pattern "*.tif" --host 0.0.0.0 --port 
8080

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

# --- Optional Pillow (for TIFF->PNG preview) ---
try:
    from PIL import Image  # type: ignore
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# --- Watchdog (file events) ---
try:
    from watchdog.observers import Observer  # type: ignore
    from watchdog.events import FileSystemEventHandler, FileSystemEvent  # type: ignore
    WATCHDOG_AVAILABLE = True
except Exception:
    WATCHDOG_AVAILABLE = False

# --- Web server (Flask) ---
from flask import Flask, Response, abort, jsonify, make_response, render_template_string, send_file

app = Flask(__name__)

# ----------------------------- utilities ---------------------------------

WEB_FRIENDLY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

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
            name = entry.name
            if name.startswith("."):
                continue
            if not is_match(name, patterns):
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
    """True if size/mtime unchanged for stable_for seconds."""
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

# ----------------------------- shared state ---------------------------------

@dataclass
class Latest:
    path: Optional[str] = None
    mtime: float = 0.0
    size: int = 0

STATE_LOCK = threading.Lock()
LATEST = Latest()

def update_latest_from_dir(directory: str, patterns: List[str], debounce: float) -> None:
    p = latest_file(directory, patterns)
    if not p:
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
time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)))

# ----------------------------- watcher threads -----------------------------

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
        # cheap coalescing: don't refresh more often than every 300 ms
        now = time.time()
        with self._trigger_lock:
            if now - self._last_trigger < 0.3:
                return
            self._last_trigger = now
        logging.debug("FS event: %s -> %s", event.event_type, event.src_path)
        threading.Thread(target=update_latest_from_dir, args=(self.directory, self.patterns, 
self.debounce), daemon=True).start()

def start_watchdog(directory: str, patterns: List[str], debounce: float) -> Optional[Observer]:
    if not WATCHDOG_AVAILABLE:
        logging.warning("watchdog not available; using polling.")
        return None
    observer = Observer()
    observer.schedule(Handler(directory, patterns, debounce), directory, recursive=False)
    observer.start()
    logging.info("Watching %s (event-driven).", directory)
    return observer

def start_polling(directory: str, patterns: List[str], debounce: float, interval: float, 
stop_event: threading.Event):
    logging.info("Polling %s every %.2fs.", directory, interval)
    last_seen = None
    last_mtime = -1.0
    while not stop_event.is_set():
        p = latest_file(directory, patterns)
        if p:
            try:
                m = os.stat(p).st_mtime
            except FileNotFoundError:
                m = -1
            if p != last_seen or m > last_mtime:
                last_seen, last_mtime = p, m
                update_latest_from_dir(directory, patterns, debounce)
        stop_event.wait(interval)

# ----------------------------- web app ---------------------------------

INDEX_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Latest Image</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: system-ui, sans-serif; margin: 1.2rem; }
    header { margin-bottom: 0.8rem; }
    img { max-width: 100%; height: auto; display: block; }
    .meta { color: #555; font-size: 0.95rem; margin-bottom: 0.8rem; }
    .bar { display:flex; gap:1rem; align-items:center; margin-bottom:0.5rem }
    button { padding: 0.35rem 0.7rem; }
    code { background:#f2f2f2; padding:0.15rem 0.35rem; border-radius: 6px; }
  </style>
</head>
<body>
  <header>
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
  </header>

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
      if (s > 0) {
        timer = setInterval(refreshImage, s * 1000);
      }
    }
    // start with default selected
    setIntervalFromSelect();
  </script>
</body>
</html>
"""

def format_time(ts: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))

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

@app.route("/status")
def status():
    with STATE_LOCK:
        if not LATEST.path:
            return jsonify({"ok": True, "latest": None})
        return jsonify({
            "ok": True,
            "latest": {
                "path": LATEST.path,
                "name": os.path.basename(LATEST.path),
                "size": LATEST.size,
                "mtime": LATEST.mtime
            }
        })

@app.route("/image")
def image():
    with STATE_LOCK:
        p = LATEST.path
        mtime = LATEST.mtime
    if not p or not os.path.isfile(p):
        abort(404, "No image available")
    # If browser friendly, stream as-is
    if is_web_friendly(p):
        guessed = mimetypes.guess_type(p)[0] or "application/octet-stream"
        resp = make_response(send_file(p, mimetype=guessed, as_attachment=False, 
conditional=True))
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["ETag"] = f"W/{int(mtime)}"
        return resp
    # Try Pillow conversion for non-web formats (e.g., TIFF)
    if not PIL_AVAILABLE:
        # Fall back to raw file download if Pillow not present
        return send_file(p, as_attachment=False)
    try:
        img = Image.open(p)
        # Convert to 8-bit if needed; browsers handle PNG well
        if img.mode not in ("RGB", "RGBA", "L"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        resp = make_response(send_file(buf, mimetype="image/png"))
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["ETag"] = f"W/{int(mtime)}"
        return resp
    except Exception as e:
        logging.warning("Conversion failed, serving original: %s", e)
        return send_file(p, as_attachment=False)

@app.route("/download")
def download():
    with STATE_LOCK:
        p = LATEST.path
    if not p or not os.path.isfile(p):
        abort(404, "No file available")
    return send_file(p, as_attachment=True)

# ----------------------------- CLI / main -------------------------------

def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="Serve the latest image from a folder via a basic web server.")
    ap.add_argument("--dir", default=r"D:\debug\test", help="Folder to monitor.")
    ap.add_argument("--pattern", action="append", default=[], help="Glob pattern(s), e.g. --pattern '*.tif' (repeatable).")
    ap.add_argument("--debounce", type=float, default=1.5, help="Seconds a file must remain unchanged before use.")
    ap.add_argument("--poll-interval", type=float, default=0.0, help="Enable polling fallback at this interval (seconds).")
    ap.add_argument("--host", default="127.0.0.1", help="Web server host (default 127.0.0.1).")
    ap.add_argument("--port", type=int, default=8080, help="Web server port (default 8080).")
    ap.add_argument("--log-level", default="INFO", choices=["DEBUG","INFO","WARNING","ERROR"], 
help="Logging level.")
    return ap.parse_args(argv)

def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(asctime)s %(levelname)s: %(message)s")

    directory = os.path.abspath(args.dir)
    os.makedirs(directory, exist_ok=True)
    if not os.path.isdir(directory):
        logging.error("Directory does not exist: %s", directory)
        sys.exit(2)

    patterns = args.pattern or []  # empty => accept all files

    # Initialize once on startup (in case files already exist)
    update_latest_from_dir(directory, patterns, args.debounce)

    # Start watcher
    observer = start_watchdog(directory, patterns, args.debounce)
    stop_poll = threading.Event()
    poll_thread = None
    if args.poll_interval and args.poll_interval > 0.0:
        poll_thread = threading.Thread(
            target=start_polling,
            args=(directory, patterns, args.debounce, args.poll_interval, stop_poll),
            daemon=True,
        )
        poll_thread.start()

    try:
        logging.info("Serving on http://%s:%d", args.host, args.port)
        app.run(host=args.host, port=args.port, threaded=True)
    finally:
        if observer:
            observer.stop()
            observer.join(timeout=5)
        if poll_thread:
            stop_poll.set()
            poll_thread.join(timeout=5)

if __name__ == "__main__":
    main()

