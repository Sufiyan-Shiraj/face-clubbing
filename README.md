# CatLog

<p align="center">
  <img src="frontend/public/catlog-logo.png" alt="CatLog Logo" width="360" />
</p>

<p align="center">
  <strong>Who was at the event?</strong><br>
  <em>The privacy-first event photo organizer, face clustering engine, and static gallery generator.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python&logoColor=white" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/React-19-61DAFB.svg?style=flat&logo=react&logoColor=black" alt="React 19" />
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Vite-6.4+-646CFF.svg?style=flat&logo=vite&logoColor=white" alt="Vite" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg?style=flat" alt="MIT License" />
</p>

---

## Overview

**CatLog** is a modern, privacy-first desktop application and static site generator designed for event organizers, conference coordinators, and photographers. 

It takes an event's photo collection, detects faces, extracts mathematical embeddings using **InsightFace** (ArcFace/RetinaFace), groups attendees with high-precision clustering, and provides an interactive visual review interface. Finally, it exports a lightweight, ultra-responsive web gallery where attendees can quickly find all photos they appear in and download the original full-resolution files without file duplication.

---

## Key Features

- **🔒 100% Privacy & Local Processing**  
  All face detection, facial embedding, and clustering algorithms run strictly on your local machine. No attendee biometrics, photos, or personal data are ever uploaded to cloud AI providers.
- **📁 Universal Source Ingestion**  
  Scan photos from **Local Folders**, compressed **ZIP Archives**, or **Google Drive** links (read-only using a public API key, no OAuth/Google login required).
- **🐱 Interactive Mascot & Tour Guide**  
  Features **Camera Cat**, CatLog's signature mascot illustrated across 8 distinct poses and 3 Risograph color themes (*Dark Slate*, *Deep Navy*, and *Riso Paper*). An interactive 11-step spotlight tour walks organizers through key tools, keyboard shortcuts, and clustering sliders.
- **🎯 Visual Review & Smart Suggestions**  
  - **Ranked Merging Suggestions**: Automatically surfaces attendee clusters with similar facial features in the $[0.50, 0.65]$ distance band.
  - **Unrecognized Face Triage**: Rapidly inspect faces that did not automatically attach to clusters; multi-select and assign them to existing people or create new profiles with one click.
  - **Interactive Lightbox with Bounding Boxes**: Click any photo to view detected face boxes with color-coded confidence indicators and on-canvas person reassignment.
  - **Full Undo/Redo**: Safely test threshold adjustments and manual merges with persistent edit replay.
- **🌐 Dual Export Options**  
  - **Standalone Single-File HTML**: An ultra-fast, zero-dependency, single HTML gallery file with embedded CSS, thumbnails, and client-side attendee filtering.
  - **Static Web Bundle**: A complete React web gallery ready for zero-cost deployment to GitHub Pages, Cloudflare Pages, AWS S3, or Netlify.
- **🎨 Public Static Viewer Rework & Per-Person Downloads**  
  - **3 Color Themes**: Instant toggle between *Dark Slate*, *Riso Paper*, and *Deep Navy* with persistent theme memory.
  - **Per-Person Downloads**: Attendees can click "Download all N photos" or enter **Select Mode** to tick specific photos and download a custom selection.
  - **Client-Side ZIP Streaming**: Local exports stream-build a single ZIP using `client-zip` directly in the browser with live progress and cancel—no server required and low memory footprint.
  - **Sequential Google Drive Direct Downloads**: Google Drive exports download photos one by one via direct Drive URLs with clear browser permission prompts and "Open in Drive" fallback.
  - **Sanitized Filenames**: Downloads follow clean `personname_001.jpg` naming without exposing private directory paths or attendee IDs.
- **🔄 Open Saved Projects**  
  Resume past events instantly! Reopen existing export directories without re-scanning or re-embedding photos.
- **⚡ Zero Photo Duplication**  
  Group photos are indexed once and mapped to every detected attendee. Original photos remain untouched.

---

## Architecture

```
+--------------------------------------------------------------------------+
|  CatLog Desktop Application                                              |
|                                                                          |
|  pywebview Window  --->  React 19 UI (Vite + TypeScript + Tailwind)      |
|                              |  HTTP + SSE Event Stream                  |
|                              v                                           |
|                      FastAPI Server (localhost, random available port)   |
|                              |                                           |
|                              v                                           |
|   Clustering Engine: Scan -> Detect -> Embed -> Cluster -> Re-attach     |
|   InsightFace (buffalo_l) / ArcFace 512D / NumPy / OpenCV                |
|   Google Drive Module: Direct API v3 download & thumbnail fetch          |
+--------------------------------------------------------------------------+
                               |
                               v  (Export Pipeline)
+--------------------------------------------------------------------------+
|  Published Attendee Galleries                                            |
|                                                                          |
|  [Mode A] Single-File Standalone HTML (`index.html` ~ zero-dependency)   |
|  [Mode B] Static Web Bundle (`people.json`, `faces/`, `thumbs/`)         |
|  Attendee Search & Lightbox -> Direct downloads of original images       |
+--------------------------------------------------------------------------+
```

---

## Technology Stack

