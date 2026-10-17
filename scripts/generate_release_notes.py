"""Generate markdown release notes for CatLog release."""

from __future__ import annotations
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def generate_release_notes(dist_dir: Path | None = None, out_file: Path | None = None):
    dist_dir = dist_dir or (REPO_ROOT / "dist_release")
    out_file = out_file or (REPO_ROOT / "RELEASE_NOTES.md")

    version_file = REPO_ROOT / "VERSION"
    version = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else "0.1.0-rc1"
    tag = os.environ.get("TAG", f"v{version}")

    sums_file = dist_dir / "SHA256SUMS.txt"
    checksums_table = ""

    if sums_file.exists():
        lines = sums_file.read_text(encoding="utf-8").strip().splitlines()
        checksums_table = "| Package Archive | SHA-256 Checksum | Platform Status |\n| :--- | :--- | :---: |\n"
        for line in lines:
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                digest, name = parts[0], parts[1]
                status = "**Stable**" if "windows" in name else "**Beta**"
                checksums_table += f"| `{name}` | `{digest}` | {status} |\n"
    else:
        checksums_table = "_Checksums manifest will be attached upon release publication._\n"

    notes = f"""# CatLog {tag}

**Who was at the event?**
*The privacy-first event photo organizer, face clustering engine, and static gallery generator.*

---

### Downloads & Verification

{checksums_table}

*Verification*: Compare your downloaded file checksum against `SHA256SUMS.txt` using:
- **Windows (PowerShell)**: `Get-FileHash <file> -Algorithm SHA256`
- **macOS / Linux**: `sha256sum <file>`

---

### Important Release Notices

#### 1. Pre-Trained Face Models (Downloaded on First Run)
- Face detection (**SCRFD 10G**) and recognition (**ArcFace ResNet50**) deep learning model weights (`buffalo_l` pack, ~300 MB) are **NOT bundled** in the release archives to keep downloads portable (~150 MB) and strictly comply with upstream licensing terms.
- On first launch, CatLog automatically downloads the official model pack directly from InsightFace upstream to your local user cache (`~/.insightface/models/buffalo_l/`).
- **Notice**: Pre-trained InsightFace model weights are provided strictly for **non-commercial research and evaluation purposes**.

#### 2. Platform Status & Unsigned Binary Guidance
- **Windows (x64)**: Stable production build. When first running on Windows, Defender SmartScreen may display an alert. Click **More info** &rarr; **Run anyway**.
- **macOS (Apple Silicon & Intel)**: Portable **Beta** release. When launching on macOS, Gatekeeper may indicate the developer cannot be verified. Right-click (or Control-click) `CatLog` &rarr; select **Open** &rarr; click **Open**. Alternatively, allow via *System Settings > Privacy & Security*.
- **Linux (x64)**: Portable **Beta** release. Extract the `.tar.gz` and run `./CatLog/CatLog`. If WebKitGTK is not installed on your system, CatLog will automatically fall back to opening in your default web browser.

#### 3. Privacy Guarantee
- **100% Local Processing**: All face detection, embedding vectors, and clustering run on your CPU.
- Zero photo bytes, faces, or identity templates are ever transmitted to any third party or cloud AI service.
- User projects and application settings are stored locally in `~/.catlog/`.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [LICENSE](LICENSE) for third-party software and copyright details.
"""

    out_file.write_text(notes, encoding="utf-8")
    print(f"Generated {out_file} ({len(notes.splitlines())} lines).")


if __name__ == "__main__":
    generate_release_notes()
