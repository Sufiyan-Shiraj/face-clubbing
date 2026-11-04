# CatLog Architecture & File Map (FILE_MAP.md)

**Generated**: 2026-11-04T07:55:00+05:30  
**Target Release**: CatLog V2 (Phases V2-0 through V2-9)  
**Scope**: Codebase directory layout, module map, test registry, and execution instructions.

---

## 1. TOP-LEVEL REPOSITORY LAYOUT

```text
face-clubbing/
├── .github/                     # GitHub Actions CI/CD workflows and issue templates
│   ├── ISSUE_TEMPLATE/          # Bug report and feature request templates with privacy cautions
│   └── workflows/release.yml    # Multi-platform release automation workflow
├── backend/                     # Python backend engine, API, Drive client, and packaging
│   ├── api/                     # FastAPI server, REST routes, job runner, diagnostics, and update check
│   ├── drive/                   # Google Drive API client, recursive BFS crawler, and link parser
│   ├── engine/                  # Core clustering pipeline, face detection, embeddings, snapshots, merger
│   └── version.py               # Single source of truth for version numbering (v0.1.0-rc1)
├── dist/                        # PyInstaller compiled standalone executable outputs (CatLog.exe)
├── dist_release/                # Packaged portable ZIP release archives
├── docs/                        # Specifications, manuals, release checklists, and reputation guides
│   ├── archive/                 # Historical specifications, mockups, and superseded documentation
│   ├── CODE_SIGNING_AND_REPUTATION.md # Windows SmartScreen & code signing guidance
│   ├── OFFLINE_MODEL_PACK.md    # Air-gapped model installation guide
│   └── RELEASE_CHECKLIST.md     # Production release verification protocol
├── eval/                        # Verification, baseline auditing, and benchmark evaluation scripts
├── frontend/                    # React 19 organizer desktop application (Vite + Tailwind CSS)
│   ├── public/                  # Brand logos, icons, mascots (3 themes), and paper textures
│   └── src/                     # React components, API client, hooks, and test suites
├── installer/                   # Windows Inno Setup installer script (`catlog_setup.iss`)
├── scripts/                     # Packaging, Inno compilation, and utility automation scripts
├── tests/                       # Complete Pytest test suite (23 test files, 173 tests)
├── viewer/                      # Static public web viewer (Vite + React + Tailwind CSS)
│   ├── public/                  # Favicons, theme textures, and standalone logs page
│   └── src/                     # Virtualized photo gallery, album tabs, and streaming downloader
├── BUILD_PLAN.md                # Phased development and implementation plan
├── FILE_MAP.md                  # This file: codebase architecture, module map, and execution guide
├── LICENSE                      # MIT Open Source License
├── README.md                    # Project overview, installation instructions, and user manual
├── REPORT.md                    # Historical V1 release candidate audit report
├── SPEC.md                      # Authoritative project specification (Revision 4)
├── STATUS.md                    # Canonical repository state audit and script-checked verification
├── V2_CHANGES.md                # User-visible changes and migration guide for V2
├── V2_DECISIONS.md              # Architectural decisions log and design choices for V2
├── V2_REPORT.md                 # Authoritative V2 development audit report (Phases V2-0 to V2-9)
└── V2_RISKS.md                  # Pre-release risk matrix and unverified items analysis
```

---

## 2. V2 FEATURE MODULE MAP

