"""Script to package complete release bundles for Windows, macOS, and Linux."""

import os
import sys
import shutil
import zipfile
import tarfile
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_RELEASE = REPO_ROOT / "dist_release"
DIST_RELEASE.mkdir(parents=True, exist_ok=True)


def get_version() -> str:
    v_file = REPO_ROOT / "VERSION"
    if v_file.exists():
        return v_file.read_text(encoding="utf-8").strip()
    return "0.1.0-rc1"


def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def build_unix_bundle(platform_name: str, ext: str):
    version = get_version()
    archive_name = f"CatLog-{version}-{platform_name}.{ext}"
    out_archive = DIST_RELEASE / archive_name

    print(f"[INFO] Building {platform_name} portable distribution: {archive_name}")

    # Files to include in the portable Unix package
    bundle_files = [
        ("run.sh", REPO_ROOT / "run.sh", 0o755),
        ("main.py", REPO_ROOT / "main.py", 0o644),
        ("requirements.txt", REPO_ROOT / "requirements.txt", 0o644),
        ("README.md", REPO_ROOT / "README.md", 0o644),
        ("LICENSE", REPO_ROOT / "LICENSE", 0o644),
        ("THIRD_PARTY_NOTICES.md", REPO_ROOT / "THIRD_PARTY_NOTICES.md", 0o644),
        ("VERSION", REPO_ROOT / "VERSION", 0o644),
        ("catlog.ico", REPO_ROOT / "catlog.ico", 0o644),
    ]

    # Directories to include
    bundle_dirs = [
        ("backend", REPO_ROOT / "backend"),
        ("frontend/dist", REPO_ROOT / "frontend" / "dist"),
        ("viewer/dist", REPO_ROOT / "viewer" / "dist"),
    ]

    readme_content = f"""CatLog {version} ({platform_name.upper()})
=======================================
Privacy-first event photo organizer, face clustering engine, and static gallery generator.

QUICK START:
1. Ensure Python 3.10+ is installed on your system.
2. Open a terminal inside this folder.
3. Run the launch script:
     chmod +x run.sh
     ./run.sh
4. CatLog will automatically set up its environment, download dependencies,
   and launch the desktop user interface.

If you prefer using uv (ultra-fast package manager):
     pip install uv
     ./run.sh

PRIVACY:
100% of face detection, embedding vectors, and clustering run locally on your machine.
Zero photos or attendee biometrics are ever sent to any cloud server.
"""

    if ext == "tar.gz":
        with tarfile.open(out_archive, "w:gz") as tar:
            guide_data = readme_content.encode("utf-8")
            ti = tarfile.TarInfo(name=f"CatLog-{version}-{platform_name}/QUICKSTART.txt")
            ti.size = len(guide_data)
            ti.mode = 0o644
            import io
            tar.addfile(ti, io.BytesIO(guide_data))

            for arcname, fpath, mode in bundle_files:
                if fpath.exists():
                    ti = tar.gettarinfo(str(fpath), arcname=f"CatLog-{version}-{platform_name}/{arcname}")
                    ti.mode = mode
                    with open(fpath, "rb") as f:
                        tar.addfile(ti, f)

            for arc_prefix, dir_path in bundle_dirs:
                if dir_path.exists():
                    for root, dirs, files in os.walk(dir_path):
                        rel = Path(root).relative_to(dir_path)
                        for f in files:
                            fp = Path(root) / f
                            arc = f"CatLog-{version}-{platform_name}/{arc_prefix}/{rel / f}".replace("\\", "/")
                            ti = tar.gettarinfo(str(fp), arcname=arc)
                            ti.mode = 0o644
                            with open(fp, "rb") as f:
                                tar.addfile(ti, f)
    else:  # zip
        with zipfile.ZipFile(out_archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"CatLog-{version}-{platform_name}/QUICKSTART.txt", readme_content)

            for arcname, fpath, mode in bundle_files:
                if fpath.exists():
                    zinfo = zipfile.ZipInfo(f"CatLog-{version}-{platform_name}/{arcname}")
                    zinfo.external_attr = mode << 16
                    with open(fpath, "rb") as f:
                        zf.writestr(zinfo, f.read())

            for arc_prefix, dir_path in bundle_dirs:
                if dir_path.exists():
                    for root, dirs, files in os.walk(dir_path):
                        rel = Path(root).relative_to(dir_path)
                        for f in files:
                            fp = Path(root) / f
                            arc = f"CatLog-{version}-{platform_name}/{arc_prefix}/{rel / f}".replace("\\", "/")
                            zf.write(fp, arcname=arc)

    digest = compute_sha256(out_archive)
    (DIST_RELEASE / f"{archive_name}.sha256").write_text(f"{digest}  {archive_name}\n", encoding="utf-8")
    print(f"[PASS] Created {out_archive} ({out_archive.stat().st_size:,} bytes) SHA-256: {digest}")


def main():
    print("=== Packaging CatLog Multi-Platform Release Archives ===")
    build_unix_bundle("macos-universal", "zip")
    build_unix_bundle("linux-x64", "tar.gz")

    # Generate unified SHA256SUMS.txt
    archives = sorted(list(DIST_RELEASE.glob("CatLog-*.zip")) + list(DIST_RELEASE.glob("CatLog-*.tar.gz")))
    sums_file = DIST_RELEASE / "SHA256SUMS.txt"
    lines = []
    for a in archives:
        lines.append(f"{compute_sha256(a)}  {a.name}")
    sums_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[INFO] Updated {sums_file} with {len(lines)} archive checksums:")
    for line in lines:
        print(f"  {line}")


if __name__ == "__main__":
    main()
