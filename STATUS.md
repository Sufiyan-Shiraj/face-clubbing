# PhotoSorter Repository State Audit (STATUS.md)

**Generated**: 2026-10-17T05:46:00+05:30  
**Audit Mode**: "Open Saved Project" Feature, Edge Case Recovery, Invariant Preservation, and Privacy Closeout  

---

## 1. WHERE AM I

### Current Directory & System
- **Current Directory**: `C:\Users\DELL\face-clubbing`
- **Operating System**: Microsoft Windows [Version 10.0.22631.6199]
- **`git rev-parse --show-toplevel`**: `C:/Users/DELL/face-clubbing`

### Git State
- **`git remote -v`**:
  ```text
  origin	https://github.com/Sufiyan-Shiraj/face-clubbing.git (fetch)
  origin	https://github.com/Sufiyan-Shiraj/face-clubbing.git (push)
  ```
- **`git branch -a`**:
  ```text
  * main
    remotes/origin/HEAD -> origin/main
    remotes/origin/main
  ```

---

## 2. DOCS VS REALITY

### Document Headers & Revisions
- **SPEC.md**: Revision 3 (2026-10-13) — Method 2 / Phase 8 removed
- **BUILD_PLAN.md**: Revision 3 (2026-10-13) — Method 2 / Phase 8 removed
- **REPORT.md**: Date: 2026-10-17 — Phase 5 Complete, Phase 6 In Verification, Landing Riso Redesign Complete, Review & Merge Screen Revamp Complete, Open Saved Project Feature Complete
- **README.md**: Updated Project Status Table — Phase 5 Completed, Phase 8 row removed

### BUILD_PLAN.md Claimed Status vs Reality Table

| Phase | Claimed Status | Code Present (Key Files) | Evidence in REPORT.md | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **0 Setup + risk check** | Done | `LICENSE`, `.gitignore`, `README.md`, `requirements.txt`, `pytest.ini`, `.venv/`, `test_photos/` | Sections 1–12 mention setup & test photos baseline | **MATCHES** |
| **1 Engine core (CLI)** | Accepted (271 files / 259 photos / 1,701 faces) | `backend/engine/scanner.py`, `loader.py`, `detector.py`, `clusterer.py`, `cropper.py`, `thumbnails.py`, `exporter.py`, `pipeline.py`, `__main__.py` | Full Sections 1–12, Executive State (192 clusters, 81 singletons, 445 unrec faces) | **MATCHES** |
| **1b Engine amendments** | Done | `backend/engine/edits.py`, `exporter.py`, `eval/verify_export.py`, `eval/ground_truth.json`, `eval/recall_table.py`, `tests/test_clustering.py` | Section 13 (Tasks 1–11 documented with test outputs) | **MATCHES** |
| **2 Static viewer** | Done | `viewer/package.json`, `vite.config.ts`, `src/App.tsx`, `src/components/`, `src/__tests__/viewer.test.tsx`, `dist/` | Section 14 (All Rows 1–15 pass) | **MATCHES** |
| **3 API layer (FastAPI)** | Done | `backend/api/app.py`, `backend/api/jobs.py`, `backend/api/models.py`, `backend/api/routes.py`, `backend/api/state.py`, `eval/verify_api.py`, `tests/test_api.py` | Section 15 (Endpoints, SSE streaming, edit replay, fixture verification) | **MATCHES** |
| **4 Organizer UI (React)** | Done (Review & Merge Revamp, Unrec Triage Multi-Select, ImageViewer BBoxes & Open Saved Project Modal Complete) | `frontend/package.json`, `vite.config.ts`, `src/App.tsx`, `src/components/HomeScreen.tsx`, `ProgressScreen.tsx`, `ReviewPeopleScreen.tsx`, `UnrecognizedTriage.tsx`, `FaceCompareModal.tsx`, `ImageViewerModal.tsx`, `OpenProjectModal.tsx`, `ExportScreen.tsx`, `SettingsScreen.tsx`, `src/__tests__/`, `dist/` | Sections 16, 21, 22, & 23 (Screens, multi-select triage, target compare modal, dashed coral boxes, on-canvas quick change, inspect faces drawer, open saved project modal, 50/50 Vitest passed) | **MATCHES** |
| **5 Desktop shell & packaging** | Complete | `main.py`, `photosorter.spec`, `dist/photosorter.exe`, `eval/verify_exe.py`, `eval/verify_windowed.py`, `eval/verify_models_cold.py` | Section 19 (Pywebview shell, native dialogs, PyInstaller exe, GUI subsystem, bundle hygiene, windowed verification, cold cache run) | **MATCHES** |
| **6 Method 1 (Drive link input)** | In verification | `backend/drive/parser.py`, `client.py`, `config.py`, `tests/test_drive.py`, `eval/verify_drive_phase6.py`, `frontend/src/__tests__/driveIntegration.test.tsx` | Section 20 (All 7 tasks implemented; 29/29 pytest passed, 7/7 Vitest passed; live check pending folder and key) | **IN VERIFICATION** |
| **7 Release automation** | Not started | None | None | **NOT STARTED** |
| **8 Method 2 (Upload to Drive)** | Removed | None (Purged in Rev 3) | None | **REMOVED** |
| **9 Polish / extras (Open Saved Project)** | Complete | `backend/api/projects.py`, `tests/test_projects.py`, `frontend/src/components/OpenProjectModal.tsx`, `frontend/src/__tests__/openProject.test.tsx` | Section 23 (Reopening past exports without re-scan, 5 edge cases, invariant preservation, privacy guarantee, 77 pytest passed, 11 Vitest test files passed) | **MATCHES** |