| V2 Phase | Feature Name | Core Backend Modules | Frontend / Viewer Components |
| :---: | :--- | :--- | :--- |
| **V2-0** | Drive Subfolder Recursion | `backend/drive/client.py`<br>`backend/engine/pipeline.py` | `frontend/src/components/HomeScreen.tsx` |
| **V2-1** | Release Health & Diagnostics | `backend/api/diagnostics.py`<br>`backend/engine/models_downloader.py` | `frontend/src/components/CopyDiagnosticsButton.tsx`<br>`frontend/src/components/ModelDownloadBanner.tsx` |
| **V2-2** | Multi-Source Scan & Provenance | `backend/engine/models.py`<br>`backend/engine/scanner.py`<br>`backend/api/state.py` | `frontend/src/components/HomeScreen.tsx`<br>`frontend/src/components/ReviewPeopleScreen.tsx` |
| **V2-3** | Incremental Source Addition | `backend/engine/snapshots.py`<br>`backend/engine/clusterer.py`<br>`backend/api/routes.py` | `frontend/src/components/AddSourceModal.tsx`<br>`frontend/src/components/WhatChangedModal.tsx` |
| **V2-4** | Two-Project Merger | `backend/engine/merger.py`<br>`backend/api/state.py` | `frontend/src/components/MergeProjectsModal.tsx`<br>`frontend/src/components/OpenProjectModal.tsx` |
| **V2-5** | Multi-Source Viewer & Albums | `backend/engine/exporter.py`<br>`backend/engine/standalone_html.py` | `viewer/src/components/PhotoGallery.tsx`<br>`viewer/src/components/PhotoModal.tsx` |
| **V2-6** | Drive Image Quality Tiers | `backend/drive/client.py`<br>`backend/engine/pipeline.py` | `frontend/src/components/SettingsScreen.tsx`<br>`frontend/src/components/AddSourceModal.tsx` |
| **V2-7** | Input Guidance & Cloud Links | `backend/drive/parser.py`<br>`backend/engine/scanner.py` | `frontend/src/components/InputGuidanceModal.tsx` |
| **V2-8** | Distribution & Update Notice | `backend/version.py`<br>`backend/api/updates.py`<br>`scripts/build_inno_installer.py` | `frontend/src/components/AppUpdateBanner.tsx`<br>`installer/catlog_setup.iss` |
| **V2-9** | Selective Engine Optimization | `backend/engine/detector.py`<br>`backend/engine/thumbnails.py` | N/A (Backend inference optimization) |

---

## 3. TEST SUITES & VERIFICATION REGISTRY

### 3.1 Backend Pytest Suites (`tests/` — 23 Files / 173 Tests)
- `tests/test_api.py`: FastAPI routes, SSE progress streaming, and health checks.
- `tests/test_batch_assign.py`: Multi-face selection, batch person assignment, and undo stack.
- `tests/test_cache.py`: Embedding cache versioning, file-ID stability, and invalidation.
- `tests/test_clustering.py`: Seed + attach-only agglomerative clustering and same-photo guard.
- `tests/test_diagnostics.py`: Regex scrubbing of API keys, Windows/Unix paths, and error codes.
- `tests/test_distribution.py`: Update check API endpoint, semver comparison, and Inno script.
- `tests/test_drive.py`: Google Drive client, BFS recursive traversal, and API key masking.
- `tests/test_edits.py`: `edits.json` replay, face-ID anchor locating, and rename/remove/hide.
- `tests/test_engine_cold_regression.py`: 40-photo fixed subset cold regression and bbox validation.
- `tests/test_exporter.py`: Public bundle isolation, `people.json` export, and hygiene checks.
- `tests/test_incremental.py`: Frozen mode invariants (0 delta), face attachment, and snapshots.
- `tests/test_input_guidance.py`: Cloud URL parsing, Google Photos warning, and nested ZIPs.
- `tests/test_isolation.py`: Output folder auto-nesting and temp folder clean isolation.
- `tests/test_merge_projects.py`: Project merger, settings hash validation, and conflict detection.
- `tests/test_model_download.py`: InsightFace model downloader, HTTP Range resume, and mirrors.
- `tests/test_multi_source.py`: Manifest v2 generation, v1 migration, and cross-source dedupe.
- `tests/test_multi_source_export.py`: Mixed-source viewer export and Drive download synthesis.
- `tests/test_pipeline.py`: Full end-to-end pipeline execution from CLI and API.
- `tests/test_projects.py`: Workspace project management and active project guard.
- `tests/test_quality_tiers.py`: Drive image quality presets (`fast`, `better`, `best`, `original`).
- `tests/test_scanner.py`: Local folder and archive scanner, stable hashing, and duplicate collapse.
- `tests/test_standalone_html.py`: Standalone offline single-file gallery generator (`gallery.html`).
- `tests/test_thumbnails.py`: Composite face quality scoring, aspect-preserving crops, and thumbnails.

