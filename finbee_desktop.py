import threading
import socket
import time
import sys
import webview
from waitress import serve
from app import app


# ---------------- FIND FREE PORT ----------------
def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


port = find_free_port()


# ---------------- RUN FLASK ----------------
def run_flask():
    serve(app, host='127.0.0.1', port=port)


flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()


# ---------------- WAIT FOR SERVER ----------------
for _ in range(40):
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=1):
            break
    except OSError:
        time.sleep(0.25)
else:
    raise RuntimeError("Flask server did not start")


# ---------------- CREATE WINDOW ----------------
window = webview.create_window(
    title="FinBee",
    url=f"http://127.0.0.1:{port}",
    width=1200,
    height=800,
    min_size=(900, 600),
    confirm_close=True
)


# ---------------- START WEBVIEW ----------------
if sys.platform == "win32":
    webview.start(gui="edgechromium")
else:
    webview.start()
