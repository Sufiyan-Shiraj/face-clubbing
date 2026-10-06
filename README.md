# PhotoSorter

PhotoSorter is a free, privacy-first, desktop application and static site generator designed for event organizers. It takes an event's photos, groups them by person using face detection and embedding clustering (powered by InsightFace), and exports a lightweight static web gallery where attendees can quickly find all photos they appear in and download the originals without duplication.

---

## Project Status

| Phase | Description | Status |
|---|---|---|
| **Phase 0** | Setup, environment, and risk check | **Done** |
| **Phase 1** | Engine core (CLI, face detection, seed/attach, merge) | **Accepted** |
| **Phase 1b** | Engine amendments (stable identity, edit replay, 0.65 band, eval suite) | **Completed** |
| **Phase 2** | Static viewer (single people grid, unrecognized view, hide toggle) | Built (Pending rev 2 update) |
| **Phase 3-9** | FastAPI API, Desktop UI, Drive integration, packaging | Not started |

---

## Key Features

- **No Duplication:** Group photos are indexed once and mapped to every detected person. Original photos remain untouched.
- **Organizer-Centric:** Built for event organizers with a modern desktop UI (React + pywebview + FastAPI) and zero complex server setup.
- **Nobody Dropped:** Low-quality or small faces and photos with no detected faces are categorized into an **Unrecognized** gallery, ensuring 100% of event photos are accessible.
- **Static Public Viewer:** Generates a lightweight static website (`export/`) ready to host on GitHub Pages, Cloudflare Pages, or any static host.
- **Multiple Sources:** Works with local folders, zip files, and Google Drive links (read-only with an API key, or optional OAuth upload).

---

## Architecture

```
+--------------------------------------------------------------+
|  Desktop App                                                 |
|                                                              |
|  pywebview window  --->  React UI (bundled static assets)    |
|                              |  HTTP + SSE                   |
|                              v                               |
|                      FastAPI (localhost, random port)        |
|                              |                               |
|                              v                               |
|   Engine: scan -> detect -> embed -> cluster -> export       |
|   Drive module: read (API key) / upload (OAuth, optional)    |
+--------------------------------------------------------------+
                              |
                              v  (export bundle)
+--------------------------------------------------------------+
|  Static Viewer Site (React / HTML + CSS)                     |
|  reads people.json + config.json + thumbs/faces              |
|  download buttons -> original files (local / Google Drive)   |
+--------------------------------------------------------------+
```

---

## Quick Start (Run from Source)

### Prerequisites
- Python 3.10 to 3.12 recommended
- Git

### Windows
```powershell
git clone <repo-url>
cd face-clubbing
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m backend.engine --input test_photos --out export
```

### macOS / Linux
```bash
git clone <repo-url>
cd face-clubbing
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m backend.engine --input test_photos --out export
```

---

## Export Bundle Structure

```
export/
  config.json        # Theme, event name, accent color, and branding
  people.json        # People clusters, metadata, and photo references
  faces/             # Representative square face crops for each cluster
  thumbs/            # Lightweight JPEG thumbnails for gallery preview
```

---

## Privacy and Ethics

- **Biometric Data:** Face detection models produce mathematical embeddings (vectors) used exclusively for local clustering. No facial biometric data is shared with third parties or external cloud APIs.
- **Attendee Privacy:** We strongly advise event organizers to obtain attendee consent before publishing galleries and use unguessable URLs when hosting static viewer sites.
- **Review & Removal:** The organizer UI allows clusters to be manually hidden or modified upon request.

---

## Licensing & Model Notice

- **Software License:** PhotoSorter's code is licensed under the [MIT License](LICENSE).
- **InsightFace Pretrained Models:** The pretrained face analysis models (such as `buffalo_l`) are provided by the InsightFace project and are strictly for **non-commercial research and educational use**. By using these models, you agree to InsightFace's license terms. For commercial deployments, a commercially licensed face recognition model must be substituted.
