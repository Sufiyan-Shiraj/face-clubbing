"""Native OS Dialog helper for PhotoSorter.

Provides reliable folder/file pickers that pop up in the foreground
even when triggered from a background web server on Windows, macOS, or Linux.
"""

import sys
import os
import base64
import subprocess
from pathlib import Path
from typing import Optional


def open_folder_dialog(initial_dir: Optional[str] = None, title: str = "Select Public Export Directory") -> Optional[str]:
    """Launch a native system folder picker in the foreground."""
    init_path = ""
    if initial_dir and Path(initial_dir).exists():
        init_path = str(Path(initial_dir).resolve())

    # Strategy 1 (Windows): PowerShell with .NET FolderBrowserDialog + TopMost owner form
    # We use -EncodedCommand (Base64 UTF-16LE) to completely avoid shell escaping / quote issues.
    if sys.platform == "win32":
        try:
            escaped_dir = init_path.replace("'", "''")
            escaped_title = title.replace("'", "''")
            ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms

$fbd = New-Object System.Windows.Forms.FolderBrowserDialog
$fbd.Description = '{escaped_title}'
$fbd.ShowNewFolderButton = $true
$fbd.AutoUpgradeEnabled = $true
if ('{escaped_dir}' -and (Test-Path '{escaped_dir}')) {{
    $fbd.SelectedPath = '{escaped_dir}'
}}

$topForm = New-Object System.Windows.Forms.Form
$topForm.TopMost = $true
$topForm.StartPosition = 'CenterScreen'
$topForm.Width = 10
$topForm.Height = 10
$topForm.Opacity = 0.01
$topForm.ShowInTaskbar = $true
$topForm.Text = '{escaped_title}'
$topForm.Show()
$topForm.BringToFront()
$topForm.Activate()

$res = $fbd.ShowDialog($topForm)
$topForm.Close()

if ($res -eq [System.Windows.Forms.DialogResult]::OK) {{
    Write-Output ("SELECTED:" + $fbd.SelectedPath)
}} else {{
    Write-Output "CANCELLED"
}}
"""
            encoded = base64.b64encode(ps_script.encode("utf-16le")).decode("ascii")
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded],
                capture_output=True,
                text=True,
                timeout=300,
            )
            for line in proc.stdout.splitlines():
                line = line.strip()
                if line.startswith("SELECTED:"):
                    chosen = line[len("SELECTED:"):].strip()
                    if chosen and Path(chosen).exists():
                        return chosen
                elif line == "CANCELLED":
                    return None
        except Exception as e:
            print(f"[dialog] PowerShell dialog error: {e}", file=sys.stderr)

    # Strategy 2 (macOS): AppleScript native folder chooser
    if sys.platform == "darwin":
        try:
            osa_script = f'POSIX path of (choose folder with prompt "{title}")'
            proc = subprocess.run(
                ["osascript", "-e", osa_script],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if proc.returncode == 0:
                chosen = proc.stdout.strip()
                if chosen and Path(chosen).exists():
                    return chosen
            return None
        except Exception as e:
            print(f"[dialog] AppleScript error: {e}", file=sys.stderr)

    # Strategy 3 (Linux / Universal Fallback): Tkinter with TopMost mapped window
    try:
        escaped_init = init_path.replace("'", "\\'")
        escaped_title = title.replace("'", "\\'")
        tk_code = f"""
import sys
from pathlib import Path
try:
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.title('{escaped_title}')
    root.geometry('1x1+0+0')
    root.attributes('-alpha', 0.01)
    root.attributes('-topmost', True)
    root.lift()
    root.focus_force()
    root.update()
    initial = r'{escaped_init}' if r'{escaped_init}' else None
    res = filedialog.askdirectory(
        parent=root,
        initialdir=initial,
        title=r'{escaped_title}',
        mustexist=False
    )
    root.destroy()
    if res:
        print('SELECTED:' + str(Path(res).resolve()), flush=True)
    else:
        print('CANCELLED', flush=True)
except Exception as e:
    print('ERROR:' + str(e), file=sys.stderr, flush=True)
"""
        proc = subprocess.run(
            [sys.executable, "-c", tk_code],
            capture_output=True,
            text=True,
            timeout=300,
        )
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line.startswith("SELECTED:"):
                chosen = line[len("SELECTED:"):].strip()
                if chosen and Path(chosen).exists():
                    return chosen
            elif line == "CANCELLED":
                return None
    except Exception as e:
        print(f"[dialog] Tkinter error: {e}", file=sys.stderr)

    return None
