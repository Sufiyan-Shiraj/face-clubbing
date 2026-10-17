"""Packaging script for CatLog release archives across all platforms.

Collects the compiled standalone binary along with README.md, LICENSE,
THIRD_PARTY_NOTICES.md, and VERSION into portable archives:
  - Windows x64: CatLog-<version>-windows-x64.zip
  - macOS arm64: CatLog-<version>-macos-arm64.zip
  - macOS x64:   CatLog-<version>-macos-x64.zip
  - Linux x64:   CatLog-<version>-linux-x64.tar.gz
Computes SHA-256 checksums and generates SHA256SUMS.txt.
"""

from __future__ import annotations
import os
import sys
import shutil
import zipfile
import tarfile
import hashlib
import argparse
import platform
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def get_version() -> str:
    version_file = REPO_ROOT / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.1.0-rc1"


def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def detect_platform() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "windows":
        return "windows-x64"
    elif system == "darwin":
        if "arm" in machine or "aarch64" in machine:
            return "macos-arm64"
        return "macos-x64"
    elif system == "linux":
        return "linux-x64"
    return f"{system}-{machine}"


def package_release(
    version: str | None = None,
    target_platform: str | None = None,
    out_dir: str | Path | None = None,
    generate_all_checksums: bool = False,
) -> Path | None:
    version = version or get_version()
    target_platform = target_platform or detect_platform()
    out_dir = Path(out_dir or (REPO_ROOT / "dist_release"))
    out_dir.mkdir(parents=True, exist_ok=True)

    if generate_all_checksums:
        # Generate SHA256SUMS.txt for all existing archives in out_dir
        archives = sorted(list(out_dir.glob("CatLog-*.zip")) + list(out_dir.glob("CatLog-*.tar.gz")))
        if not archives:
            print(f"[WARNING] No CatLog archives found in {out_dir}")
            return None
        sums_file = out_dir / "SHA256SUMS.txt"
        lines = []
        for arch in archives:
            digest = compute_sha256(arch)
            lines.append(f"{digest}  {arch.name}")
        sums_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"[INFO] Generated {sums_file} ({len(lines)} entries):")
        for line in lines:
            print(f"  {line}")
        return sums_file

    print("=" * 70)
    print(f"PACKAGING CATLOG RELEASE ARTIFACT: {target_platform} (v{version})")
    print("=" * 70)

    # Locate binary
    if "windows" in target_platform:
        exe_candidates = [
            REPO_ROOT / "dist" / "CatLog.exe",
            REPO_ROOT / "dist" / "CatLog" / "CatLog.exe",
        ]
        archive_name = f"CatLog-{version}-windows-x64.zip"
        is_tar = False
    elif "macos" in target_platform:
        exe_candidates = [
            REPO_ROOT / "dist" / "CatLog",
            REPO_ROOT / "dist" / "CatLog.app" / "Contents" / "MacOS" / "CatLog",
            REPO_ROOT / "dist" / "CatLog" / "CatLog",
        ]
        suffix = "macos-arm64" if "arm64" in target_platform else "macos-x64"
        archive_name = f"CatLog-{version}-{suffix}.zip"
        is_tar = False
    else:  # Linux
        exe_candidates = [
            REPO_ROOT / "dist" / "CatLog",
            REPO_ROOT / "dist" / "CatLog" / "CatLog",
        ]
        archive_name = f"CatLog-{version}-linux-x64.tar.gz"
        is_tar = True

    binary_path = None
    for cand in exe_candidates:
        if cand.exists() and cand.is_file():
            binary_path = cand
            break

    if not binary_path:
        raise FileNotFoundError(
            f"Could not find compiled CatLog binary in dist/. Checked: {exe_candidates}"
        )

    print(f"[INFO] Found binary: {binary_path} ({binary_path.stat().st_size:,} bytes)")

    # Additional documentation files to bundle
    doc_files = [
        ("README.md", REPO_ROOT / "README.md"),
        ("LICENSE", REPO_ROOT / "LICENSE"),
        ("THIRD_PARTY_NOTICES.md", REPO_ROOT / "THIRD_PARTY_NOTICES.md"),
        ("VERSION", REPO_ROOT / "VERSION"),
    ]

    archive_path = out_dir / archive_name
    binary_name = binary_path.name

    if is_tar:
        print(f"[INFO] Creating tar.gz archive: {archive_path}")
        with tarfile.open(archive_path, "w:gz") as tar:
            # Set executable permissions on binary
            tarinfo = tar.gettarinfo(str(binary_path), arcname=f"CatLog/{binary_name}")
            tarinfo.mode = 0o755
            with open(binary_path, "rb") as f:
                tar.addfile(tarinfo, f)

            for arcname, doc_path in doc_files:
                if doc_path.exists():
                    doc_tarinfo = tar.gettarinfo(str(doc_path), arcname=f"CatLog/{arcname}")
                    doc_tarinfo.mode = 0o644
                    with open(doc_path, "rb") as f:
                        tar.addfile(doc_tarinfo, f)
    else:
        print(f"[INFO] Creating zip archive: {archive_path}")
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            # On Unix systems preserve executable bits in zip
            if not sys.platform.startswith("win"):
                zinfo = zipfile.ZipInfo(f"CatLog/{binary_name}")
                zinfo.external_attr = 0o755 << 16  # rwxr-xr-x
                with open(binary_path, "rb") as f:
                    zf.writestr(zinfo, f.read())
            else:
                zf.write(binary_path, arcname=f"CatLog/{binary_name}")

            for arcname, doc_path in doc_files:
                if doc_path.exists():
                    zf.write(doc_path, arcname=f"CatLog/{arcname}")

    archive_size = archive_path.stat().st_size
    checksum = compute_sha256(archive_path)
    print(f"[PASS] Archive created: {archive_path} ({archive_size:,} bytes)")
    print(f"[PASS] SHA-256: {checksum}")

    # Write single checksum sidecar file
    sidecar = out_dir / f"{archive_name}.sha256"
    sidecar.write_text(f"{checksum}  {archive_name}\n", encoding="utf-8")

    return archive_path


def main():
    parser = argparse.ArgumentParser(description="Package CatLog release artifacts")
    parser.add_argument("--version", default=None, help="Version string (e.g. 0.1.0-rc1)")
    parser.add_argument("--platform", default=None, help="Target platform (windows-x64, linux-x64, macos-arm64, macos-x64)")
    parser.add_argument("--out-dir", default=None, help="Output directory for archives (default: dist_release/)")
    parser.add_argument("--generate-sums", action="store_true", help="Generate SHA256SUMS.txt for all archives in out-dir")
    args = parser.parse_args()

    try:
        package_release(
            version=args.version,
            target_platform=args.platform,
            out_dir=args.out_dir,
            generate_all_checksums=args.generate_sums,
        )
    except Exception as e:
        print(f"[ERROR] Packaging failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
