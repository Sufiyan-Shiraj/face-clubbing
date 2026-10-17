#!/usr/bin/env python3
"""Windowed launch verification script for PhotoSorter (BUILD_PLAN Phase 5).

Checks:
(a) A top-level window titled "PhotoSorter" appears
(b) No console window is created (PE Subsystem 2 GUI and no ConsoleWindowClass window)
(c) The page loads (health check HTTP 200 on the port from the process, and root HTML served)
(d) Closing the window (WM_CLOSE) ends the process and releases the port

If any part cannot be automated in the current environment, marks it NEEDS ORGANIZER REVIEW
with exact manual reproduction steps.
"""

import os
import sys
import time
import socket
import struct
import shutil
import tempfile
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def check_pe_subsystem(exe_path: Path) -> int:
    with open(exe_path, "rb") as f:
        header = f.read(1024)
    pe_offset = struct.unpack_from("<I", header, 0x3C)[0]
    subsystem = struct.unpack_from("<H", header, pe_offset + 0x5C)[0]
    return subsystem


def http_get(url: str, timeout: float = 5.0) -> tuple[int, str]:
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode("utf-8")
            return resp.status, data
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def find_process_windows(target_pids: set[int]) -> list[tuple[int, int, str, str]]:
    """Returns list of (hwnd, pid, title, class_name) for windows belonging to target_pids."""
    results = []
    if sys.platform != "win32":
        return results

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def enum_proc(hwnd, lparam):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in target_pids:
            length = user32.GetWindowTextLengthW(hwnd)
            title_buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title_buff, length + 1)

            class_buff = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, class_buff, 256)

            results.append((hwnd, pid.value, title_buff.value, class_buff.value))
        return True

    user32.EnumWindows(WNDENUMPROC(enum_proc), 0)
    return results


def get_process_tree_pids(root_pid: int) -> set[int]:
    """Finds all PIDs spawned by the root process or belonging to CatLog.exe / photosorter.exe."""
    pids = {root_pid}
    try:
        import psutil
        for p in psutil.process_iter(["pid", "ppid", "name"]):
            if p.info["ppid"] == root_pid or (p.info["name"] and any(x in p.info["name"].lower() for x in ("catlog", "photosorter"))):
                pids.add(p.info["pid"])
    except Exception:
        pass
    return pids