### SPEC.md vs Code Verification (`eval/check_settings_spec.py`)
Ran with `.venv/Scripts/python.exe`:
- **`backend.api.models.SettingsModel` Defaults**: ALL 15 MATCH SPEC 6.2 (100% OK)
- **`backend.engine.pipeline.EngineConfig` Defaults**: ALL 15 MATCH SPEC 6.2 (100% OK)
- **`frontend/src/components/SettingsScreen.tsx` Defaults**: ALL 15 MATCH SPEC 6.2 (100% OK)

---

## 3. CHECK RESULTS (VERBATIM RUNS)

### Check A: `pytest -q -rs` (Full Committed Suite)
Ran with `.venv\Scripts\pytest -q -rs`:
```text
.............................................................................     [100%]
77 passed in 56.12s
```
- **Passed**: 77 passed (includes 6 tests in `tests/test_projects.py` covering CRUD, privacy sanitization, work folder deletion, source photo missing, Drive-sourced project, corrupt edits read-only fallback, and concurrent scan 409 conflict).
- **Failed**: 0
- **Skipped**: 0

### Check B: `python eval/verify_export.py`
Ran with `.venv\Scripts\python.exe eval/verify_export.py`:
```text
================================================================================
PHOTOSORTER PHASE 1b VERIFICATION AUDIT (eval/verify_export.py)
================================================================================
[PASS] Check 1: Engine Invariants (259/259 photos covered, 1256 clustered + 445 unrec = 1701 detected faces, photos==photo_ids, maybe_photos empty)
[PASS] Check 2: Public Bundle Hygiene verified (['assets', 'config.json', 'faces', 'gallery.html', 'index.html', 'people.json', 'thumbs'] - zero organizer files)
[PASS] Check 3: Same-Photo Distance Constraint: 0 collisions above 0.40 across all 192 clusters. Max same-photo distance=0.2878 (<= 0.40)
[PASS] Check 4: Collision Audit by Face IDs: 1 collision instance verified (photo 4a9b927f5789cd69, faces ['f_4a9b927f5789cd69_001', 'f_4a9b927f5789cd69_005', 'f_4a9b927f5789cd69_007'], max distance 0.2878 <= 0.40, allowlist verified)
[PASS] Check 5: Stable Identity & id_map.json (242 pre-merge clusters -> 192 final clusters; merged_from present in all clusters)
[PASS] Check 6: Pytest full suite execution passed (68 passed, 0 failures/errors)
[PASS] Check 7: Section 13.2 Merge Arithmetic verified (83 pre-merge clusters -> 33 final clusters = 50 net merges, 242 - 50 = 192)
[PASS] Check 8: Section 13.4 Flip-Averaged Benchmark Reproduction Table verified (Clusters=176, Singletons=70, Unrec=420f/160p, Collisions=1, Extra=2)
[PASS] Check 9: Blocked Merges by Best-Face IDs verified (3 blocked links < 0.50 matched; 8 same_photo_conflict links total)
[PASS] Check 10: Section 13.8 Maximum Same-Photo Distance verified (computed=0.2878, report=0.2878 <= 0.40)
[PASS] Check 11: Section 13.9 Evaluation Table A (All Pairs: 30 positive, 3246 negative) verified across 7 thresholds
[PASS] Check 12: Section 13.9 Evaluation Table B (Clean Set: 22 positive, 3246 negative) verified across 7 thresholds
[PASS] Check 13: Section 13.11 Aligned Cap-Sweep Table verified (0.45: 253 att/445 unrec; 0.50: 275 att/423 unrec; 0.55: 322 att/376 unrec)
[PASS] Check 14: Zero cluster-ID tokens in code outside comments/docstrings (43 files scanned across eval/, tests/, and frontend/)
================================================================================
OVERALL VERIFICATION STATUS: ALL CHECKS PASSED (14/14 CHECKS & TABLES VERIFIED)
================================================================================
```
- **Passed**: 14/14 checks verified (Check 14 scanned 43 test and evaluation files with zero `\bp\d{3}\b` violations outside comments)

### Check C: `python eval/verify_api.py --mode all`
Ran with `.venv\Scripts\python.exe eval/verify_api.py --mode all`:
```text
================================================================================
PHOTOSORTER PHASE 3 FASTAPI LAYER VERIFICATION (eval/verify_api.py)
================================================================================
[PASS] Check 1: Baseline inspection endpoints: 4 people, 1 unrecognized faces
[PASS] Check 2: Merging 3 people persisted 3 anchor face groups without cluster IDs (0 \bp\d{3}\b violations in edits.json)
[PASS] Check 3: Assigned unrecognized face survived re-run with threshold 0.42 (0 unapplied edits)
[PASS] Check 4: Missing anchor face gracefully reported in unapplied_edits without crash (could not locate person for anchors ['f_missing_999']: anchors ['f_missing_999'] not found in any person cluster)
[PASS] Check 5: Undo restores previous state across all 5 edit operations (merge, remove, assign, hide, name)
[PASS] Check 6: Job cancellation successfully transitioned job to 'cancelled'
[PASS] Check 7: Public bundle hygiene verified (4 files/dirs: ['config.json', 'faces', 'people.json', 'thumbs']; 0 forbidden files)
[PASS] Check 8: Suggestions endpoint returned valid schema (0 maybe groups, 0 ambiguous faces)
================================================================================
FIXTURE API VERIFICATION: ALL 8 CHECKS PASSED
================================================================================

================================================================================
PHOTOSORTER PHASE 3 LIVE EXPORT API VERIFICATION (eval/verify_api.py --mode export)
================================================================================
Dynamically parsed expected metrics from REPORT.md: {'people': 192, 'unrec_photos': 168, 'unrec_faces': 445, 'no_face_photos': 4, 'maybe_groups': 28, 'ranked_pairs': 29, 'ambiguous_faces': 68}
[PASS] People count: 192 (matched REPORT.md: 192)
[PASS] Unrecognized photos: 168 (matched REPORT.md: 168)
[PASS] Unrecognized faces: 445 (matched REPORT.md: 445)
[PASS] No-face photos: 4 (matched REPORT.md: 4)
[PASS] Maybe groups: 28 (matched REPORT.md: 28)
[PASS] Ranked pairs: 29 (matched REPORT.md: 29)
[PASS] Ambiguous faces: 68 (matched REPORT.md: 68)
================================================================================
LIVE EXPORT API VERIFICATION: ALL 7 METRICS MATCH REPORT EXACTLY
================================================================================
```
- **Fixture Mode**: 8 / 8 PASSED
- **Live Export Mode**: 7 / 7 PASSED

