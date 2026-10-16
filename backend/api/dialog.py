"""Native OS Dialog helper for PhotoSorter.

Provides reliable folder/file pickers that pop up in the foreground
even when triggered from a background web server on Windows, macOS, or Linux.
"""

import sys
import subprocess
from pathlib import Path
from typing import Optional


def open_folder_dialog(initial_dir: Optional[str] = None, title: str = "Select Public Export Directory") -> Optional[str]:
    """Launch a native system folder picker in the foreground."""
    init_path = ""
    if initial_dir and Path(initial_dir).exists():
        init_path = str(Path(initial_dir).resolve())

    # Strategy 1: Python subprocess with Tkinter and topmost attribute
    # Running in a new subprocess ensures Windows grants foreground window privileges.
    tk_code = f"""
import sys
from pathlib import Path
try:
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes('-topmost', 1)
    root.lift()
    root.focus_force()
    initial = r'''{init_path}''' if r'''{init_path}''' else None
    res = filedialog.askdirectory(
        parent=root,
        initialdir=initial,
        title=r'''{title}''',
        mustexist=False
    )
    root.destroy()
    if res:
        print('SELECTED:' + str(Path(res).resolve()))
    else:
        print('CANCELLED')
except Exception as e:
    print('ERROR:' + str(e), file=sys.stderr)
"""
    try:
        proc = subprocess.run(
            [sys.executable, "-c", tk_code],
            capture_output=True,
            text=True,
            timeout=300,  # 5 min timeout for user to pick
        )
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line.startswith("SELECTED:"):
                chosen = line[len("SELECTED:"):].strip()
                if chosen:
                    return chosen
            elif line == "CANCELLED":
                return None
    except Exception:
        pass

    # Strategy 2 (Windows only): PowerShell FolderBrowserDialog
    if sys.platform == "win32":
        escaped_path = init_path.replace("'", "''")
        init_script = f"$dialog.SelectedPath = '{escaped_path}';" if init_path else ""
        ps_code = f"""
Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = '{title}'
$dialog.ShowNewFolderButton = $true
{init_script}
$topForm = New-Object System.Windows.Forms.Form
$topForm.TopMost = $true
$topForm.StartPosition = 'CenterScreen'
$topForm.Width = 1
$topForm.Height = 1
$topForm.Show()
$topForm.BringToFront()
$res = $dialog.ShowDialog($topForm)
$topForm.Close()
if ($res -eq [System.Windows.Forms.DialogResult]::OK) {{
    Write-Output ("SELECTED:" + $dialog.SelectedPath)
}} else {{
    Write-Output "CANCELLED"
}}
"""
        try:
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_code],
                capture_output=True,
                text=True,
                timeout=300,
            )
            for line in proc.stdout.splitlines():
                line = line.strip()
                if line.startswith("SELECTED:"):
                    chosen = line[len("SELECTED:"):].strip()
                    if chosen:
                        return chosen
                elif line == "CANCELLED":
                    return None
        except Exception:
            pass

    return None