### 3.2 Frontend Vitest Suites (`frontend/src/__tests__/` — 24 Files / 136 Tests)
Covers all organizer screens, modals, custom dialogs, update banners, and interaction flows.

### 3.3 Static Viewer Vitest Suites (`viewer/src/__tests__/` — 3 Files / 31 Tests)
Covers theme loading, batch download streaming, select mode, album filtering, and grid virtualization.

### 3.4 Verification & Audit Scripts (`eval/`)
- `eval/check_baseline.py`: Verifies pinned 259-photo baseline fixture bit-for-bit exactness.
- `eval/check_settings_spec.py`: Verifies 15 slider and configuration defaults against SPEC 6.2.
- `eval/check_status_integrity.py`: Verifies STATUS.md duration integrity, counts, and SHA-256 digests.
- `eval/check_ui_rules.py`: Verifies minimum 12px text size and WCAG 2.1 AA accessibility contrast.
- `eval/compare_startups.py`: Measures and compares cold startup latency (onefile vs onedir).
- `eval/measure_drive_quality.py`: Evaluates bandwidth, face yield, and resolution across quality tiers.
- `eval/smoke_test.py`: Verifies standalone executable launch and `/api/health` response.
- `eval/verify_api.py`: Tests API layer endpoints against pinned fixtures and live state.
- `eval/verify_exe.py`: Tests compiled standalone onedir executable against the 259-photo baseline.
- `eval/verify_export.py`: Authoritative 17-point invariant checker for public export bundles.
- `eval/verify_windowed.py`: Verifies windowed launch, subsystem 2 GUI, and clean port release.

---

## 4. EXECUTION GUIDE (COMMAND CHEATSHEET)

### Run Automated Test Suites
```bash
# 1. Full Backend Pytest Suite (173 tests)
.\.venv\Scripts\python.exe -m pytest -q -rs

# 2. V2 Core Feature Suites Only (105 tests)
.\.venv\Scripts\python.exe -m pytest tests/test_drive.py tests/test_diagnostics.py tests/test_multi_source.py tests/test_incremental.py tests/test_merge_projects.py tests/test_multi_source_export.py tests/test_quality_tiers.py tests/test_input_guidance.py tests/test_distribution.py tests/test_model_download.py -q

# 3. Frontend Vitest Suite (136 tests)
cd frontend && npm test -- --run && cd ..

# 4. Static Viewer Vitest Suite (31 tests)
cd viewer && npm test -- --run && cd ..
```

### Run Quality & Integrity Audits
```bash
# 1. STATUS.md Integrity Checker
.\.venv\Scripts\python.exe eval/check_status_integrity.py

# 2. Pinned Baseline Reproduction
.\.venv\Scripts\python.exe eval/check_baseline.py

# 3. Export Bundle Invariants (17 Checks)
.\.venv\Scripts\python.exe eval/verify_export.py

# 4. SPEC 6.2 Settings Default Audit
.\.venv\Scripts\python.exe eval/check_settings_spec.py

# 5. UI Accessibility & Minimum 12px Font Audit
.\.venv\Scripts\python.exe eval/check_ui_rules.py
```

### Build Production Packages
```bash
# 1. Build Web Assets
cd frontend && npm run build && cd ..
cd viewer && npm run build && cd ..

# 2. Package Portable Release ZIP
.\.venv\Scripts\python.exe scripts/package_release.py

# 3. Verify Standalone Executable
.\.venv\Scripts\python.exe eval/verify_exe.py
.\.venv\Scripts\python.exe eval/verify_windowed.py
.\.venv\Scripts\python.exe eval/smoke_test.py
```