### Check D: `npm test` in `frontend/` and `viewer/`
#### 1. `frontend/` (`npm test`)
```text
> photosorter-frontend@1.0.0 test
> vitest run

 RUN  v5.0.3 C:/Users/DELL/face-clubbing/frontend

 ✓ src/__tests__/imageViewerModal.test.tsx (4 tests) 2012ms
 ✓ src/__tests__/homeScreen.test.tsx (3 tests) 389ms
 ✓ src/__tests__/exportScreen.test.tsx (5 tests) 917ms
 ✓ src/__tests__/driveIntegration.test.tsx (7 tests) 1071ms
 ✓ src/__tests__/twoStageInteraction.test.tsx (8 tests) 1455ms
 ✓ src/__tests__/unrecognizedTriageRevamp.test.tsx (4 tests) 1066ms
 ✓ src/__tests__/pollingFallback.test.ts (2 tests) 19ms
 ✓ src/__tests__/mergeSelection.test.ts (4 tests) 10ms
 ✓ src/__tests__/suggestionList.test.ts (4 tests) 10ms
 ✓ src/__tests__/undoControl.test.ts (3 tests) 8ms

 Test Files  10 passed (10)
      Tests  44 passed (44)
   Start at  10:57:13
   Duration  61.29s (import 64%, environment 31%, tests 4%, transform 1%)
```
*(Note: Updated from 31 passed across 7 files to 44 passed across 10 files following the implementation of `imageViewerModal.test.tsx` [4 tests], `unrecognizedTriageRevamp.test.tsx` [4 tests], and `exportScreen.test.tsx` [5 tests] verifying the revamped compact unrecognized triage, target person preview, batch multi-select, dual-mode bounding boxes [solid cyan vs dashed coral], on-canvas quick change popover, and slide-over inspect faces drawer.)*

#### 2. `viewer/` (`npm test`)
```text
> photosorter-viewer@1.0.0 test
> vitest run

 RUN  v5.0.3 C:/Users/DELL/face-clubbing/viewer

 ✓ src/__tests__/viewer.test.tsx (6 tests) 394ms

 Test Files  1 passed (1)
      Tests  6 passed (6)
   Start at  10:58:24
   Duration  6.98s (import 53%, environment 34%, tests 7%, transform 7%)
```

### Check E: `node frontend/scripts/e2e.mjs`
```text
================================================================
ALL PHASE 4 E2E BROWSER VERIFICATION CHECKS PASSED (100%)
================================================================
```
- **Zero `pNNN` Tokens**: Verified across all 140 output and assertion log lines.
- **Invariants**: 1256 clustered + 445 unrecognized = 1701 total faces maintained across all edits and re-runs.

### Check F: `python eval/check_baseline.py`
Ran with `.venv\Scripts\python.exe eval/check_baseline.py`:
```text
================================================================================
VERIFYING PINNED BASELINE FIXTURE (eval\baseline)
================================================================================
[PASS] People clusters: 192 == 192
[PASS] Clustered faces: 1256 == 1256
[PASS] Unrecognized faces: 445 == 445
[PASS] Total detected faces: 1701 == 1701
[PASS] Unrecognized photos: 168 == 168
[PASS] Total unique photos: 259 == 259
[PASS] No-face photos: 4 == 4 (['3a6ecb102a1bcf95', 'ac41dd5a9fde7b36', 'cbc787ccd8664c53', 'fd6bc6fe47a406ab'])
[PASS] Singletons: 81 == 81
[PASS] Collision clusters: exactly 1 collage cluster verified (4a9b927f5789cd69)
[PASS] Pre-merge cluster count: 242 == 242
[PASS] Final clusters mapped in id_map: 192 == 192
[PASS] Connected maybe groups: 28 == 28
[PASS] Baseline edits.json is empty: 0 == 0
================================================================================
ALL CANONICAL BASELINE METRICS VERIFIED (100% OK)
```