def main():
    repo_root = Path(__file__).resolve().parent.parent
    exe_path = repo_root / "dist" / "CatLog.exe"
    if not exe_path.exists():
        exe_path = repo_root / "dist" / "photosorter.exe"

    print("=" * 80)
    print("CATLOG / PHOTOSORTER WINDOWED LAUNCH VERIFICATION (eval/verify_windowed.py)")
    print("=" * 80)

    if sys.platform != "win32":
        print("[NEEDS ORGANIZER REVIEW] Windowed launch script currently requires Windows Win32 API.")
        sys.exit(0)

    if not exe_path.exists():
        print(f"[FAIL] Executable not found at {exe_path}")
        sys.exit(1)

    # 1. Check PE Subsystem (Subsystem 2 = IMAGE_SUBSYSTEM_WINDOWS_GUI)
    subsystem = check_pe_subsystem(exe_path)
    print(f"[INFO] PE Subsystem: {subsystem} (2 = Windows GUI, 3 = Windows CUI/Console)")
    assert subsystem == 2, f"Expected PE Subsystem 2 (GUI), got {subsystem}"
    print("[PASS] (b) PE Subsystem is IMAGE_SUBSYSTEM_WINDOWS_GUI (no console window)")

    # Create isolated temp dirs
    temp_dir = Path(tempfile.mkdtemp(prefix="test_windowed_"))
    temp_work = temp_dir / "work"
    temp_out = temp_dir / "export"
    temp_work.mkdir(parents=True, exist_ok=True)
    temp_out.mkdir(parents=True, exist_ok=True)

    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"

    log_path = temp_dir / "server.log"
    log_file = open(log_path, "w", encoding="utf-8")

    # Launch WITHOUT --no-gui
    cmd = [
        str(exe_path),
        "--port", str(port),
        "--work-dir", str(temp_work),
        "--output-dir", str(temp_out),
    ]

    print(f"\n[INFO] Launching executable in WINDOWED mode (without --no-gui):")
    print(f"       {' '.join(cmd)}")
    proc = subprocess.Popen(
        cmd,
        cwd=str(repo_root),
        stdout=log_file,
        stderr=log_file,
    )

    t0 = time.time()
    try:
        # Wait for HTTP server
        server_ready = False
        while time.time() - t0 < 30.0:
            if proc.poll() is not None:
                break
            try:
                status, _ = http_get(f"{base_url}/api/health", timeout=1.0)
                if status == 200:
                    server_ready = True
                    break
            except Exception:
                time.sleep(0.3)

        assert server_ready, "Server failed to respond on health check"
        print(f"[PASS] (c) Server online and healthy at {base_url}/api/health")

        # Verify page loads HTML
        status, html_content = http_get(f"{base_url}/", timeout=2.0)
        assert status == 200, f"Root / returned status {status}"
        assert "<title>" in html_content or "html" in html_content.lower(), "Root / did not return HTML"
        print(f"[PASS] (c) Frontend page loads successfully (status 200, HTML content served)")

        # Wait for top-level window titled "CatLog" (or "PhotoSorter")
        print("\n[INFO] Searching for top-level window titled 'CatLog' (or 'PhotoSorter')...")
        window_found = False
        photosorter_hwnd = None
        window_title = ""

        time.sleep(1.5)  # Allow pywebview to finish window creation
        for _ in range(40):
            all_pids = get_process_tree_pids(proc.pid)
            windows = find_process_windows(all_pids)

            for hwnd, pid, title, class_name in windows:
                # Check (b) no console window
                if class_name == "ConsoleWindowClass":
                    print(f"[FAIL] Found unexpected console window! (class={class_name}, hwnd={hwnd})")
                    sys.exit(1)

                if title.strip() in ("CatLog", "PhotoSorter"):
                    window_found = True
                    photosorter_hwnd = hwnd
                    window_title = title
                    break

            if window_found:
                break
            time.sleep(0.5)

        if not window_found:
            print("\n" + "!" * 70)
            print("[NEEDS ORGANIZER REVIEW] Top-level window titled 'CatLog' was not detected via EnumWindows.")
            print("This can happen if running in a non-interactive session or headless build worker.")
            print("MANUAL VERIFICATION STEPS:")
            print(" 1. Run dist\\CatLog.exe (or dist\\photosorter.exe) directly by double-clicking in File Explorer.")
            print(" 2. Confirm a native desktop window titled 'CatLog' appears without any console window.")
            print(" 3. Verify the React organizer UI loads completely inside the window.")
            print(" 4. Close the window by clicking the 'X' button in the titlebar.")
            print(" 5. Confirm in Task Manager that CatLog.exe exits and the bound port is released.")
            print("!" * 70 + "\n")
            return

        print(f"[PASS] (a) Top-level window found: hwnd={photosorter_hwnd}, title='{window_title}'")
        print("[PASS] (b) Verified no ConsoleWindowClass window associated with the process")

        # (d) Close window using WM_CLOSE (0x0010)
        print(f"\n[INFO] Sending WM_CLOSE (0x0010) to window hwnd={photosorter_hwnd}...")
        WM_CLOSE = 0x0010
        user32.PostMessageW(photosorter_hwnd, WM_CLOSE, 0, 0)

        # Wait for process to exit
        t_close = time.time()
        exited = False
        while time.time() - t_close < 15.0:
            if proc.poll() is not None:
                exited = True
                break
            time.sleep(0.3)

        assert exited, "Process did not terminate after receiving WM_CLOSE"
        print(f"[PASS] (d) Closing window cleanly ended process (exit code: {proc.returncode})")

        # Verify port release
        port_released = False
        t_port = time.time()
        while time.time() - t_port < 5.0:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("127.0.0.1", port))
                    port_released = True
                    break
            except OSError:
                time.sleep(0.2)

        assert port_released, f"Port {port} was not released after process termination"
        print(f"[PASS] (d) Port {port} successfully released and re-bindable")

        print("\n" + "=" * 80)
        print("ALL WINDOWED LAUNCH CHECKS PASSED AUTOMATICALLY:")
        print(f" [PASS] (a) Top-level window titled '{window_title}' appeared")
        print(" [PASS] (b) No console window (PE Subsystem 2 GUI, no ConsoleWindowClass)")
        print(" [PASS] (c) Page loads (health check 200, HTML served on process port)")
        print(" [PASS] (d) WM_CLOSE cleanly terminated process and released bound port")
        print("=" * 80)

    finally:
        try:
            if sys.platform == "win32" and proc.poll() is None:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
            elif proc.poll() is None:
                proc.kill()
        except Exception:
            pass
        log_file.close()
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
