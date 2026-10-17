"""Sync VERSION file with Windows version_info.txt and package.json files."""

from __future__ import annotations
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def sync_version():
    version_file = REPO_ROOT / "VERSION"
    if not version_file.exists():
        version_file.write_text("0.1.0-rc1\n", encoding="utf-8")
    
    version_str = version_file.read_text(encoding="utf-8").strip()

    # Parse numeric components for VSVersionInfo (e.g., 0.1.0-rc1 -> 0, 1, 0, 0)
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", version_str)
    if match:
        major, minor, patch = match.groups()
        build = 0
    else:
        major, minor, patch, build = 0, 1, 0, 0

    four_tuple = f"({major}, {minor}, {patch}, {build})"

    # Update version_info.txt
    version_info_path = REPO_ROOT / "version_info.txt"
    if version_info_path.exists():
        content = version_info_path.read_text(encoding="utf-8")
        content = re.sub(r"filevers=\(\d+,\s*\d+,\s*\d+,\s*\d+\)", f"filevers={four_tuple}", content)
        content = re.sub(r"prodvers=\(\d+,\s*\d+,\s*\d+,\s*\d+\)", f"prodvers={four_tuple}", content)
        content = re.sub(r"StringStruct\('FileVersion',\s*'[^']+'\)", f"StringStruct('FileVersion', '{version_str}')", content)
        content = re.sub(r"StringStruct\('ProductVersion',\s*'[^']+'\)", f"StringStruct('ProductVersion', '{version_str}')", content)
        version_info_path.write_text(content, encoding="utf-8")
        print(f"Updated {version_info_path} to version {version_str} {four_tuple}")

    # Update package.json files
    for pkg_rel in ["package.json", "frontend/package.json", "viewer/package.json"]:
        pkg_path = REPO_ROOT / pkg_rel
        if pkg_path.exists():
            pkg_content = pkg_path.read_text(encoding="utf-8")
            pkg_content = re.sub(r'"version":\s*"[^"]+"', f'"version": "{version_str}"', pkg_content)
            pkg_path.write_text(pkg_content, encoding="utf-8")
            print(f"Updated {pkg_rel} to version {version_str}")


if __name__ == "__main__":
    sync_version()