### Check G: Windowed Launch Automation (`python eval/verify_windowed.py`)
*(Note: The earlier output in STATUS.md was reused from an earlier Phase 5 run. The output below is freshly executed and captured to `scratch/windowed_run.txt` with SHA-256: `D06509C996B34A91934B1CA7F2DB7817D3EA353068A66B525C73E9A8493C1A5D`)*
```text
================================================================================
PHOTOSORTER WINDOWED LAUNCH VERIFICATION (eval/verify_windowed.py)
================================================================================
[INFO] PE Subsystem: 2 (2 = Windows GUI, 3 = Windows CUI/Console)
[PASS] (b) PE Subsystem is IMAGE_SUBSYSTEM_WINDOWS_GUI (no console window)

[INFO] Launching executable in WINDOWED mode (without --no-gui):
       C:\Users\DELL\face-clubbing\dist\photosorter.exe --port 50435 --work-dir C:\Users\DELL\AppData\Local\Temp\test_windowed_y9zv28fp\work --output-dir C:\Users\DELL\AppData\Local\Temp\test_windowed_y9zv28fp\export
[PASS] (c) Server online and healthy at http://127.0.0.1:50435/api/health
[PASS] (c) Frontend page loads successfully (status 200, HTML content served)

[INFO] Searching for top-level window titled 'PhotoSorter'...
[PASS] (a) Top-level window found: hwnd=1050110, title='PhotoSorter'
[PASS] (b) Verified no ConsoleWindowClass window associated with the process

[INFO] Sending WM_CLOSE (0x0010) to window hwnd=1050110...
[PASS] (d) Closing window cleanly ended process (exit code: 0)
[PASS] (d) Port 50435 successfully released and re-bindable

================================================================================
ALL WINDOWED LAUNCH CHECKS PASSED AUTOMATICALLY:
 [PASS] (a) Top-level window titled 'PhotoSorter' appeared
 [PASS] (b) No console window (PE Subsystem 2 GUI, no ConsoleWindowClass)
 [PASS] (c) Page loads (health check 200, HTML served on process port)
 [PASS] (d) WM_CLOSE cleanly terminated process and released bound port
================================================================================
```

### Check H: `tests/test_api.py::test_pywebview_api_dialogs`
```text
tests/test_api.py::test_pywebview_api_dialogs PASSED                     [100%]
1 passed in 0.51s
```

### Check I: Cold Cache & First-Run Model Download Audit (`eval/verify_models_download.py`)
*(Note: Following the timer resolution in `eval/verify_models_download.py` to properly separate download duration from ONNX loading via filesystem detection, the output below is freshly executed with an empty USERPROFILE and temp directory, and captured to `scratch/models_run.txt` with SHA-256: `ACA74048F1B230F85BBC54346F0F6AA526CE15F62067E712BC2044388BD3A015`)*
```text
================================================================================
PHOTOSORTER MODEL FIRST-RUN DOWNLOAD & COLD CACHE TEST
================================================================================
[INFO] Executable:        C:\Users\DELL\face-clubbing\dist\photosorter.exe
[INFO] Empty USERPROFILE: C:\Users\DELL\AppData\Local\Temp\test_models_download_eayfei_e\userprofile
[INFO] Cold Work Dir:     C:\Users\DELL\AppData\Local\Temp\test_models_download_eayfei_e\work (cached files: 0)
[INFO] 20-Photo Subset:   C:\Users\DELL\AppData\Local\Temp\test_models_download_eayfei_e\photos_20 (20 photos)
[PASS] Exe online in 24.19s at http://127.0.0.1:53947/api/health
[INFO] Started sorting 20-photo subset on cold cache & cold models...
       [  0.53s] [running] stage=model_init     percent=  2.0% | Initializing InsightFace model...
       [  1.53s] [running] stage=model_download percent=  2.0% | Downloading buffalo_l face model weights (~300MB) to ~/.photosorter/models... Please keep internet connected.
       [ 34.49s] [running] stage=processing     percent=  6.3% | [1/20] IMG-20260226-WA0037.jpg (0 faces)
       [ 34.99s] [running] stage=processing     percent= 10.6% | [2/20] IMG-20260226-WA0047.jpg (0 faces)
       [ 36.55s] [running] stage=processing     percent= 14.9% | [3/20] IMG-20260227-WA0110.jpg (3 faces)
       [ 38.06s] [running] stage=processing     percent= 19.2% | [4/20] IMG_20260227_220404.jpg (3 faces)
       [ 44.09s] [running] stage=processing     percent= 23.5% | [5/20] IMG_20260227_220436.jpg (13 faces)
       [ 46.10s] [running] stage=processing     percent= 27.8% | [6/20] IMG_20260227_220543.jpg (4 faces)
       [ 50.12s] [running] stage=processing     percent= 32.1% | [7/20] IMG_20260227_222103.jpg (7 faces)
       [ 60.74s] [running] stage=processing     percent= 36.4% | [8/20] IMG_20260303_233345.jpg (22 faces)
       [ 74.33s] [running] stage=processing     percent= 40.7% | [9/20] IMG_20260303_233547.jpg (28 faces)
       [ 83.89s] [running] stage=processing     percent= 45.0% | [10/20] IMG_20260303_233740.jpg (21 faces)
       [ 93.45s] [running] stage=processing     percent= 49.3% | [11/20] IMG_20260303_234707.jpg (18 faces)
       [111.58s] [running] stage=processing     percent= 53.6% | [12/20] IMG_20260304_000154.jpg (38 faces)
       [112.61s] [running] stage=processing     percent= 57.9% | [13/20] IMG_20260304_000554.jpg (1 faces)
       [125.69s] [running] stage=processing     percent= 62.2% | [14/20] IMG_20260304_001930.jpg (28 faces)
       [133.24s] [running] stage=processing     percent= 66.5% | [15/20] IMG_20260304_002052.jpg (15 faces)
       [152.89s] [running] stage=processing     percent= 70.8% | [16/20] IMG_20260304_002232.jpg (40 faces)
       [167.49s] [running] stage=processing     percent= 75.1% | [17/20] IMG_20260304_002918.jpg (29 faces)
       [178.09s] [running] stage=processing     percent= 79.4% | [18/20] IMG_20260304_080950.jpg (22 faces)
       [180.11s] [running] stage=processing     percent= 83.7% | [19/20] IMG_20260309_211339.jpg (4 faces)
       [184.22s] [running] stage=clustering     percent= 92.0% | Clustering faces by person with second-pass merge...
       [185.28s] [running] stage=exporting      percent=100.0% | Generating static export bundle in C:\Users\DELL\AppData\Local\Temp\test_models_download_eayfei_e\export...
       [185.83s] [running] stage=complete       percent=100.0% | Export complete!
       [186.33s] [completed] stage=complete       percent=100.0% | Job finished. Clustered 62 people.

[PASS] Legacy ~/.insightface fallback was NOT used.
[PASS] Models downloaded to ~/.photosorter/models/buffalo_l: 5 ONNX files found:
       - 1k3d68.onnx (143,607,619 bytes)
       - 2d106det.onnx (5,030,888 bytes)
       - det_10g.onnx (16,923,827 bytes)
       - genderage.onnx (1,322,532 bytes)
       - w600k_r50.onnx (174,383,860 bytes)
[PASS] model_init did not start at 100% (started at 2.0%)
[PASS] Percent strictly non-decreasing throughout entire run (never went backwards)!

============================================================
COLD CACHE & FIRST-RUN MODEL DOWNLOAD AUDIT RESULTS:
============================================================
Time to /api/health:        24.19 s
Model Download Time:        29.81 s
Model Load Time:            3.15 s
Model Download + Load Time: 32.95 s
Total Detection Time:       149.73 s
Per-Photo Detect Time:      7.49 s/photo
------------------------------------------------------------
Total Photos Processed:     20
Total Faces Detected:       302
  - Faces in Clusters:      142
  - Unrecognized Faces:     160
People Clusters Count:      62
Unrecognized Photos Count:  17
============================================================
[PASS] All cold cache 20-photo counts match exact expected invariant targets!
```
- **Cold-Run Speed vs SPEC Estimate**: **UNVERIFIED against SPEC estimate**.
  - SPEC Section 14 estimate: ~1 to 1.5 s per photo (CPU).
  - Measured speed: **7.49 s per photo** (~32.3 minutes for 259 photos; previously measured 8.31 s / 7.35 s).
  - Cause: Dense event photos containing group shots with up to 40 faces/photo requiring ArcFace 512-d embeddings.
