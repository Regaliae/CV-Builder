"""Serve the built CV Builder (this folder) on http://localhost:8000.

Run it with:  python serve.py      (or double-click CV-Builder.bat)
Stop it with: Ctrl+C               (or just close the window)

Why not plain `python -m http.server`? On Windows, Ctrl+C often doesn't
stop it: the browser keeps connections open, and the server only notices
the key press once another request arrives. Here the server runs in
background threads and the main thread just waits, so Ctrl+C is handled
straight away and the port is released at once.

Only this computer can reach the app (it listens on localhost only).
The port stays 8000 on purpose: the browser keeps your resumes per
address, so a different port would look like an empty CV Builder.
"""

import functools
import http.server
import os
import signal
import socket
import sys
import threading
import time
import webbrowser

PORT = int(os.environ.get("CV_BUILDER_PORT", "8000"))
URL = f"http://localhost:{PORT}"
ROOT = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    # Always fetch a fresh index.html after an update; the hashed files in assets/ can be cached forever.
    def end_headers(self):
        if not self.path.startswith("/assets/"):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, fmt, *args):
        pass  # keep the window quiet


class Server(http.server.ThreadingHTTPServer):
    daemon_threads = True
    # Lets a restart reuse the port at once on Linux/macOS. Left off on Windows,where it would let two copies share the port (and Windows does not block a restart there anyway).
    allow_reuse_address = os.name != "nt"


class Server6(Server):
    address_family = socket.AF_INET6


def start_servers():
    handler = functools.partial(Handler, directory=ROOT)
    servers = [Server(("127.0.0.1", PORT), handler)]
    try:  # browsers may try ::1 for "localhost" first
        servers.append(Server6(("::1", PORT), handler))
    except OSError:
        pass
    for s in servers:
        threading.Thread(target=s.serve_forever, kwargs={"poll_interval": 0.2}, daemon=True).start()
    return servers


def main():
    try:
        servers = start_servers()
    except OSError:
        print(f"Port {PORT} is already in use - CV Builder is probably already running")
        print("in another window. Opening it in the browser instead.")
        webbrowser.open(URL)
        time.sleep(2)
        return 0

    stop = threading.Event()

    def on_signal(*_):
        stop.set()

    signal.signal(signal.SIGINT, on_signal)
    if hasattr(signal, "SIGBREAK"):  # Ctrl+Break and closing the window on Windows
        signal.signal(signal.SIGBREAK, on_signal)
    signal.signal(signal.SIGTERM, on_signal)

    print(f"CV Builder is running at {URL}")
    print("Press Ctrl+C (or close this window) to stop it.")
    webbrowser.open(URL)

    while not stop.is_set():
        stop.wait(0.2)  # short waits so Ctrl+C is noticed immediately

    print("Stopping CV Builder...")
    for s in servers:
        s.shutdown()  # returns within one poll interval (0.2 s)
        s.server_close()  # releases the port right away
    print("Stopped.")
    return 0


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    # Leave right away instead of waiting on idle browser connections.
    os._exit(code)
