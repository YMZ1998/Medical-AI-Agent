#!/usr/bin/env python3
"""
Watch a folder for new/updated files and publish the latest one to a web service.

Features
- Event-driven via watchdog (fast, low CPU).
- Optional polling fallback (--poll-interval).
- Debounce to ensure files are fully written before upload.
- Pattern filter (e.g., *.tif).
- Retries with exponential backoff.
- Only publishes the LATEST file present at trigger time.
"""

from __future__ import annotations
import argparse
import fnmatch
import logging
import os
import queue
import sys
import threading
import time
from dataclasses import dataclass
from typing import Optional, List, Tuple

import requests

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except Exception:
    WATCHDOG_AVAILABLE = False

# ----------------------------- helpers ---------------------------------

def is_match(name: str, patterns: List[str]) -> bool:
    if not patterns:
        return True
    return any(fnmatch.fnmatch(name, p) for p in patterns)

def file_is_stable(path: str, stable_for: float, check_every: float = 0.5) -> bool:
    """
    Returns True when a file hasn't changed size/mtime for `stable_for` seconds.
    """
    end_time = None
    last: Optional[Tuple[int, float]] = None
    while True:
        try:
            st = os.stat(path)
        except FileNotFoundError:
            return False
        current = (st.st_size, st.st_mtime)
        if last == current:
            if end_time is None:
                end_time = time.time() + stable_for
            if time.time() >= end_time:
                return True
        else:
            last = current
            end_time = None
        time.sleep(check_every)

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
                mtime = entry.stat().st_mtime
            except FileNotFoundError:
                continue
            if mtime > latest_mtime:
                latest_mtime = mtime
                latest_path = entry.path
    except FileNotFoundError:
        return None
    return latest_path

def post_file(endpoint: str, path: str, field_name: str, token: Optional[str], extra: List[str], timeout: float) -> requests.Response:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = {}
    # extra key=value pairs
    for kv in extra:
        if "=" in kv:
            k, v = kv.split("=", 1)
            data[k] = v
    with open(path, "rb") as f:
        files = {field_name: (os.path.basename(path), f)}
        resp = requests.post(endpoint, headers=headers, data=data, files=files, timeout=timeout)
    return resp

def retry_post(endpoint: str, path: str, field_name: str, token: Optional[str], extra: List[str], timeout: float, attempts: int, base_delay: float) -> bool:
    delay = base_delay
    for i in range(1, attempts + 1):
        try:
            resp = post_file(endpoint, path, field_name, token, extra, timeout)
            if 200 <= resp.status_code < 300:
                logging.info("Uploaded %s -> %s (status %s)", path, endpoint, resp.status_code)
                return True
            else:
                logging.warning("Upload failed (attempt %d/%d): HTTP %s, body=%s", i, attempts, resp.status_code, resp.text[:500])
        except Exception as e:
            logging.warning("Upload error (attempt %d/%d): %s", i, attempts, e)
        if i < attempts:
            time.sleep(delay)
            delay *= 2
    return False

# ----------------------------- worker ----------------------------------

@dataclass
class Config:
    directory: str
    patterns: List[str]
    debounce: float
    endpoint: str
    field_name: str
    token: Optional[str]
    timeout: float
    attempts: int
    backoff: float
    extra: List[str]

class PublishWorker:
    """
    Receives "trigger" events and, after a short coalescing window, publishes the latest file.
    """
    def __init__(self, cfg: Config, coalesce_window: float = 0.75):
        self.cfg = cfg
        self.coalesce_window = coalesce_window
        self._q: "queue.Queue[float]" = queue.Queue()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        # Nudge queue so the thread wakes up
        try:
            self._q.put_nowait(time.time())
        except queue.Full:
            pass
        self._thread.join(timeout=5)

    def trigger(self):
        try:
            self._q.put_nowait(time.time())
        except queue.Full:
            pass

    def _run(self):
        last_trigger_time: Optional[float] = None
        while not self._stop.is_set():
            try:
                t = self._q.get(timeout=0.2)
                last_trigger_time = t
                # Coalesce multiple triggers close in time
                while True:
                    try:
                        t2 = self._q.get(timeout=self.coalesce_window)
                        last_trigger_time = t2
                    except queue.Empty:
                        break
                # Act on the latest file
                path = latest_file(self.cfg.directory, self.cfg.patterns)
                if not path:
                    logging.debug("No matching files found yet.")
                    continue
                # Wait until stable
                if not file_is_stable(path, stable_for=self.cfg.debounce):
                    logging.debug("File %s disappeared or unstable.", path)
                    continue
                # Upload
                ok = retry_post(
                    endpoint=self.cfg.endpoint,
                    path=path,
                    field_name=self.cfg.field_name,
                    token=self.cfg.token,
                    extra=self.cfg.extra,
                    timeout=self.cfg.timeout,
                    attempts=self.cfg.attempts,
                    base_delay=self.cfg.backoff,
                )
                if not ok:
                    logging.error("Giving up uploading %s after %d attempts.", path, self.cfg.attempts)
            except queue.Empty:
                pass