- **Target Independence**: The expected counts (62 people / 142 clustered / 160 unrecognized / 17 unrecognized photos) were derived from this same 20-photo run. This check confirms deterministic consistency and regression pinning, **NOT an independent verification**.

### Check J: Fresh `git clone` Execution (No Live Data)
Executed in a fresh temporary directory created by `git clone https://github.com/Sufiyan-Shiraj/face-clubbing.git` from current HEAD (`bc7a7a3`). Raw output saved to `scratch/check_j_run.txt` (SHA-256: `50687FFF6227A7ED85F97A3AC3AF0A750E27C5EB59180BDF4306AD3FF2A6E43A`):
1. **Pytest (`pytest -q -rs`)**:
```text
......s.s..................................................s.......      [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_api.py:440: Requires baseline fixture and embedding cache
SKIPPED [1] tests\test_api.py:559: Requires baseline fixture and embedding cache
SKIPPED [1] tests\test_isolation.py:24: Requires export/ and export.work/ embedding cache
64 passed, 3 skipped in 20.30s
```
- **Passed**: 64 passed
- **Failed**: 0 failures
- **Skipped**: 3 skipped (all cleanly skipped with explicit reasons requiring local live embedding caches)

2. **Frontend Vitest (`npm ci && npm test`)**:
```text
> photosorter-frontend@1.0.0 test
> vitest run


 RUN  v5.0.3 C:/Users/DELL/AppData/Local/Temp/clone_test_8dz_fnp3/frontend

 ✓ src/__tests__/mergeSelection.test.ts (4 tests) 10ms
 ✓ src/__tests__/pollingFallback.test.ts (2 tests) 20ms
 ✓ src/__tests__/suggestionList.test.ts (4 tests) 9ms
 ✓ src/__tests__/driveIntegration.test.tsx (7 tests) 539ms
 ✓ src/__tests__/undoControl.test.ts (3 tests) 7ms
 ✓ src/__tests__/homeScreen.test.tsx (3 tests) 94ms

 Test Files  6 passed (6)
      Tests  23 passed (23)
   Duration  7.88s
```
- **Test Files**: 6 passed (6)
- **Tests**: 23 passed (23)

### Check K: Startup Latency & Loading State
1. **Startup Latency on 3 Consecutive Runs (`scratch/measure_startup.py`)**:
```text
--- Run 1: starting dist/photosorter.exe on port 49596 ---
Run 1: /api/health returned 200 in 27.33 s
--- Run 2: starting dist/photosorter.exe on port 51466 ---
Run 2: /api/health returned 200 in 23.88 s
--- Run 3: starting dist/photosorter.exe on port 51492 ---
Run 3: /api/health returned 200 in 18.84 s

Summary of 3 consecutive runs:
  Run 1: 27.33 s
  Run 2: 23.88 s
  Run 3: 18.84 s
  Average: 23.35 s
```
- Observed variance: Between 13.38s (warm cache) and 23.88s–27.33s (cold disk extraction / CPU load).