| Component | Technologies |
|---|---|
| **Desktop Shell** | Python 3.11+, `pywebview` 5.x, Windows Base64 native folder dialogs |
| **Backend API** | FastAPI, Uvicorn, SSE Starlette streaming, Pydantic V2 |
| **Machine Learning** | InsightFace (`buffalo_l`), ONNX Runtime, NumPy, SciPy |
| **Organizer UI** | React 19, TypeScript, Vite, Tailwind CSS, Lucide Icons |
| **Gallery Viewers** | Standalone Single-File HTML5 (Vanilla JS) & Static React Viewer |
| **Testing** | Pytest (83 tests), Vitest (73 tests, 13 test suites) |

---

## Quick Start (Run from Source)

### Prerequisites

1. **Python 3.11+** installed and available on PATH.
2. **Node.js 18+** & **npm** installed.
3. **Git** for repository cloning.

### Installation

```bash
# 1. Clone repository
git clone https://github.com/Sufiyan-Shiraj/face-clubbing.git
cd face-clubbing

# 2. Setup Python virtual environment & dependencies
python -m venv .venv

# On Windows:
.venv\Scripts\activate
pip install -r requirements.txt

# On macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt

# 3. Install frontend dependencies & build bundle
cd frontend
npm install
npm run build
cd ..
```

### Launch Desktop Application

**Windows:**
```cmd
run.bat
```
*(Or run `.\.venv\Scripts\python.exe main.py`)*

**macOS / Linux:**
```bash
chmod +x run.sh
./run.sh
```
*(Or run `python3 main.py`)*

---

### Standalone Desktop Executable (Windows)

For running CatLog without installing Python, Node.js, or development tools:

- **Download**: Run `photosorter.exe` (or `CatLog.exe`) from `dist/` or project release artifacts.
- **System Requirements**: 64-bit Windows 10 (version 1809+) or Windows 11.
- **WebView2 Runtime**: CatLog's native window shell uses Microsoft Edge WebView2:
  - Windows 10 (recent versions) and Windows 11 come with WebView2 pre-installed by Microsoft out of the box.
  - If running on a stripped or enterprise LTSC/Server installation without WebView2, download the standard **Evergreen Bootstrapper** from [Microsoft's official WebView2 page](https://developer.microsoft.com/en-us/microsoft-edge/webview2/#download).
  - CatLog also supports headless batch mode via `--no-gui` if no desktop display is needed.

---

### Headless Engine (CLI Mode)

To run the clustering engine in headless batch mode without the graphical UI:

```powershell
python -m backend.engine --input path/to/event_photos --out export --threshold 0.50
```

---

## Export Gallery Bundle

When exporting an event, CatLog outputs a clean, publishable directory:

```
export/
  index.html         # Self-contained standalone gallery or static viewer loader
  config.json        # Event name, theme settings, and accent colors
  people.json        # People clusters, attendee indices, and photo references
  faces/             # Representative square face crops for each attendee
  thumbs/            # Lightweight WebP/JPEG thumbnails for fast browsing
```

To test the generated gallery locally:
```bash
cd export
python -m http.server 8080
```
Open `http://localhost:8080` in your browser.

---

## Mascot & Visual Design System

CatLog features the **Camera Cat** mascot, rendered across 8 dedicated poses and 3 Risograph-inspired themes:

- **Themes**:
  - `t-dark` — **Dark Slate**: High-contrast chalkboard aesthetic with warm chalk-white lines.
  - `t-navy` — **Deep Navy**: Rich editorial blue with warm orange and teal riso accents.
  - `t-paper` — **Riso Paper**: Tactile off-white newsprint aesthetic with misregistered ink offset.
- **Poses**:
  1. *Pose 1*: Hello & Welcome
  2. *Pose 2*: Looking Around & Investigating
  3. *Pose 3*: Pointing to Action
  4. *Pose 4*: Excited Celebration
  5. *Pose 5*: Working Hard at Computer
  6. *Pose 6*: Done & Verified
  7. *Pose 7*: Leaving with Packed Bundle
  8. *Pose 8*: Idle Resting Snooze

All poses are pre-rendered as transparent PNGs under `frontend/public/mascot/` for instantaneous rendering.

---

## Verification & Test Suites

The codebase is backed by full backend and frontend regression suites:

- **Backend Pytest**:
  ```bash
  .\.venv\Scripts\python -m pytest tests
  # 83 passed in ~84s
  ```
- **Frontend Vitest**:
  ```bash
  cd frontend
  npx vitest run
  # 13 test files passed, 73 tests passed in ~25s
  ```
- **Type Checking & Production Build**:
  ```bash
  cd frontend
  npm run build
  # 0 errors, built in ~13s
  ```

---

## Privacy, Ethics, and Model Notice

- **Biometric Vector Safety**: Mathematical embeddings (512D unit vectors) are used solely for local distance calculations. No biometric identifiers or templates are shared with third parties.
- **Attendee Consent**: We encourage event organizers to ensure attendee consent prior to publishing galleries online and to use unguessable subdomains or private hosting.
- **InsightFace Pretrained Models**: The pretrained face analysis models (e.g. `buffalo_l`) are provided by the InsightFace project and are intended for non-commercial research and educational use. For commercial deployments, consult InsightFace's license or substitute a commercially licensed recognition model.

---

## License

CatLog's application code is licensed under the [MIT License](LICENSE).