# ----------------------------- watchers --------------------------------

class Handler(FileSystemEventHandler):
    def __init__(self, worker: PublishWorker, patterns: List[str]):
        super().__init__()
        self.worker = worker
        self.patterns = patterns

    def on_any_event(self, event: FileSystemEvent):
        # Trigger only for files that match the pattern; directories are ignored.
        if event.is_directory:
            return
        name = os.path.basename(event.src_path)
        if name.startswith("."):
            return
        if not is_match(name, self.patterns):
            return
        logging.debug("FS event: %s -> %s", event.event_type, event.src_path)
        self.worker.trigger()

def start_watchdog(path: str, worker: PublishWorker, patterns: List[str]) -> Observer:
    observer = Observer()
    handler = Handler(worker, patterns)
    observer.schedule(handler, path, recursive=False)
    observer.start()
    logging.info("Watching %s with watchdog (event-driven).", path)
    return observer

def polling_loop(path: str, worker: PublishWorker, patterns: List[str], interval: float, stop_event: threading.Event):
    logging.info("Polling %s every %.2fs.", path, interval)
    last_seen: Optional[str] = None
    last_mtime = -1.0
    while not stop_event.is_set():
        p = latest_file(path, patterns)
        if p:
            try:
                mtime = os.stat(p).st_mtime
            except FileNotFoundError:
                mtime = -1
            if p != last_seen or mtime > last_mtime:
                last_seen, last_mtime = p, mtime
                worker.trigger()
        stop_event.wait(interval)

# ----------------------------- main ------------------------------------

def parse_args(argv: Optional[List[str]] = None):
    ap = argparse.ArgumentParser(description="Publish the latest file from a folder to a web service when new files appear.")
    ap.add_argument("--dir", default=r"D:\debug\test", help="Folder to monitor.")
    ap.add_argument("--endpoint", default="http://127.0.0.1:8080", help="Web service URL to POST the file to.")
    ap.add_argument("--field-name", default="file", help="Form field name for file upload (default: file).")
    ap.add_argument("--pattern", action="append", default=[], help="Glob pattern(s) to include (e.g., --pattern '*.tif'). Repeatable.")
    ap.add_argument("--debounce", type=float, default=1.5, help="Seconds a file must be unchanged before upload.")
    ap.add_argument("--timeout", type=float, default=30.0, help="HTTP request timeout (seconds).")
    ap.add_argument("--attempts", type=int, default=4, help="Max upload attempts.")
    ap.add_argument("--backoff", type=float, default=1.0, help="Initial backoff between retries (seconds).")
    ap.add_argument("--token-env", default="UPLOAD_TOKEN", help="Env var name holding a Bearer token (optional).")
    ap.add_argument("--extra", action="append", default=[], help="Extra form fields as key=value (repeatable).")
    ap.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    ap.add_argument("--poll-interval", type=float, default=0.0, help="If >0, enable polling fallback at this interval (seconds).")
    return ap.parse_args(argv)

def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(asctime)s %(levelname)s: %(message)s")
    directory = os.path.abspath(args.dir)
    if not os.path.isdir(directory):
        logging.error("Directory does not exist: %s", directory)
        sys.exit(2)
    token = os.environ.get(args.token_env) or None
    patterns = args.pattern or []  # empty => accept all files
    cfg = Config(
        directory=directory,
        patterns=patterns,
        debounce=args.debounce,
        endpoint=args.endpoint,
        field_name=args.field_name,
        token=token,
        timeout=args.timeout,
        attempts=args.attempts,
        backoff=args.backoff,
        extra=args.extra,
    )

    worker = PublishWorker(cfg)
    worker.start()

    # Event-driven if available
    observer = None
    stop_poll = threading.Event()
    poll_thread = None

    try:
        if WATCHDOG_AVAILABLE:
            observer = start_watchdog(directory, worker, patterns)
        else:
            logging.warning("watchdog not available; falling back to polling.")
        # Optional polling (either as fallback or alongside watchdog for safety)
        if args.poll_interval and args.poll_interval > 0:
            poll_thread = threading.Thread(
                target=polling_loop,
                args=(directory, worker, patterns, args.poll_interval, stop_poll),
                daemon=True,
            )
            poll_thread.start()

        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Stopping...")
    finally:
        worker.stop()
        if observer:
            observer.stop()
            observer.join(timeout=5)
        if poll_thread:
            stop_poll.set()
            poll_thread.join(timeout=5)

if __name__ == "__main__":
    main()