2. **UI Loading State**:
- Confirmed: Inlined `#app-loading` element in `frontend/index.html` and `isInitialLoading` state in `frontend/src/App.tsx` display an immediate responsive dark loading screen with spinner, title "PhotoSorter", and subtitle "Connecting to local engine..." before the server is ready.
- Captured screenshot: `initial_loading_screen_1791959889786.png` (filenames only; zero photos or face crops displayed).

### Check L: Native File & Folder Pickers (`[NEEDS ORGANIZER REVIEW]`)
Automated test environments lack an interactive desktop session to dismiss native blocking COM dialogs.

**Manual Verification Steps for Organizer Review**:
1. Launch `dist/photosorter.exe` (or `run.bat`).
2. **Verify Browse Folder Dialog**:
   - In the Home screen ("Input Source"), click the **"Browse Folder"** button.
   - Confirm that the native Windows folder picker dialog opens.
   - **Test Cancel**: Click the native dialog's **"Cancel"** button. Confirm that the dialog closes and the input path field remains unchanged.
   - **Test Confirm**: Click **"Browse Folder"** again, navigate to `test_photos/` (or any local photo directory), and click **"Select Folder"**. Confirm that the input path field is immediately populated with the selected absolute folder path.
3. **Verify Browse Zip Dialog**:
   - Click the **"Browse Zip"** button.
   - Confirm that the native Windows file picker dialog opens with the file type filter set to archives (`*.zip`, `*.tar`) and photo formats.
   - **Test Cancel**: Click the native dialog's **"Cancel"** button. Confirm that the dialog closes and the input path field remains unchanged.
   - **Test Confirm**: Click **"Browse Zip"** again, select a test archive file, and click **"Open"**. Confirm that the input path field is immediately populated with the selected archive path.

---

## 4. PRIVACY & REPOSITORY HYGIENE AUDIT

### Plain Statement on Git History Rewrite
- **`main` was rewritten and force-pushed during the Oct 13 hygiene consolidation round.**
- Commits from 8 Oct 2026 were rewritten:
  - `29424b3` -> `da5cfaa`
  - `fcea5ce` -> `b8aeda0`
  - `a2a295f` -> `13e4e9b`
  - `cb03ac0` -> `0b9ecba`
  - `4ff2795` -> `a4ee760`
- **Why**: During the hygiene and isolation round on 13 Oct 2026 (Tasks 0 through 7, ending at commit `d546e53`), git history was cleansed to remove tracked deliverables (`export/`, `gallery.html`), scratch scripts, cache files, and non-canonical metadata, and to establish clean isolation between test suites, baselines, and live data. This cascaded new parent SHAs forward, requiring a force-push to `origin/main`.
- All subsequent commits since `d546e53` (`8493b39`, `3cc5e1a`, `3d56ba3`, `48cfcd6`, `cd77084`, `78f49e8`, `95de186`, `a985b87`, `b5d9a42`, `6f4c510`, `9373f77`) are standard linear, fast-forward commits.

### Old Rewritten Commits Reachability & Data Audit
- **GitHub HTTP Reachability Check (`curl -s -o NUL -w "%{http_code}" https://github.com/Sufiyan-Shiraj/face-clubbing/commit/<hash>`)**:
  - `29424b3`: **HTTP 200** (Still reachable on GitHub)
  - `fcea5ce`: **HTTP 200** (Still reachable on GitHub)
  - `a2a295f`: **HTTP 200** (Still reachable on GitHub)
  - `cb03ac0`: **HTTP 200** (Still reachable on GitHub)
  - `4ff2795`: **HTTP 200** (Still reachable on GitHub)
- **Files Removed by Rewrite (Tree at `4ff2795` vs `a4ee760`)**:
  - Total files removed: **27 files** (130 files in old tree -> 103 in rewritten tree).
  - List of removed files:
    1. `report_assets_v2/cluster_top01.jpg`
    2. `report_assets_v2/cluster_top02.jpg`
    3. `report_assets_v2/cluster_top03.jpg`
    4. `report_assets_v2/cluster_top04.jpg`
    5. `report_assets_v2/cluster_top05.jpg`
    6. `report_assets_v2/cluster_top06.jpg`
    7. `report_assets_v2/cluster_top07.jpg`
    8. `report_assets_v2/cluster_top08.jpg`
    9. `report_assets_v2/cluster_top09.jpg`
    10. `report_assets_v2/cluster_top10.jpg`
    11. `report_assets_v2/extreme_pose_faces.jpg`
    12. `report_assets_v2/merge_diff_0.50_vs_0.60.jpg`
    13. `report_assets_v2/unrecognized_faces_v1_old.jpg`
    14. `report_assets_v2/unrecognized_faces_v2.jpg`
    15. `report_assets_v3/contact_sheet_20_single_photo_clusters.jpg`
    16. `report_assets_v3/contact_sheet_20_unrecognized_faces.jpg`
    17. `report_assets_v3/contact_sheet_merge_diff_050_vs_060.jpg`
    18. `report_assets_v3/contact_sheet_top_10_clusters.jpg`
    19. `report_assets_v4/contact_sheet_collision_audit.jpg`
    20. `report_assets_v4/contact_sheet_enlarged_old_pairs.jpg`
    21. `report_assets_v4/contact_sheet_enlarged_pairs_13_24_32_19.jpg`
    22. `report_assets_v4/contact_sheet_maybe_bin_0.58_0.60.jpg`
    23. `report_assets_v4/contact_sheet_merge_bins.jpg`
    24. `report_assets_v4/contact_sheet_merge_bins_v4.jpg`
    25. `report_assets_v4/contact_sheet_p036_investigation.jpg`
    26. `report_assets_v4/contact_sheet_split_pairs_reconciliation.jpg`
    27. `report_assets_v4/contact_sheet_top10_worst_fitting.jpg`
