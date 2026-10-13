"""PhotoSorter Desktop Shell Entry Point (BUILD_PLAN Phase 5).

Starts FastAPI backend on a random free port in a background thread,
opens a native pywebview desktop window pointing to the local server,
exposes native file and folder pickers via JS API,
and cleanly shuts down the server on window close.
"""

from __future__ import annotations
import sys
import time
import socket
import threading
import argparse
from pathlib import Path
import uvicorn
import webview

# Ensure repo root is on sys.path
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    REPO_ROOT = Path(sys._MEIPASS)
else:
    REPO_ROOT = Path(__file__).resolve().parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.api.app import create_app


def find_free_port() -> int:
    """Finds a random free TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class WebviewApi:
    """JS API exposed to React UI as window.pywebview.api."""

    def __init__(self, window: webview.Window | None = None):
        self._window = window

    def set_window(self, window: webview.Window) -> None:
        self._window = window

    def select_folder(self, title: str = "Select Folder") -> str:
        """Opens native OS folder picker dialog and returns selected path."""
        if not self._window:
            return ""
        result = self._window.create_file_dialog(
            webview.FOLDER_DIALOG,
            allow_multiple=False,
        )
        if result and len(result) > 0:
            return str(result[0])
        return ""

    def select_file(self, title: str = "Select File or Zip Archive") -> str:
        """Opens native OS file picker dialog and returns selected file path."""
        if not self._window:
            return ""
        file_types = (
            "Supported Files (*.zip;*.tar;*.jpg;*.jpeg;*.png;*.heic;*.heif;*.tif;*.tiff)",
            "Zip Archives (*.zip;*.tar)",
            "All Files (*.*)",
        )
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=file_types,
        )
        if result and len(result) > 0:
            return str(result[0])
        return ""


class ServerThread(threading.Thread):
    """Background thread running Uvicorn server."""

    def __init__(self, app, host: str, port: int):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            log_level="warning",
            access_log=False,
        )
        self.server = uvicorn.Server(config=config)

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True


def wait_for_server(host: str, port: int, timeout: float = 10.0) -> bool:
    """Waits until the HTTP server is accepting connections."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(0.05)
    return False


def main():
    parser = argparse.ArgumentParser(description="PhotoSorter Desktop Shell")
    parser.add_argument("--port", type=int, default=0, help="Port to run on (0 for random free port)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--no-gui", action="store_true", help="Run server only without opening GUI window")
    parser.add_argument("--work-dir", type=str, default=None, help="Custom working directory")
    parser.add_argument("--output-dir", type=str, default=None, help="Custom export output directory")
    args = parser.parse_args()

    port = args.port if args.port > 0 else find_free_port()
    host = args.host

    work_path = Path(args.work_dir) if args.work_dir else None
    out_path = Path(args.output_dir) if args.output_dir else None

    app = create_app(work_dir=work_path, output_dir=out_path)

    server_thread = ServerThread(app=app, host=host, port=port)
    server_thread.start()

    if not wait_for_server(host, port, timeout=10.0):
        print(f"[ERROR] Failed to start local server on {host}:{port}")
        server_thread.stop()
        sys.exit(1)

    url = f"http://{host}:{port}"

    if args.no_gui:
        print(f"PhotoSorter server running at {url} (Ctrl+C to stop)")
        try:
            while server_thread.is_alive():
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        finally:
            server_thread.stop()
        return

    # Start native pywebview GUI
    api = WebviewApi()
    window = webview.create_window(
        title="PhotoSorter",
        url=url,
        js_api=api,
        width=1320,
        height=880,
        min_size=(960, 640),
        background_color="#0a0a0a",
    )
    api.set_window(window)

    try:
        webview.start(debug=False)
    finally:
        # Clean shutdown when window is closed
        server_thread.stop()
        server_thread.join(timeout=3.0)
        sys.exit(0)


if __name__ == "__main__":
    main()