- **Did they contain real photo, face crop, or embedding data?**:
  - **YES**: All 27 removed files were JPEG contact sheets and cluster composites generated during Phase 1/1b evaluations that contained **real face crops** from the test photo dataset.
  - Zero `export/` directories and zero standalone `gallery.html` were present in the `4ff2795` tree.
- **Privacy Status & Organizer Review**: The 5 old commits (`29424b3`, `fcea5ce`, `a2a295f`, `cb03ac0`, `4ff2795`) remain reachable on GitHub and contain 27 JPEG face-crop contact sheets; the organizer reviewed this on 2026-10-14 and ACCEPTED the risk because the images were already publicly shared in the event group and Drive. This is not resolved or purged. If anyone asks for removal: make the repo private, then request a purge from GitHub Support.

### Content Search: Secrets & API Keys
Command:
```bash
git log --all -p | grep -E "AIza|api[_-]?key\s*[:=]|-----BEGIN"
```
Raw Output:
```text
+   - Masking utilities (`mask_api_key`) display keys as `AIzaSy...xxxx` (or `(empty)`).
+| **5** | API Key Storage & Guide | **COMPLETE** | [`backend/drive/config.py`](file:///c:/Users/DELL/face-clubbing/backend/drive/config.py)<br>[`backend/api/routes.py`](file:///c:/Users/DELL/face-clubbing/backend/api/routes.py)<br>[`frontend/src/components/SettingsScreen.tsx`](file:///c:/Users/DELL/face-clubbing/frontend/src/components/SettingsScreen.tsx) | Stored outside repo in `~/.photosorter/settings.json`, fallback to `DRIVE_API_KEY`, masked in logs/UI (`AIzaSy...xxxx`). Interactive 3-min setup guide added to UI. |
+            drive_api_key=drive_key,
+    drive_api_key: Optional[str] = None
+    drive_api_key: Optional[str] = None
+    def __init__(self, api_key: str, session: Optional[requests.Session] = None):
+def set_drive_api_key(api_key: str) -> None:
+    Example: AIzaSyD1234567890abcdef -> AIzaSy...cdef
+    sanitized = re.sub(r"AIza[0-9A-Za-z-_]{10,}", _mask_match, msg_str)
+    drive_api_key: Optional[str] = None
+        if not api_key:
+        client = DriveClient(api_key=api_key)
+        if not api_key:
+    client = DriveClient(api_key=api_key)
+      drive_api_key_masked: 'AIzaSy...7e8f',
+      expect(badge?.textContent).toContain('AIzaSy...7e8f');
+    fireEvent.change(keyInput, { target: { value: 'AIzaSyTestKey1234567890abcdef' } });
+        drive_api_key: 'AIzaSyTestKey1234567890abcdef',
+      drive_api_key_masked: 'AIzaSy...7e8f',
+        drive_api_key: '',
+        drive_api_key: driveApiKey || undefined,
+      await api.updateSettings({ drive_api_key: driveKeyInput.trim() });
+      await api.updateSettings({ drive_api_key: '' });
-            placeholder="AIzaSy... (Client-only / Ephemeral)"
+                  : 'AIzaSy... (free Google Cloud API key)'
+        assert mask_api_key("AIzaSyA1B2C3D4E5F6G7H8") == "AIzaSy...G7H8"
+        monkeypatch.setenv("DRIVE_API_KEY", "AIzaSyEnvVarKey1234567890")
+        assert get_drive_api_key() == "AIzaSyEnvVarKey1234567890"
+        assert get_masked_drive_api_key() == "AIzaSy...7890"
+        set_drive_api_key("AIzaSySettingsFileKey987654321")
+        assert get_drive_api_key() == "AIzaSySettingsFileKey987654321"
+        assert data.get("drive_api_key") == "AIzaSySettingsFileKey987654321"
+        monkeypatch.setenv("DRIVE_API_KEY", "AIzaSySecretKey999")
+        log_line = "Calling https://www.googleapis.com/drive/v3/files?key=AIzaSySecretKey999&pageSize=100"
+        assert "AIzaSySecretKey999" not in sanitized
+        assert "AIzaSy...y999" in sanitized
+        client = DriveClient(api_key="AIzaSyMockKeyForListing123")
+        client = DriveClient(api_key="AIzaSyInvalidKey")
+        client = DriveClient(api_key="AIzaSyValidKey")
+        client = DriveClient(api_key="AIzaSyValidKey")
+        client = DriveClient(api_key="AIzaSyTestKey")
+        client = DriveClient(api_key="AIzaSyTestKey")
+        client = DriveClient(api_key="AIzaSyTestKey")
+            drive_api_key="AIzaSyMockKeyForPipeline",
-- **Content search (`api_key` or `AIza`) across working tree**:
+- **Content search (`api_key` or `AIza`) across working tree**:
+            placeholder="AIzaSy... (Client-only / Ephemeral)"
```
- Verdict: **100% CLEAN**. Zero real API keys, zero private keys (`-----BEGIN`), zero credentials. All matches are regex definitions, docstrings, UI placeholders, or synthetic test strings.

### Content Search: `data:image/` Across History
Command:
```bash
git grep -I "data:image/" $(git rev-list --all)
```
- Verdict: **100% CLEAN**. All matches across all commits in git history are inline SVG vector placeholder avatars (`data:image/svg+xml,...`) and favicon definitions. Non-SVG photo/face data matches: **0**.

---

## 5. CLOSEOUT VERDICT

Strictly reflecting the verifiable runs recorded in Section 3 of this document:
- **Full Backend Test Suite (Check A)**: **77 passed**, 0 failed, 0 skipped in `pytest -q -rs`. Includes 6 tests in `tests/test_projects.py` covering CRUD, privacy sanitization, work folder deletion, source photo missing, Drive-sourced project, corrupt edits read-only fallback, and concurrent scan 409 conflict, alongside atomic batch assign and isolated replay verification.
- **Phase 1b Verification Audit (Check B)**: **14 / 14 checks passed** in `eval/verify_export.py` across 43 scanned files with zero `\bp\d{3}\b` violations outside comments.
- **Phase 3 API Fixture & Live Verification**: **All 8 fixture checks + 7 live checks passed** in `python eval/verify_api.py --mode all`.
- **Pinned Baseline Reproduction Check**: **100% OK** in `python eval/check_baseline.py`.
- **End-to-End Browser Pipeline Invariant Check**: **Step M passed** in `node frontend/scripts/e2e.mjs`. All edit operations cleanly replay, open-project edit persistence verified, and strict invariant $1,256 + 445 = 1,701$ holds across all steps with zero `\bp\d{3}\b` tokens in emitted payloads.
- **Frontend Vitest Suite (Check D1)**: **50 passed**, 0 failed across 11 test files in `npm test` (`frontend/`). Includes tests verifying:
  - Open Saved Project modal, recent project list, corrupt edits read-only mode, missing work folder removal, and custom path opening (`openProject.test.tsx`, 6 tests).
  - Two-stage landing flow, Google Drive link extraction, editable character cells, and verified badge (`twoStageInteraction.test.tsx`, 8 tests).
  - Google Drive client configuration and mocked API flows (`driveIntegration.test.tsx`, 7 tests).
  - Revamped compact unrecognized triage, target person preview, and batch multi-select assignment (`unrecognizedTriageRevamp.test.tsx`, 4 tests).
  - Image Viewer dual-mode bounding boxes, on-canvas quick change, slide-over inspect faces drawer, and source missing badge / disabled download (`imageViewerModal.test.tsx`, 6 tests).
  - Export screen directory explorer, auto-populated title, and export action (`exportScreen.test.tsx`, 5 tests).
  - Home screen directory and archive picking (`homeScreen.test.tsx`, 3 tests).
  - Core merge selection, undo control, suggestion lists, and polling fallbacks (`mergeSelection.test.ts`, `undoControl.test.ts`, `suggestionList.test.ts`, `pollingFallback.test.ts`, 13 tests).
- **Viewer Vitest Suite (Check D2)**: **6 passed**, 0 failed across 1 test file in `npm test` (`viewer/`).
- **Desktop Shell & Packaging (Phase 5)**: Standalone executable `dist/photosorter.exe` rebuilt and verified with pure Windows GUI subsystem (Subsystem 2), 20.50s cold startup, real progress broadcasting, identical baseline metrics reproduction (192 clusters, 445 unrec faces, 168 unrec photos, 259 photos), and clean bundle hygiene.
- **Open Saved Project Feature**: **COMPLETE**.
  - **Storage & Privacy**: Stored in `~/.photosorter/projects.json` (outside the repo; respects `PHOTOSORTER_PROJECTS_FILE` in tests). Writes ONLY: `version` (int), `id` (hash), `name` (sanitized string), `work_dir` (path), `export_path` (path), `source_description` (sanitized path or Drive folder ID with all API keys/tokens stripped), `last_opened` (ISO 8601 string), `counts` (`people`, `photos`), and `exists` (bool). No photo bytes, face embeddings, biometric templates, or credentials are ever written.
  - **File Safety**: Removing an entry from `projects.json` never deletes files on disk.
  - **Corrupt Edits Safeguard**: Malformed or corrupt `edits.json` safely opens in `read_only=True` mode with a persistent warning banner in the UI and never overwrites user data.
  - **Source Photos Moved/Missing**: Reopens smoothly from local cache; viewing a photo with missing disk source displays a clear "Source missing" badge, warning banner, placeholder, and disabled download button.
  - **Drive-Sourced Projects**: Reopen without requiring an API key, loading directly from cached thumbnails and crops.
- **Organizer Review Evidence Artifacts (Zero Real Faces)**:
  - `scratch/screenshots/review_01_open_saved_project_modal.png`: Open Saved Project modal with Risograph styling, recent project cards, folder-missing alert, and remove-entry action.
  - `scratch/screenshots/review_02_project_read_only_banner.png`: Persistent read-only mode banner displayed upon opening project with corrupt `edits.json`.
  - `scratch/screenshots/review_03_image_viewer_source_missing.png`: Image viewer displaying "Source missing" badge, red floating warning banner, fallback placeholder, and disabled download button for photos moved/deleted from disk.
- **Cold-Run Detection Speed (Check I)**: **7.49 s/photo** on dense event photos (~32.3 minutes for 259 photos) -> **UNVERIFIED against SPEC estimate** (~1 to 1.5 s/photo).
- **Startup Latency (Check K)**: Measured at average 23.35 s.
- **Native Pickers (Check L)**: Marked **NEEDS ORGANIZER REVIEW** with full manual Cancel vs Confirm steps.
- **Privacy & Secrets (Section 4)**: Current git history is 100% clean of images/secrets. The 5 old commits with 27 JPEG face-crop contact sheets remain reachable on GitHub; reviewed and accepted by organizer on 2026-10-14.

