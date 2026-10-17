# PhotoSorter Repository State Audit (STATUS.md)

**Generated**: 2026-10-17T07:37:00+05:30  
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
- **`git status -sb`**:
  ```text
  ## main
  ```
- **`git log --oneline -8`**:
  ```text
  6e2b2ce docs: audit and sync STATUS.md, REPORT.md, BUILD_PLAN.md, and test suites with verified scratch outputs and dynamic exists
  c96b227 fix(ui): mount OpenProjectModal via body portal with topmost z-index and explicit click handlers
  d102b4e feat(projects): open saved project with edge case recovery and invariant preservation
  6e95082 feat(ui): complete review merge screen revamp, unrecognized triage multi-select, and image viewer face boxes
  afcaf08 fix(ui): lock header and left navbar in fixed layout with internal main view scrolling
  03fbdb5 fix(dialog): ensure native Windows folder picker opens in foreground via Base64 PowerShell TopMost dialog
  8e00843 feat(ui): revamp export explorer, scan progress timer, and elevate global typography
  3279e52 settings revamp half
  ```

---

## 2. DOCS VS REALITY

### Document Headers & Revisions
- **SPEC.md**: Revision 3 (2026-10-13) — Method 2 / Phase 8 removed; Section 18.1 added documenting Phase 6 live Drive thumbnail floor sweeps
- **BUILD_PLAN.md**: Revision 3 (2026-10-13) — Method 2 / Phase 8 removed; Phase 6 Complete; Phase 6b UI redesign Complete (pending organizer review); Open saved project (feature) Complete; Phases 7 & 9 Not started
- **REPORT.md**: Date: 2026-10-17 — Phase 5 Complete, Phase 6 Complete (live verification on public Drive folder fully verified, evidence recorded, 64px floor documented in SPEC §18), Landing Riso Redesign Complete, Review & Merge Screen Revamp Complete, Open Saved Project Feature Complete
- **README.md**: Updated Project Status Table — Phase 5 Completed, Phase 6 Completed, Phase 6b Complete (pending organizer review), Phase 7 & 9 Not started, Open saved project (feature) Complete

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
| **6 Method 1 (Drive link input)** | Complete | `backend/drive/parser.py`, `client.py`, `config.py`, `tests/test_drive.py`, `eval/verify_drive_phase6.py`, `frontend/src/__tests__/driveIntegration.test.tsx` | Section 20 (All 7 tasks implemented; 29/29 pytest passed, 7/7 Vitest passed; live verification on 83 photos completed with 100% thumbnails, 92.1% bandwidth saved, 64px floor documented in SPEC §18) | **MATCHES** |
| **6b UI redesign** | Complete (pending organizer review) | `frontend/src/components/`, `frontend/src/index.css`, `frontend/src/__tests__/` | Sections 21 & 22 (Risograph theme, 2-stage landing flow, compact triage, bboxes) | **COMPLETE (PENDING REVIEW)** |
| **7 Release automation** | Not started | None | None | **NOT STARTED** |
| **8 Method 2 (Upload to Drive)** | Removed | None (Purged in Rev 3) | None | **REMOVED** |
| **9 Polish / extras** | Not started | None | None | **NOT STARTED** |
| **Open saved project (feature)** | Complete | `backend/api/projects.py`, `tests/test_projects.py`, `frontend/src/components/OpenProjectModal.tsx`, `frontend/src/__tests__/openProject.test.tsx` | Section 23 (Reopening past exports without re-scan, 5 edge cases, invariant preservation, privacy guarantee, 77 pytest passed, 11 Vitest test files passed) | **COMPLETE** |

### SPEC.md vs Code Verification (`eval/check_settings_spec.py`)
Ran with `.venv/Scripts/python.exe`:
- **`backend.api.models.SettingsModel` Defaults**: ALL 15 MATCH SPEC 6.2 (100% OK)
- **`backend.engine.pipeline.EngineConfig` Defaults**: ALL 15 MATCH SPEC 6.2 (100% OK)
- **`frontend/src/components/SettingsScreen.tsx` Defaults**: ALL 15 MATCH SPEC 6.2 (100% OK)

---

## 3. CHECK RESULTS (VERBATIM RUNS FROM SAVED RAW FILES)

### Check A: `pytest -q -rs` (Full Committed Suite)
- **Source File**: `scratch/pytest_run.txt`
- **SHA-256 Digest**: `424674820304B7AD27B9758DF97E6479D990D139E3981C21FD3A539CE3A4B85D`
- **PowerShell `Get-FileHash` Verification**:
```text
Algorithm : SHA256
Hash      : 424674820304B7AD27B9758DF97E6479D990D139E3981C21FD3A539CE3A4B85D
Path      : C:\Users\DELL\face-clubbing\scratch\pytest_run.txt
```
- **Verbatim Output**:
```text
........................................................................ [ 93%]
.....                                                                    [100%]
77 passed in 59.27s
```
- **Summary**: 77 passed in 59.27s (0 failed, 0 skipped).

---

### Check B: `python eval/verify_export.py` (Phase 1b Verification Audit)
- **Source File**: `scratch/verify_export.txt`
- **SHA-256 Digest**: `40B3E223005D3AE67E3DBE2A625ACA96D63893F0E7FD1A84E59CC6D9B7306317`
- **PowerShell `Get-FileHash` Verification**:
```text
Algorithm : SHA256
Hash      : 40B3E223005D3AE67E3DBE2A625ACA96D63893F0E7FD1A84E59CC6D9B7306317
Path      : C:\Users\DELL\face-clubbing\scratch\verify_export.txt
```
- **Verbatim Output**:
```text
================================================================================
PHOTOSORTER PHASE 1b VERIFICATION AUDIT (eval/verify_export.py)
================================================================================
[PASS] Check 1: Engine Invariants (259/259 photos covered, 1256 clustered + 445 unrec = 1701 detected faces, photos==photo_ids, maybe_photos empty)
[PASS] Check 2: Public Bundle Hygiene verified (['assets', 'config.json', 'faces', 'gallery.html', 'index.html', 'people.json', 'thumbs'] - zero organizer files)
[PASS] Check 3: Same-Photo Distance Constraint: 0 collisions above 0.40 across all 192 clusters. Max same-photo distance=0.2878 (<= 0.40)
[PASS] Check 4: Collision Audit by Face IDs: 1 collision instance verified (photo 4a9b927f5789cd69, faces ['f_4a9b927f5789cd69_001', 'f_4a9b927f5789cd69_005', 'f_4a9b927f5789cd69_007'], max distance 0.2878 <= 0.40, allowlist verified)
[PASS] Check 5: Stable Identity & id_map.json (242 pre-merge clusters -> 192 final clusters; merged_from present in all clusters)
[PASS] Check 6: Pytest full suite execution passed (77 passed, 0 failures/errors)
[PASS] Check 7: Section 13.2 Merge Arithmetic verified (83 pre-merge clusters -> 33 final clusters = 50 net merges, 242 - 50 = 192)
[PASS] Check 8: Section 13.4 Flip-Averaged Benchmark Reproduction Table verified (Clusters=176, Singletons=70, Unrec=420f/160p, Collisions=1, Extra=2)
[PASS] Check 9: Blocked Merges by Best-Face IDs verified (3 blocked links < 0.50 matched; 8 same_photo_conflict links total)
[PASS] Check 10: Section 13.8 Maximum Same-Photo Distance verified (computed=0.2878, report=0.2878 <= 0.40)
[PASS] Check 11: Section 13.9 Evaluation Table A (All Pairs: 30 positive, 3246 negative) verified across 7 thresholds
[PASS] Check 12: Section 13.9 Evaluation Table B (Clean Set: 22 positive, 3246 negative) verified across 7 thresholds
[PASS] Check 13: Section 13.11 Aligned Cap-Sweep Table verified (0.45: 253 att/445 unrec; 0.50: 275 att/423 unrec; 0.55: 322 att/376 unrec)
[PASS] Check 14: Zero cluster-ID tokens in code outside comments/docstrings (46 files scanned across eval/, tests/, and frontend/)
================================================================================
OVERALL VERIFICATION STATUS: ALL CHECKS PASSED (14/14 CHECKS & TABLES VERIFIED)
================================================================================
```
- **Summary**: 14/14 checks passed (Check 6: 77 passed, 0 failures/errors; Check 14: 46 files scanned with zero `\bp\d{3}\b` violations outside comments).

---

### Check C: `python eval/verify_api.py --mode all` (Phase 3 FastAPI Layer Verification)
- **Source File**: `scratch/verify_api.txt`
- **SHA-256 Digest**: `A978286B52D9684E884874DEE07DFA314E8EBD7D1AE80DB769FC294A1157C07C`
- **PowerShell `Get-FileHash` Verification**:
```text
Algorithm : SHA256
Hash      : A978286B52D9684E884874DEE07DFA314E8EBD7D1AE80DB769FC294A1157C07C
Path      : C:\Users\DELL\face-clubbing\scratch\verify_api.txt
```
- **Verbatim Output**:
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
[PASS] Check 4a: Baseline invariant holds: 1256 clustered + 445 unrecognized = 1701 total faces
[PASS] Check 4b: Batch assign (2 face_ids) and undo verified; invariant 1256 + 445 = 1701 holds, zero pNNN in edits.json
[PASS] Check 4c: Detach known face to unknown and undo verified; invariant 1256 + 445 = 1701 holds, zero pNNN in edits.json
[PASS] Check 4d: Create new person from selected faces and undo verified (192 -> 193 -> 192); invariant holds, zero pNNN in edits.json
[PASS] Check 4e: Failed edits handled gracefully (HTTP 400 for bad op, unapplied for ghost face); state preserved and invariant 1256 + 445 = 1701 holds
================================================================================
LIVE EXPORT API VERIFICATION: ALL 7 METRICS MATCH REPORT EXACTLY
================================================================================
```
- **Summary**: 8/8 Fixture Checks Passed; 7/7 Live Export Metrics Matched Report Exactly.

---

### Check D1: `npm test` in `frontend/` (Frontend Vitest Suite)
- **Source File**: `scratch/vitest_frontend.txt`
- **SHA-256 Digest**: `5B0D1480EB1F7DCDCD07B6C8A352A3D69A929A1075F7989D73235889F7B67516`
- **PowerShell `Get-FileHash` Verification**:
```text
Algorithm : SHA256
Hash      : 5B0D1480EB1F7DCDCD07B6C8A352A3D69A929A1075F7989D73235889F7B67516
Path      : C:\Users\DELL\face-clubbing\scratch\vitest_frontend.txt
```
- **Verbatim Output**:
```text
> photosorter-frontend@1.0.0 test
> vitest run --run


[1m[30m[46m RUN [49m[39m[22m [36mv5.0.3 [39m[90mC:/Users/DELL/face-clubbing/frontend[39m

 [32m✓[39m src/__tests__/driveIntegration.test.tsx [2m([22m[2m7 tests[22m[2m)[22m[33m 822[2mms[22m[39m
 [32m✓[39m src/__tests__/twoStageInteraction.test.tsx [2m([22m[2m8 tests[22m[2m)[22m[33m 1101[2mms[22m[39m
   [32m✓[39m Organizer Two-Stage Interaction & Drive Folder ID Extraction [2m(8)[22m
     [33m[2m✓[22m[39m renders Initial State with no face preview frames visible[33m 542[2mms[22m[39m
 [32m✓[39m src/__tests__/imageViewerModal.test.tsx [2m([22m[2m4 tests[22m[2m)[22m[33m 1447[2mms[22m[39m
   [32m✓[39m ImageViewerModal - Unknown Face Boxes & Person Changing [2m(4)[22m
     [33m[2m✓[22m[39m renders bounding boxes for BOTH known and unknown faces[33m 334[2mms[22m[39m
     [33m[2m✓[22m[39m allows changing an unknown face to an existing person directly from Inspect Faces drawer[33m 710[2mms[22m[39m
 [32m✓[39m src/__tests__/unrecognizedTriageRevamp.test.tsx [2m([22m[2m4 tests[22m[2m)[22m[33m 683[2mms[22m[39m
 [32m✓[39m src/__tests__/openProject.test.tsx [2m([22m[2m6 tests[22m[2m)[22m[33m 916[2mms[22m[39m
   [32m✓[39m Open Saved Project Feature [2m(6)[22m
     [33m[2m✓[22m[39m renders recent projects list with name, source, and counts[33m 386[2mms[22m[39m
 [32m✓[39m src/__tests__/exportScreen.test.tsx [2m([22m[2m5 tests[22m[2m)[22m[33m 675[2mms[22m[39m
   [32m✓[39m ExportScreen Component [2m(4)[22m
     [33m[2m✓[22m[39m renders file explorer window with breadcrumbs and directory items[33m 330[2mms[22m[39m
 [32m✓[39m src/__tests__/mergeSelection.test.ts [2m([22m[2m4 tests[22m[2m)[22m[32m 11[2mms[22m[39m
 [32m✓[39m src/__tests__/pollingFallback.test.ts [2m([22m[2m2 tests[22m[2m)[22m[32m 23[2mms[22m[39m
 [32m✓[39m src/__tests__/undoControl.test.ts [2m([22m[2m3 tests[22m[2m)[22m[32m 12[2mms[22m[39m
 [32m✓[39m src/__tests__/suggestionList.test.ts [2m([22m[2m4 tests[22m[2m)[22m[32m 12[2mms[22m[39m
 [32m✓[39m src/__tests__/homeScreen.test.tsx [2m([22m[2m3 tests[22m[2m)[22m[32m 126[2mms[22m[39m

[2m Test Files [22m [1m[32m11 passed[39m[22m[90m (11)[39m
[2m      Tests [22m [1m[32m50 passed[39m[22m[90m (50)[39m
[2m   Start at [22m 07:20:14
[2m   Duration [22m 35.52s[2m (environment 65%, import 27%, tests 6%, transform 2%)[22m

[2m    Isolate [22m [33m11 workers spawned[39m[2m · ~6.35s startup each (spawn + environment, per file)[22m
[2m            [22m [2mat least ~16.95s faster with [22m[33misolate: false[39m[2m — reuses workers across files instead of one per file[22m

Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
[90mstderr[2m | src/__tests__/imageViewerModal.test.tsx[2m > [22m[2mImageViewerModal - Unknown Face Boxes & Person Changing[2m > [22m[2mallows changing an unknown face to an existing person directly from Inspect Faces drawer
[22m[39mWarning: An update to ImageViewerModal inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ImageViewerModal (C:/Users/DELL/face-clubbing/frontend/src/components/ImageViewerModal.tsx:23:3)
Warning: An update to ImageViewerModal inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ImageViewerModal (C:/Users/DELL/face-clubbing/frontend/src/components/ImageViewerModal.tsx:23:3)

[90mstderr[2m | src/__tests__/twoStageInteraction.test.tsx[2m > [22m[2mOrganizer Two-Stage Interaction & Drive Folder ID Extraction[2m > [22m[2mdoes NOT show Set API key button when API key is already configured
[22m[39mWarning: An update to HomeScreen inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at HomeScreen (C:/Users/DELL/face-clubbing/frontend/src/components/HomeScreen.tsx:61:3)

[90mstderr[2m | src/__tests__/imageViewerModal.test.tsx[2m > [22m[2mImageViewerModal - Unknown Face Boxes & Person Changing[2m > [22m[2mallows creating a new person for an unknown face
[22m[39mWarning: An update to ImageViewerModal inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ImageViewerModal (C:/Users/DELL/face-clubbing/frontend/src/components/ImageViewerModal.tsx:23:3)
Warning: An update to ImageViewerModal inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ImageViewerModal (C:/Users/DELL/face-clubbing/frontend/src/components/ImageViewerModal.tsx:23:3)

[90mstderr[2m | src/__tests__/imageViewerModal.test.tsx[2m > [22m[2mImageViewerModal - Unknown Face Boxes & Person Changing[2m > [22m[2mallows detaching a known face to unknown
[22m[39mWarning: An update to ImageViewerModal inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ImageViewerModal (C:/Users/DELL/face-clubbing/frontend/src/components/ImageViewerModal.tsx:23:3)
Warning: An update to ImageViewerModal inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ImageViewerModal (C:/Users/DELL/face-clubbing/frontend/src/components/ImageViewerModal.tsx:23:3)

[90mstderr[2m | src/__tests__/openProject.test.tsx[2m > [22m[2mOpen Saved Project Feature[2m > [22m[2mhandles moved/deleted folder (404) and offers removal from list
[22m[39mOpen project failed: Error: 404: Work folder 'C:/photos/deleted.work' not found or was moved.
    at C:/Users/DELL/face-clubbing/frontend/src/__tests__/openProject.test.tsx:118:7
    at [90mfile:///C:/Users/DELL/face-clubbing/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:1628:35
    at [90mfile:///C:/Users/DELL/face-clubbing/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:2783:26
    at [90mfile:///C:/Users/DELL/face-clubbing/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:3321:20
    at new Promise (<anonymous>)
    at runWithCancel [90m(file:///C:/Users/DELL/face-clubbing/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:3316:10[90m)[39m
    at [90mfile:///C:/Users/DELL/face-clubbing/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:3301:20
    at new Promise (<anonymous>)
    at runWithTimeout [90m(file:///C:/Users/DELL/face-clubbing/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:3259:10[90m)[39m
    at [90mfile:///C:/Users/DELL/face-clubbing/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:3882:64

[90mstderr[2m | src/__tests__/unrecognizedTriageRevamp.test.tsx[2m > [22m[2mRevamped Unrecognized Triage & Image Viewer[2m > [22m[2mallows multi-selecting faces and clicking one button to add them all
[22m[39mWarning: An update to UnrecognizedTriage inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at UnrecognizedTriage (C:/Users/DELL/face-clubbing/frontend/src/components/UnrecognizedTriage.tsx:23:3)
Warning: An update to UnrecognizedTriage inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at UnrecognizedTriage (C:/Users/DELL/face-clubbing/frontend/src/components/UnrecognizedTriage.tsx:23:3)
Warning: An update to UnrecognizedTriage inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at UnrecognizedTriage (C:/Users/DELL/face-clubbing/frontend/src/components/UnrecognizedTriage.tsx:23:3)
Warning: An update to UnrecognizedTriage inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at UnrecognizedTriage (C:/Users/DELL/face-clubbing/frontend/src/components/UnrecognizedTriage.tsx:23:3)

[90mstderr[2m | src/__tests__/exportScreen.test.tsx[2m > [22m[2mExportScreen Component[2m > [22m[2mauto-populates gallery title from initialTitle / drive folder
[22m[39mWarning: An update to ExportScreen inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ExportScreen (C:/Users/DELL/face-clubbing/frontend/src/components/ExportScreen.tsx:20:3)
Warning: An update to ExportScreen inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ExportScreen (C:/Users/DELL/face-clubbing/frontend/src/components/ExportScreen.tsx:20:3)
Warning: An update to ExportScreen inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ExportScreen (C:/Users/DELL/face-clubbing/frontend/src/components/ExportScreen.tsx:20:3)
Warning: An update to ExportScreen inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ExportScreen (C:/Users/DELL/face-clubbing/frontend/src/components/ExportScreen.tsx:20:3)
Warning: An update to ExportScreen inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ExportScreen (C:/Users/DELL/face-clubbing/frontend/src/components/ExportScreen.tsx:20:3)
Warning: An update to ExportScreen inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ExportScreen (C:/Users/DELL/face-clubbing/frontend/src/components/ExportScreen.tsx:20:3)

[90mstderr[2m | src/__tests__/openProject.test.tsx[2m > [22m[2mOpen Saved Project Feature[2m > [22m[2mblocks opening project while a scan is running (409)
[22m[39mOpen project failed: Error: 409: Cannot open a project while a scan is running.
    at C:/Users/DELL/face-clubbing/frontend/src/__tests__/openProject.test.tsx:160:7
    at [90mfile:///C:/Users/DELL/face-clubbing/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:1628:35
    at [90mfile:///C:/Users/DELL/face-clubbing/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:2783:26
    at [90mfile:///C:/Users/DELL/face-clubbing/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:3321:20
    at new Promise (<anonymous>)
    at runWithCancel [90m(file:///C:/Users/DELL/face-clubbing/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:3316:10[90m)[39m
    at [90mfile:///C:/Users/DELL/face-clubbing/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:3301:20
    at new Promise (<anonymous>)
    at runWithTimeout [90m(file:///C:/Users/DELL/face-clubbing/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:3259:10[90m)[39m
    at [90mfile:///C:/Users/DELL/face-clubbing/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:3882:64
```
- **Summary**: 50 passed across 11 test files in 35.52s.

---

### Check D2: `npm test` in `viewer/` (Static Viewer Vitest Suite)
- **Source File**: `scratch/vitest_viewer.txt`
- **SHA-256 Digest**: `C1E206E53154FCF727459037B9D23FFC148FB2EF092B6944279636F6F99C8A18`
- **PowerShell `Get-FileHash` Verification**:
```text
Algorithm : SHA256
Hash      : C1E206E53154FCF727459037B9D23FFC148FB2EF092B6944279636F6F99C8A18
Path      : C:\Users\DELL\face-clubbing\scratch\vitest_viewer.txt
```
- **Verbatim Output**:
```text
> photosorter-viewer@1.0.0 test
> vitest run --run


[1m[30m[46m RUN [49m[39m[22m [36mv5.0.3 [39m[90mC:/Users/DELL/face-clubbing/viewer[39m

 [32m✓[39m src/__tests__/viewer.test.tsx [2m([22m[2m6 tests[22m[2m)[22m[33m 319[2mms[22m[39m

[2m Test Files [22m [1m[32m1 passed[39m[22m[90m (1)[39m
[2m      Tests [22m [1m[32m6 passed[39m[22m[90m (6)[39m
[2m   Start at [22m 07:21:15
[2m   Duration [22m 35.64s[2m (import 63%, environment 36%, tests 1%, transform 1%)[22m
```
- **Summary**: 6 passed across 1 test file.

---

### Check E: `node frontend/scripts/e2e.mjs` (End-to-End Browser Pipeline)
- **Source File**: `scratch/e2e_run.txt`
- **SHA-256 Digest**: `3543E57D7A4A36E803E364E7D967C8F17AB0C1CABA8E8DEF768F16C72929E39A`
- **PowerShell `Get-FileHash` Verification**:
```text
Algorithm : SHA256
Hash      : 3543E57D7A4A36E803E364E7D967C8F17AB0C1CABA8E8DEF768F16C72929E39A
Path      : C:\Users\DELL\face-clubbing\scratch\e2e_run.txt
```
- **Verbatim Output (Steps A through M & Invariant Assertions)**:
```text
================================================================
PhotoSorter Phase 4: Full End-to-End Browser Verification
[MODE] Running against built UI (frontend/dist) served directly by uvicorn
Isolated test execution against temporary workspace
================================================================

[SPAWN] Starting uvicorn with isolated work/output/cache dirs on port 8765...
[SERVER READY] PhotoSorter API running at http://127.0.0.1:8765, UI at http://127.0.0.1:8765
[BROWSER] Launching headless Chromium via Playwright...

----------------------------------------------------------------
STEP A: Start sorting job, verify >= 5 SSE updates, end at 192 people
----------------------------------------------------------------
[STEP A] Sorting job started. Collecting SSE progress updates...
  [PROGRESS UPDATE #1] [scanning]Scanning input: C:\Users\DELL\face-clubbing\test_photos0%
  [PROGRESS UPDATE #2] [scanning]Scanning photos: [1/271] IMG-20260226-WA0037.jpg0%
  [PROGRESS UPDATE #3] [scanning]Scanning photos: [2/271] IMG-20260226-WA0047.jpg0%
  [PROGRESS UPDATE #4] [scanning]Scanning photos: [3/271] IMG-20260227-WA0110.jpg0%
  [PROGRESS UPDATE #5] [scanning]Scanning photos: [4/271] IMG_20260227_220404.jpg0%
  [PROGRESS UPDATE #6] [scanning]Scanning photos: [5/271] IMG_20260227_220436.jpg0%
  [PROGRESS UPDATE #7] [scanning]Scanning photos: [6/271] IMG_20260227_220543.jpg0%
  [PROGRESS UPDATE #8] [scanning]Scanning photos: [7/271] IMG_20260227_222103.jpg0.1%
[STEP A] Total progress updates recorded: 12 (>= 5 required)
[STEP A] Review People screen loaded. People count: 192
[INVARIANT a] clustered=1256, unrecognized=445, total=1701 (invariant = HOLDS)

----------------------------------------------------------------
STEP C: 7-way split from eval/ground_truth.json (Set C) on clean state
----------------------------------------------------------------
[STEP C] Set C ground truth face IDs (8 faces):
  - f_cdfa42b70c134a74_001
  - f_49eff969f7dee3bd_001
  - f_1ba2b67379394309_005
  - f_d9c8bf96d71c7101_005
  - f_34a0bab12251055a_003
  - f_10bae275a2e5daf8_002
  - f_a527ac003612de6e_005
  - f_869adaf675c3009c_006
[STEP C] Set C faces are distributed across 7 initial clusters.
  Cluster #1 size: 71 faces (contains 2 Set C face IDs)
  Cluster #2 size: 1 faces (contains 1 Set C face IDs)
  Cluster #3 size: 1 faces (contains 1 Set C face IDs)
  Cluster #4 size: 1 faces (contains 1 Set C face IDs)
  Cluster #5 size: 1 faces (contains 1 Set C face IDs)
  Cluster #6 size: 1 faces (contains 1 Set C face IDs)
  Cluster #7 size: 1 faces (contains 1 Set C face IDs)
[STEP C] Sum of the seven cluster sizes: 77
[STEP C] Merge button text before click: "Merge Selected (7)"
[STEP C] Merging all 7 clusters in one single action...
[STEP C] Total people count after C: 186
[STEP C] Resulting person face count: 77
[STEP C] Asserting sum (77) === resulting person face count (77)...
  [PASS] Cluster sizes sum (77) equals resulting person face count (77)!
[STEP C] Asserting all 8 Set C faces reside in the merged person by face ID...
  [PASS] All 8 Set C face IDs are present in the unified person:
    - f_cdfa42b70c134a74_001 (confirmed)
    - f_49eff969f7dee3bd_001 (confirmed)
    - f_1ba2b67379394309_005 (confirmed)
    - f_d9c8bf96d71c7101_005 (confirmed)
    - f_34a0bab12251055a_003 (confirmed)
    - f_10bae275a2e5daf8_002 (confirmed)
    - f_a527ac003612de6e_005 (confirmed)
    - f_869adaf675c3009c_006 (confirmed)
[INVARIANT c] clustered=1256, unrecognized=445, total=1701 (invariant = HOLDS)

----------------------------------------------------------------
STEP B: Multi-select merge 3 people in one action (people drops by 2)
----------------------------------------------------------------
[STEP B] Selecting 3 people for multi-merge...
[STEP B] Count after merging 3 people: 184 (before: 186)
[INVARIANT b] clustered=1256, unrecognized=445, total=1701 (invariant = HOLDS)

----------------------------------------------------------------
STEP D: Assign an Unrecognized face (unrecognized count drops by 1)
----------------------------------------------------------------
[STEP D] Unrecognized faces before assign: 445
[STEP D] Unrecognized faces after assign: 444
[STEP D] SUCCESS: Unrecognized faces dropped by exactly 1.
[INVARIANT d] clustered=1257, unrecognized=444, total=1701 (invariant = HOLDS)

----------------------------------------------------------------
STEP E: Perform Undo for each edit type and assert counts return
----------------------------------------------------------------
[STEP E.1] Undoing assign edit...
  Unrecognized count restored to: 445 (baseline: 445)
[INVARIANT e.1] clustered=1256, unrecognized=445, total=1701 (invariant = HOLDS)
[STEP E.2] Undoing 3-way merge...
  People count restored to: 186 (expected: 186)
[INVARIANT e.2] clustered=1256, unrecognized=445, total=1701 (invariant = HOLDS)
[STEP E.3] Undoing 7-way split merge...
  People count restored to baseline: 192 (original: 192)
  Set C faces restored across 7 distinct persons.
[STEP E] SUCCESS: All edit types cleanly undone and counts returned to baseline.
[INVARIANT e.3] clustered=1256, unrecognized=445, total=1701 (invariant = HOLDS)

----------------------------------------------------------------
STEP F: Accept one suggestion and reject another
----------------------------------------------------------------
[STEP F] Initial suggestions count: 31
[STEP F] Accepting suggestion between anchor f_056e4727b8b8d6d0_001 and anchor f_f3de19871f241880_002 (d=0.5012)...
[STEP F] People count after accept: 191 (expected 191)
[STEP F] Rejecting suggestion between anchor f_2916e35d73c60b70_001 and anchor f_3a9077105f8e5efe_006...
[STEP F] Visible suggestion cards after rejection: 29
[STEP F] SUCCESS: Suggestion accepted and rejected with session persistence.
[INVARIANT f] clustered=1256, unrecognized=445, total=1701 (invariant = HOLDS)

----------------------------------------------------------------
STEP G: Trigger rerun and assert edits survive by face ID
----------------------------------------------------------------
[STEP G ACTION] Explicitly assigning unrecognized face ID: f_554ef87868d6ec38_003
  -> Assigning to TARGET person with anchor face ID: f_cdfa42b70c134a74_001
[STEP G PRE-RERUN] people_count: 191
[STEP G PRE-RERUN] unrecognized_faces_count: 444
[STEP G PRE-RERUN] Active persisted edits:
  1. Merged suggestion face anchors: [f_056e4727b8b8d6d0_001] + [f_f3de19871f241880_002]
  2. Assigned face ID f_554ef87868d6ec38_003 to TARGET person [f_cdfa42b70c134a74_001]
[STEP G ACTION] Navigating to Settings tab to rerun clustering with identical settings...
[STEP G ACTION] Clicking "Save & Rerun Clustering"...
[STEP G] Rerun completed! Result summary: Re-clustering completed. 2 edits replayed!People191Unrec Faces444Replayed2All organizer edits survived and were re-applied by stable face ID anchors!...
[STEP G POST-RERUN] people_count: 191
[STEP G POST-RERUN] unrecognized_faces_count: 444
[STEP G ASSERTION] Asserting people_count equals pre-rerun count (191 === 191)...
  [PASS] people_count identical: 191 === 191
[STEP G ASSERTION] Asserting unrecognized_faces_count equals pre-rerun count (444 === 444)...
  [PASS] unrecognized_faces_count identical: 444 === 444
[STEP G ASSERTION] Asserting assigned face f_554ef87868d6ec38_003 is in its TARGET person [f_cdfa42b70c134a74_001]...
  [PASS] Assigned face f_554ef87868d6ec38_003 confirmed in TARGET person (anchor f_cdfa42b70c134a74_001).
[STEP G ASSERTION] Asserting accepted-suggestion anchors (f_056e4727b8b8d6d0_001 & f_f3de19871f241880_002) are in one person...
  [PASS] Both suggestion anchors (f_056e4727b8b8d6d0_001 & f_f3de19871f241880_002) reside in one unified person post-rerun.
[INVARIANT g] clustered=1257, unrecognized=444, total=1701 (invariant = HOLDS)

----------------------------------------------------------------
STEP H: Export bundle to temp folder and assert clean static bundle structure
----------------------------------------------------------------
[STEP H ACTION] Explicitly setting export destination input to isolated path: C:\Users\DELL\face-clubbing\export.e2e_temp
[STEP H] Clicking "Export Public Bundle"...
[STEP H] Export completed: 191 people, 259 photos.
[STEP H] Contents of isolated export directory on disk: config.json,faces,people.json,thumbs
[STEP H] SUCCESS: Bundle contains strictly config.json, people.json, faces/, and thumbs/.
[INVARIANT h] clustered=1257, unrecognized=444, total=1701 (invariant = HOLDS)

----------------------------------------------------------------
STEP I: Batch assign (face_ids) to existing person
----------------------------------------------------------------
[INVARIANT pre_i] clustered=1257, unrecognized=444, total=1701 (invariant = HOLDS)
[INVARIANT i.1_batch_assign] clustered=1259, unrecognized=442, total=1701 (invariant = HOLDS)
[STEP I] Batch assign successful: unrecognized dropped by 2, clustered rose by 2, total invariant 1701 holds.
[INVARIANT i.2_undo_batch_assign] clustered=1257, unrecognized=444, total=1701 (invariant = HOLDS)
[STEP I] Undo batch assign restored invariant and counts cleanly.

----------------------------------------------------------------
STEP J: Detach known face to unknown (op: remove)
----------------------------------------------------------------
[INVARIANT pre_j] clustered=1257, unrecognized=444, total=1701 (invariant = HOLDS)
[INVARIANT j.1_detach_face] clustered=1256, unrecognized=445, total=1701 (invariant = HOLDS)
[STEP J] Detach known face successful: unrecognized rose by 1, clustered dropped by 1, invariant 1701 holds.
[INVARIANT j.2_undo_detach] clustered=1257, unrecognized=444, total=1701 (invariant = HOLDS)
[STEP J] Undo detach restored invariant and counts cleanly.

----------------------------------------------------------------
STEP K: Create new person from selected unrecognized faces
----------------------------------------------------------------
[INVARIANT pre_k] clustered=1257, unrecognized=444, total=1701 (invariant = HOLDS)
[INVARIANT k.1_create_new_person] clustered=1259, unrecognized=442, total=1701 (invariant = HOLDS)
[STEP K] Create new person from selected successful: people rose by 1 (191 -> 192), invariant 1701 holds.
[INVARIANT k.2_undo_create_new_person] clustered=1257, unrecognized=444, total=1701 (invariant = HOLDS)
[STEP K] Undo create new person restored people count and invariant cleanly.

----------------------------------------------------------------
STEP L: Failed save rolling back optimistic UI update
----------------------------------------------------------------
[INVARIANT pre_l] clustered=1257, unrecognized=444, total=1701 (invariant = HOLDS)
[INVARIANT l_failed_save_rollback] clustered=1257, unrecognized=444, total=1701 (invariant = HOLDS)
[STEP L] Failed save correctly rolled back / preserved state; invariant 1256 + 445 = 1701 holds intact.

----------------------------------------------------------------
STEP M: Open saved project (reopen past export/work folder, edit, close, reopen)
----------------------------------------------------------------
[INVARIANT pre_m] clustered=1257, unrecognized=444, total=1701 (invariant = HOLDS)
[STEP M ACTION] Clicking Open saved project in header
[STEP M] Recent projects modal opened successfully.
[INVARIANT m.1_after_open] clustered=1257, unrecognized=444, total=1701 (invariant = HOLDS)
[STEP M] Project opened from work-dir: invariant 1256 + 445 = 1701 holds.
[STEP M ACTION] Renaming person with anchor [f_cdfa42b70c134a74_001] to 'Persisted Project VIP'
[INVARIANT m.2_after_edit] clustered=1257, unrecognized=444, total=1701 (invariant = HOLDS)
[STEP M] Edit applied: invariant 1256 + 445 = 1701 holds.
[STEP M ACTION] Reopening project to verify edit persistence
[STEP M PASS] Reopened project successfully retained edit without re-scanning.
[INVARIANT m.3_reopened_project] clustered=1257, unrecognized=444, total=1701 (invariant = HOLDS)
[STEP M PASS] Invariant 1256 + 445 = 1701 holds before, during, and after project open/close/reopen cycle.
[STEP M ACTION] Triggering undo after reopen to confirm previous state returns
[STEP M PASS] Undo after reopen reverted label from 'Persisted Project VIP' back to 'null'.
[INVARIANT m.4_clean_undo] clustered=1257, unrecognized=444, total=1701 (invariant = HOLDS)
[STEP M PASS] Undo restored clean baseline and invariant holds.

----------------------------------------------------------------
ISOLATION AUDIT: Asserting canonical export/ and export.work/ were NEVER modified
----------------------------------------------------------------
[ISOLATION AUDIT PASS] Canonical export.work/edits.json unchanged (SHA-256: da76d723883a3a561492d40711efc831aaac6d5431712c9ba7bfa7b101ea9f2e).
[ISOLATION AUDIT PASS] Canonical export/ file list unchanged: [assets, config.json, faces, gallery.html, index.html, people.json, thumbs].
[ISOLATION AUDIT PASS] Canonical export/people.json unchanged (SHA-256: d880d3e309cd124bf64fe90dc3a11c7192b037c569b57ba873fef0c31de9b943).

----------------------------------------------------------------
CLUSTER-ID AUDIT: Verifying zero pNNN tokens in printed assertions and output
----------------------------------------------------------------
[CLUSTER-ID AUDIT PASS] Zero pNNN tokens detected across all 189 printed log/assertion lines.

================================================================
ALL PHASE 4 E2E BROWSER VERIFICATION CHECKS PASSED (100%)
================================================================
```
- **Summary**: All steps passed (including Step M: open saved project, edit, close, reopen, and undo). Strict invariant 1,256 + 445 = 1,701 holds. Zero `\bp\d{3}\b` tokens in emitted payloads.

---

### Check F: `python eval/check_baseline.py` (Pinned Baseline Fixture Verification)
- **Source File**: `scratch/check_baseline.txt`
- **SHA-256 Digest**: `0DB15D5276B0F0A2CC7303F69540E8F4FD641A55DB5D4C2A36FBD9FA421A4825`
- **PowerShell `Get-FileHash` Verification**:
```text
Algorithm : SHA256
Hash      : 0DB15D5276B0F0A2CC7303F69540E8F4FD641A55DB5D4C2A36FBD9FA421A4825
Path      : C:\Users\DELL\face-clubbing\scratch\check_baseline.txt
```
- **Verbatim Output**:
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
- **Summary**: 100% OK (All canonical baseline metrics verified).

---

### Check G: `python eval/verify_windowed.py` (Windowed Launch Automation)
- **Source File**: `scratch/windowed_run.txt`
- **SHA-256 Digest**: `2793BC544A73651E75F90B7FA256BB7A3F48321E9EDED3C265A6EDCBECF258C8`
- **PowerShell `Get-FileHash` Verification**:
```text
Algorithm : SHA256
Hash      : 2793BC544A73651E75F90B7FA256BB7A3F48321E9EDED3C265A6EDCBECF258C8
Path      : C:\Users\DELL\face-clubbing\scratch\windowed_run.txt
```
- **Verbatim Output**:
```text
================================================================================
PHOTOSORTER WINDOWED LAUNCH VERIFICATION (eval/verify_windowed.py)
================================================================================
[INFO] PE Subsystem: 2 (2 = Windows GUI, 3 = Windows CUI/Console)
[PASS] (b) PE Subsystem is IMAGE_SUBSYSTEM_WINDOWS_GUI (no console window)

[INFO] Launching executable in WINDOWED mode (without --no-gui):
       C:\Users\DELL\face-clubbing\dist\photosorter.exe --port 52520 --work-dir C:\Users\DELL\AppData\Local\Temp\test_windowed_32j7tsq1\work --output-dir C:\Users\DELL\AppData\Local\Temp\test_windowed_32j7tsq1\export
[PASS] (c) Server online and healthy at http://127.0.0.1:52520/api/health
[PASS] (c) Frontend page loads successfully (status 200, HTML content served)

[INFO] Searching for top-level window titled 'PhotoSorter'...
[PASS] (a) Top-level window found: hwnd=1574148, title='PhotoSorter'
[PASS] (b) Verified no ConsoleWindowClass window associated with the process

[INFO] Sending WM_CLOSE (0x0010) to window hwnd=1574148...
[PASS] (d) Closing window cleanly ended process (exit code: 0)
[PASS] (d) Port 52520 successfully released and re-bindable

================================================================================
ALL WINDOWED LAUNCH CHECKS PASSED AUTOMATICALLY:
 [PASS] (a) Top-level window titled 'PhotoSorter' appeared
 [PASS] (b) No console window (PE Subsystem 2 GUI, no ConsoleWindowClass)
 [PASS] (c) Page loads (health check 200, HTML served on process port)
 [PASS] (d) WM_CLOSE cleanly terminated process and released bound port
================================================================================
```
- **Summary**: All windowed launch checks passed (PE Subsystem 2 GUI, hwnd found, WM_CLOSE ended process cleanly and released port).

---

### Check H: `python eval/verify_exe.py` (Standalone Executable Verification)
- **Source File**: `scratch/verify_exe.txt`
- **SHA-256 Digest**: `4617C8139F9F598F1E7ABF59B590CB2C9D803BE5720F6FA309D33D84C3DD5205`
- **PowerShell `Get-FileHash` Verification**:
```text
Algorithm : SHA256
Hash      : 4617C8139F9F598F1E7ABF59B590CB2C9D803BE5720F6FA309D33D84C3DD5205
Path      : C:\Users\DELL\face-clubbing\scratch\verify_exe.txt
```
- **Verbatim Output**:
```text
================================================================================
PHOTOSORTER STANDALONE EXECUTABLE VERIFICATION (eval/verify_exe.py)
================================================================================
[PASS] Executable located: C:\Users\DELL\face-clubbing\dist\photosorter.exe
       Binary Size: 160,709,431 bytes (153.26 MB)
       Subsystem Code: 2 -> IMAGE_SUBSYSTEM_WINDOWS_GUI (Windowed - No console popup)
[PASS] Subsystem check: Built as pure Windows GUI application (console=False).
[INFO] Pre-seeded embedding cache into temp work dir (342 cached photos)

[INFO] Isolated Test Environment:
       Temp Root:   C:\Users\DELL\AppData\Local\Temp\photosorter_exe_verify_6pgpd4lt
       Work Dir:    C:\Users\DELL\AppData\Local\Temp\photosorter_exe_verify_6pgpd4lt\work
       Export Dir:  C:\Users\DELL\AppData\Local\Temp\photosorter_exe_verify_6pgpd4lt\export
       Port:        56606

[INFO] Launching: C:\Users\DELL\face-clubbing\dist\photosorter.exe --no-gui --port 56606 --work-dir C:\Users\DELL\AppData\Local\Temp\photosorter_exe_verify_6pgpd4lt\work --output-dir C:\Users\DELL\AppData\Local\Temp\photosorter_exe_verify_6pgpd4lt\export
[PASS] Executable online in 16.34s at http://127.0.0.1:56606
[PASS] Frontend UI assets properly mounted at root / (status 200)

[INFO] Triggering job on input: C:\Users\DELL\face-clubbing\test_photos
[PASS] Job started: {'job_id': 'a4870a3d', 'status': 'running', 'stage': 'starting', 'current': 0, 'total': 0, 'percent': 0.0, 'progress': 0.0, 'current_file': None, 'eta_seconds': None, 'elapsed_seconds': 0.0, 'start_time': 1792201949.7984169, 'message': 'Initializing job...', 'error': None, 'result_summary': None, 'recent_faces': []}
       [Job Progress] Stage: processing   | Progress:   4.9% (percent=  4.9%) | [9/271] [9/271] IMG_20260303_233547.jpg (28 faces)
       [Job Progress] Stage: clustering   | Progress:  92.0% (percent= 92.0%) | [271/271] Clustering faces by person with second-pass m
       [Job Progress] Stage: exporting    | Progress: 100.0% (percent=100.0%) | [271/271] Generating static export bundle in C:\Users\D
       [Job Progress] Stage: exporting    | Progress: 100.0% (percent=100.0%) | [271/271] Generating static export bundle in C:\Users\D
       [Job Progress] Stage: exporting    | Progress: 100.0% (percent=100.0%) | [271/271] Generating static export bundle in C:\Users\D
       [Job Progress] Stage: exporting    | Progress: 100.0% (percent=100.0%) | [271/271] Generating static export bundle in C:\Users\D
       [Job Progress] Stage: exporting    | Progress: 100.0% (percent=100.0%) | [271/271] Generating static export bundle in C:\Users\D
       [Job Progress] Stage: exporting    | Progress: 100.0% (percent=100.0%) | [271/271] Generating static export bundle in C:\Users\D
       [Job Progress] Stage: exporting    | Progress: 100.0% (percent=100.0%) | [271/271] Generating static export bundle in C:\Users\D
       [Job Progress] Stage: exporting    | Progress: 100.0% (percent=100.0%) | [271/271] Generating static export bundle in C:\Users\D
       [Job Progress] Stage: complete     | Progress: 100.0% (percent=100.0%) | [271/271] Job finished. Clustered 192 people.

[PASS] Pipeline finished in 17.09s
[PASS] Real progress broadcast verified: job.percent actively tracked scanning/detection.

--- BASELINE METRICS REPRODUCIBILITY CHECK ---
People Clusters:     192 (Baseline expected: 192)
Unrecognized Faces:  445 (Baseline expected: 445)
Unrecognized Photos: 168 (Baseline expected: 168)
Total Photo Records: 259 (Baseline expected: 259)
[PASS] All cluster, face, and photo counts match pinned baseline fixture identically!
[PASS] Public Export Bundle Hygiene verified. Export files: ['config.json', 'faces', 'people.json', 'thumbs']

[INFO] Terminating executable...
[PASS] Executable terminated cleanly; port 56606 released.

================================================================================
ALL PHASE 5 EXECUTABLE REQUIREMENTS VERIFIED SUCCESSFULLY!
================================================================================
```
- **Summary**: Standalone executable verified (PE Subsystem 2 GUI, online in 16.34s, pipeline finished in 17.09s, baseline metrics match: 192 clusters, 445 unrec faces, 168 unrec photos, 259 photos, export bundle clean).

---

### Check I: Cold Cache & First-Run Model Download Audit (`eval/verify_models_download.py`)
- **Source File**: `scratch/models_run.txt`
- **SHA-256 Digest**: `ACA74048F1B230F85BBC54346F0F6AA526CE15F62067E712BC2044388BD3A015`
- **Verbatim Output**:
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
  - Measured speed: **7.49 s per photo** (~32.3 minutes for 259 photos).
  - Cause: Dense event photos containing group shots with up to 40 faces/photo requiring ArcFace 512-d embeddings.

---

### Check J: Fresh `git clone` Execution from HEAD (`6e2b2ce`)
Executed in a fresh isolated temporary directory created by `git clone https://github.com/Sufiyan-Shiraj/face-clubbing.git` from current HEAD (`6e2b2ce`).

#### 1. Pytest (`pytest -q -rs`)
- **Source File**: `scratch/fresh_clone_pytest.txt`
- **SHA-256 Digest**: `C3002CB3ACC81B37A4047279D2A686401D0102E8C4329EA28D400CA86198F935`
- **PowerShell `Get-FileHash` Verification**:
```text
Algorithm : SHA256
Hash      : C3002CB3ACC81B37A4047279D2A686401D0102E8C4329EA28D400CA86198F935
Path      : C:\Users\DELL\face-clubbing\scratch\fresh_clone_pytest.txt
```
- **Verbatim Output**:
```text
......s.s......................................................s........ [ 93%]
.....                                                                    [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_api.py:444: Requires baseline fixture and embedding cache
SKIPPED [1] tests\test_api.py:563: Requires baseline fixture and embedding cache
SKIPPED [1] tests\test_isolation.py:24: Requires export/ and export.work/ embedding cache
74 passed, 3 skipped in 8.49s
```
- **Summary**: 74 passed, 3 skipped in 8.49s (0 failures; the 3 skipped tests cleanly require local live embedding caches).

#### 2. Frontend Vitest (`npm ci && npm test`)
- **Source File**: `scratch/fresh_clone_frontend.txt`
- **SHA-256 Digest**: `E6F2F65B42A2794E848B5BA6FFCAAC77EBC6E5F3D30AC5513EC33EB6C6309444`
- **PowerShell `Get-FileHash` Verification**:
```text
Algorithm : SHA256
Hash      : E6F2F65B42A2794E848B5BA6FFCAAC77EBC6E5F3D30AC5513EC33EB6C6309444
Path      : C:\Users\DELL\face-clubbing\scratch\fresh_clone_frontend.txt
```
- **Verbatim Output**:
```text
> photosorter-frontend@1.0.0 test
> vitest run --run


[1m[30m[46m RUN [49m[39m[22m [36mv5.0.3 [39m[90mC:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend[39m

 [32m✓[39m src/__tests__/openProject.test.tsx [2m([22m[2m6 tests[22m[2m)[22m[33m 918[2mms[22m[39m
   [32m✓[39m Open Saved Project Feature [2m(6)[22m
     [33m[2m✓[22m[39m renders recent projects list with name, source, and counts[33m 398[2mms[22m[39m
 [32m✓[39m src/__tests__/driveIntegration.test.tsx [2m([22m[2m7 tests[22m[2m)[22m[33m 898[2mms[22m[39m
 [32m✓[39m src/__tests__/twoStageInteraction.test.tsx [2m([22m[2m8 tests[22m[2m)[22m[33m 1194[2mms[22m[39m
   [32m✓[39m Organizer Two-Stage Interaction & Drive Folder ID Extraction [2m(8)[22m
     [33m[2m✓[22m[39m renders Initial State with no face preview frames visible[33m 566[2mms[22m[39m
 [32m✓[39m src/__tests__/unrecognizedTriageRevamp.test.tsx [2m([22m[2m4 tests[22m[2m)[22m[33m 656[2mms[22m[39m
 [32m✓[39m src/__tests__/exportScreen.test.tsx [2m([22m[2m5 tests[22m[2m)[22m[33m 659[2mms[22m[39m
 [32m✓[39m src/__tests__/imageViewerModal.test.tsx [2m([22m[2m4 tests[22m[2m)[22m[33m 1676[2mms[22m[39m
   [32m✓[39m ImageViewerModal - Unknown Face Boxes & Person Changing [2m(4)[22m
     [33m[2m✓[22m[39m renders bounding boxes for BOTH known and unknown faces[33m 448[2mms[22m[39m
     [33m[2m✓[22m[39m allows changing an unknown face to an existing person directly from Inspect Faces drawer[33m 803[2mms[22m[39m
 [32m✓[39m src/__tests__/mergeSelection.test.ts [2m([22m[2m4 tests[22m[2m)[22m[32m 11[2mms[22m[39m
 [32m✓[39m src/__tests__/pollingFallback.test.ts [2m([22m[2m2 tests[22m[2m)[22m[32m 22[2mms[22m[39m
 [32m✓[39m src/__tests__/suggestionList.test.ts [2m([22m[2m4 tests[22m[2m)[22m[32m 13[2mms[22m[39m
 [32m✓[39m src/__tests__/undoControl.test.ts [2m([22m[2m3 tests[22m[2m)[22m[32m 11[2mms[22m[39m
 [32m✓[39m src/__tests__/homeScreen.test.tsx [2m([22m[2m3 tests[22m[2m)[22m[32m 127[2mms[22m[39m

[2m Test Files [22m [1m[32m11 passed[39m[22m[90m (11)[39m
[2m      Tests [22m [1m[32m50 passed[39m[22m[90m (50)[39m
[2m   Start at [22m 07:34:09
[2m   Duration [22m 19.68s[2m (environment 45%, import 38%, tests 12%, transform 4%, worker 1%)[22m

[2m    Isolate [22m [33m11 workers spawned[39m[2m · ~2.38s startup each (spawn + environment, per file)[22m
[2m            [22m [2mat least ~6.35s faster with [22m[33misolate: false[39m[2m — reuses workers across files instead of one per file[22m

[90mstderr[2m | src/__tests__/openProject.test.tsx[2m > [22m[2mOpen Saved Project Feature[2m > [22m[2mhandles moved/deleted folder (404) and offers removal from list
[22m[39mOpen project failed: Error: 404: Work folder 'C:/photos/deleted.work' not found or was moved.
    at C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/src/__tests__/openProject.test.tsx:118:7
    at [90mfile:///C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:1628:35
    at [90mfile:///C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:2783:26
    at [90mfile:///C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:3321:20
    at new Promise (<anonymous>)
    at runWithCancel [90m(file:///C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:3316:10[90m)[39m
    at [90mfile:///C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:3301:20
    at new Promise (<anonymous>)
    at runWithTimeout [90m(file:///C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:3259:10[90m)[39m
    at [90mfile:///C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:3882:64

Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
[90mstderr[2m | src/__tests__/openProject.test.tsx[2m > [22m[2mOpen Saved Project Feature[2m > [22m[2mblocks opening project while a scan is running (409)
[22m[39mOpen project failed: Error: 409: Cannot open a project while a scan is running.
    at C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/src/__tests__/openProject.test.tsx:160:7
    at [90mfile:///C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:1628:35
    at [90mfile:///C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:2783:26
    at [90mfile:///C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:3321:20
    at new Promise (<anonymous>)
    at runWithCancel [90m(file:///C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:3316:10[90m)[39m
    at [90mfile:///C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:3301:20
    at new Promise (<anonymous>)
    at runWithTimeout [90m(file:///C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:3259:10[90m)[39m
    at [90mfile:///C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/[39mnode_modules/[4mvitest[24m/dist/chunks/run.BTlFXlnv.js:3882:64

Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
Not implemented: HTMLCanvasElement's getContext() method: without installing the canvas npm package
[90mstderr[2m | src/__tests__/twoStageInteraction.test.tsx[2m > [22m[2mOrganizer Two-Stage Interaction & Drive Folder ID Extraction[2m > [22m[2mdoes NOT show Set API key button when API key is already configured
[22m[39mWarning: An update to HomeScreen inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at HomeScreen (C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/src/components/HomeScreen.tsx:61:3)

[90mstderr[2m | src/__tests__/exportScreen.test.tsx[2m > [22m[2mExportScreen Component[2m > [22m[2mauto-populates gallery title from initialTitle / drive folder
[22m[39mWarning: An update to ExportScreen inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ExportScreen (C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/src/components/ExportScreen.tsx:20:3)
Warning: An update to ExportScreen inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ExportScreen (C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/src/components/ExportScreen.tsx:20:3)
Warning: An update to ExportScreen inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ExportScreen (C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/src/components/ExportScreen.tsx:20:3)
Warning: An update to ExportScreen inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ExportScreen (C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/src/components/ExportScreen.tsx:20:3)
Warning: An update to ExportScreen inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ExportScreen (C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/src/components/ExportScreen.tsx:20:3)
Warning: An update to ExportScreen inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ExportScreen (C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/src/components/ExportScreen.tsx:20:3)

[90mstderr[2m | src/__tests__/unrecognizedTriageRevamp.test.tsx[2m > [22m[2mRevamped Unrecognized Triage & Image Viewer[2m > [22m[2mallows multi-selecting faces and clicking one button to add them all
[22m[39mWarning: An update to UnrecognizedTriage inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at UnrecognizedTriage (C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/src/components/UnrecognizedTriage.tsx:23:3)
Warning: An update to UnrecognizedTriage inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at UnrecognizedTriage (C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/src/components/UnrecognizedTriage.tsx:23:3)
Warning: An update to UnrecognizedTriage inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at UnrecognizedTriage (C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/src/components/UnrecognizedTriage.tsx:23:3)
Warning: An update to UnrecognizedTriage inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at UnrecognizedTriage (C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/src/components/UnrecognizedTriage.tsx:23:3)

[90mstderr[2m | src/__tests__/imageViewerModal.test.tsx[2m > [22m[2mImageViewerModal - Unknown Face Boxes & Person Changing[2m > [22m[2mallows changing an unknown face to an existing person directly from Inspect Faces drawer
[22m[39mWarning: An update to ImageViewerModal inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ImageViewerModal (C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/src/components/ImageViewerModal.tsx:23:3)
Warning: An update to ImageViewerModal inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ImageViewerModal (C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/src/components/ImageViewerModal.tsx:23:3)

[90mstderr[2m | src/__tests__/imageViewerModal.test.tsx[2m > [22m[2mImageViewerModal - Unknown Face Boxes & Person Changing[2m > [22m[2mallows creating a new person for an unknown face
[22m[39mWarning: An update to ImageViewerModal inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ImageViewerModal (C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/src/components/ImageViewerModal.tsx:23:3)
Warning: An update to ImageViewerModal inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ImageViewerModal (C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/src/components/ImageViewerModal.tsx:23:3)

[90mstderr[2m | src/__tests__/imageViewerModal.test.tsx[2m > [22m[2mImageViewerModal - Unknown Face Boxes & Person Changing[2m > [22m[2mallows detaching a known face to unknown
[22m[39mWarning: An update to ImageViewerModal inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ImageViewerModal (C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/src/components/ImageViewerModal.tsx:23:3)
Warning: An update to ImageViewerModal inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://reactjs.org/link/wrap-tests-with-act
    at ImageViewerModal (C:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/frontend/src/components/ImageViewerModal.tsx:23:3)
```
- **Summary**: 50 passed across 11 test files in 19.68s.

#### 3. Viewer Vitest (`npm ci && npm test`)
- **Source File**: `scratch/fresh_clone_viewer.txt`
- **SHA-256 Digest**: `2DEAA36BDC22F9E05F91DD140AE5F40236B3424261EBFB9C0A2A160060339A83`
- **PowerShell `Get-FileHash` Verification**:
```text
Algorithm : SHA256
Hash      : 2DEAA36BDC22F9E05F91DD140AE5F40236B3424261EBFB9C0A2A160060339A83
Path      : C:\Users\DELL\face-clubbing\scratch\fresh_clone_viewer.txt
```
- **Verbatim Output**:
```text
> photosorter-viewer@1.0.0 test
> vitest run --run


[1m[30m[46m RUN [49m[39m[22m [36mv5.0.3 [39m[90mC:/Users/DELL/AppData/Local/Temp/fresh_clone_audit/viewer[39m

 [32m✓[39m src/__tests__/viewer.test.tsx [2m([22m[2m6 tests[22m[2m)[22m[33m 318[2mms[22m[39m

[2m Test Files [22m [1m[32m1 passed[39m[22m[90m (1)[39m
[2m      Tests [22m [1m[32m6 passed[39m[22m[90m (6)[39m
[2m   Start at [22m 07:35:39
[2m   Duration [22m 4.20s[2m (import 46%, environment 39%, tests 8%, transform 6%)[22m
```
- **Summary**: 6 passed across 1 test file in 4.20s.

---

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
- Measured variance: Between 18.84s and 27.33s (Average: 23.35 s).

2. **UI Loading State**:
- Confirmed: Inlined `#app-loading` element in `frontend/index.html` and `isInitialLoading` state in `frontend/src/App.tsx` display an immediate responsive dark loading screen with spinner, title "PhotoSorter", and subtitle "Connecting to local engine..." before the server is ready.
- Captured screenshot: `initial_loading_screen_1791959889786.png`.

---

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

### Check M: `python eval/verify_drive_phase6.py --folder "https://drive.google.com/drive/folders/1SwPf5q_B6KpyNGIlOM3Qck6pdcOOyJZ3"` (Phase 6 Live Google Drive Integration Verification)
- **Source File**: `scratch/verify_drive_phase6_raw.txt`
- **SHA-256 Digest**: `A546E96C095B9FD0683578A2D4EACC2C377CEA6D40E97C5D1155FA3D4B1E2B5E`
- **PowerShell `Get-FileHash` Verification**:
```text
Algorithm : SHA256
Hash      : A546E96C095B9FD0683578A2D4EACC2C377CEA6D40E97C5D1155FA3D4B1E2B5E
Path      : C:\Users\DELL\face-clubbing\scratch\verify_drive_phase6_raw.txt
```
- **Live Execution Summary**:
  - **Key Resolution**: Retrieved securely from `~/.photosorter/settings.json` (with `DRIVE_API_KEY` fallback). Zero raw keys printed, logged, or committed.
  - **Error Scenarios**: All 3 error cases tested and passed with sanitized messages (Wrong Key -> `DriveAuthError` HTTP 400; Private Folder -> `DrivePermissionError` HTTP 404; Quota Exceeded -> `DriveQuotaError` HTTP 403).
  - **Live Inventory**: 152 total files listed (83 image files, 69 videos skipped, 0 non-images, 0 subfolders).
  - **Thumbnail Downloads & Resumable Cache**:
    - Pass 1: 83 thumbnails downloaded in 0.03s into `export.work\drive\1SwPf5q_B6KpyNGIlOM3Qck6pdcOOyJZ3`.
    - Pass 2: 83 files processed in 0.01s (100% skipped from cache).
    - Thumbnail Availability: 83 / 83 (100.0%).
    - Alt=media Fallbacks: 0 / 83 (0.0%).
    - Bandwidth: 10,637,818 bytes (10.15 MB thumbnails) vs 133,936,329 bytes (127.73 MB originals) -> **92.1% bandwidth reduction**.
  - **Clustering Engine on Drive Thumbnails (`=s1000`) vs Drive Originals**:
    - Thumbnails (64 px default floor): 83 photos, 490 detected faces, 36 seeds, 182 attached, 218 clustered faces, 15 people clusters (all multi-photo), 272 unattached (255 small, 14 profile, 3 lowscore), 5 unrecognized-only photos.
    - Originals (64 px default floor, downscaled to max 1600 px, downloaded to temp outside repo and deleted afterwards): 83 photos, 489 detected faces, 325 seeds, 73 attached, 398 clustered faces, 51 people clusters (29 multi-photo, 22 singletons), 91 unattached (6 small, 49 profile, 31 lowscore), 2 unrecognized-only photos.
  - **64 px Face-Size Floor Analysis**:
    - Faces under 64 px on Thumbnails (`=s1000`): **434 / 490 (88.6%)** (median face size 34.8 px).
    - Faces under 64 px on Originals: **8 / 489 (1.6%)** (median face size 180.9 px).
  - **Evidence Table (Floor Sweeps on Thumbnails =s1000)**:
    - 64 px (SPEC §6.2 Default): 36 seeds, 182 attached, 218 clustered, 15 people, 255 unrec small, 272 unrec total, 5 unrec photos.
    - 48 px: 88 seeds, 186 attached, 274 clustered, 20 people, 191 unrec small, 216 unrec total, 3 unrec photos.
    - 40 px (Proportional $64 \times 1000/1600$): 137 seeds, 160 attached, 297 clustered, 24 people, 161 unrec small, 193 unrec total, 2 unrec photos.
    - 32 px: 195 seeds, 114 attached, 309 clustered, 26 people, 135 unrec small, 181 unrec total, 2 unrec photos.
    - 24 px: 266 seeds, 73 attached, 339 clustered, 36 people, 91 unrec small, 151 unrec total, 2 unrec photos.
  - **SPEC §6.2 Default Rule Compliance**: SPEC §6.2 defaults remain strictly **unchanged** (`min_face_size = 64`, `seed_min_face_size = 64`). Proposal with evidence table documented in SPEC §18.1 pending organizer review.
  - **Security & Hygiene Audit**: Zero raw API keys in repo, git log history, or `~/.photosorter/projects.json`.

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
- All subsequent commits since `d546e53` (`8493b39`, `3cc5e1a`, `3d56ba3`, `48cfcd6`, `cd77084`, `78f49e8`, `95de186`, `a985b87`, `b5d9a42`, `6f4c510`, `9373f77`, `c96b227`, `6e2b2ce`) are standard linear, fast-forward commits.

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
- **Full Backend Test Suite (Check A)**: **77 passed**, 0 failed, 0 skipped in `pytest -q -rs` in 59.27s. Includes 6 tests in `tests/test_projects.py` covering CRUD, privacy sanitization, work folder deletion, source photo missing, Drive-sourced project, corrupt edits read-only fallback, and concurrent scan 409 conflict, alongside atomic batch assign and isolated replay verification.
- **Phase 1b Verification Audit (Check B)**: **14 / 14 checks passed** in `eval/verify_export.py` across 46 scanned files with zero `\bp\d{3}\b` violations outside comments (Check 6: 77 passed).
- **Phase 3 API Fixture & Live Verification (Check C)**: **All 8 fixture checks + 7 live checks passed** in `python eval/verify_api.py --mode all`.
- **Pinned Baseline Reproduction Check (Check F)**: **100% OK** in `python eval/check_baseline.py`.
- **End-to-End Browser Pipeline Invariant Check (Check E)**: **Step M passed** in `node frontend/scripts/e2e.mjs`. All edit operations cleanly replay, open-project edit persistence verified, undo after reopen reverted label from 'Persisted Project VIP' back to 'null', and strict invariant $1,256 + 445 = 1,701$ holds across all steps with zero `\bp\d{3}\b` tokens in emitted payloads.
- **Frontend Vitest Suite (Check D1)**: **50 passed**, 0 failed across 11 test files in 35.52s in `npm test` (`frontend/`). Includes tests verifying:
  - Open Saved Project modal, recent project list, corrupt edits read-only mode, missing work folder removal, and custom path opening (`openProject.test.tsx`, 6 tests).
  - Two-stage landing flow, Google Drive link extraction, editable character cells, and verified badge (`twoStageInteraction.test.tsx`, 8 tests).
  - Google Drive client configuration and mocked API flows (`driveIntegration.test.tsx`, 7 tests).
  - Revamped compact unrecognized triage, target person preview, and batch multi-select assignment (`unrecognizedTriageRevamp.test.tsx`, 4 tests).
  - Image Viewer dual-mode bounding boxes, on-canvas quick change, slide-over inspect faces drawer, and source missing badge / disabled download (`imageViewerModal.test.tsx`, 4 tests).
  - Export screen directory explorer, auto-populated title, and export action (`exportScreen.test.tsx`, 5 tests).
  - Home screen directory and archive picking (`homeScreen.test.tsx`, 3 tests).
  - Core merge selection, undo control, suggestion lists, and polling fallbacks (`mergeSelection.test.ts`, `undoControl.test.ts`, `suggestionList.test.ts`, `pollingFallback.test.ts`, 13 tests).
- **Viewer Vitest Suite (Check D2)**: **6 passed**, 0 failed across 1 test file in `npm test` (`viewer/`).
- **Desktop Shell & Packaging (Phase 5, Check G & Check H)**: Standalone executable `dist/photosorter.exe` rebuilt and verified with pure Windows GUI subsystem (Subsystem 2), average 23.35s startup (verified in Check K across 3 runs: 27.33s, 23.88s, 18.84s; and 16.34s in Check H / verify_exe.py), real progress broadcasting, identical baseline metrics reproduction (192 clusters, 445 unrec faces, 168 unrec photos, 259 photos), and clean bundle hygiene.
- **Open Saved Project Feature**: **COMPLETE**.
  - **Storage & Privacy**: Stored in `~/.photosorter/projects.json` (outside the repo; respects `PHOTOSORTER_PROJECTS_FILE` in tests). Writes ONLY: `version` (int), `id` (hash), `name` (sanitized string), `work_dir` (path), `export_path` (path), `source_description` (sanitized path or Drive folder ID with all API keys/tokens stripped), `last_opened` (ISO 8601 string), and `counts` (`people`, `photos`). The `exists` flag is computed dynamically when listing projects (`work_path.exists() and work_path.is_dir()`) and is never stored on disk. No photo bytes, face embeddings, biometric templates, or credentials are ever written.
  - **File Safety**: Removing an entry from `projects.json` never deletes files on disk.
  - **Corrupt Edits Safeguard**: Malformed or corrupt `edits.json` safely opens in `read_only=True` mode with a persistent warning banner in the UI and never overwrites user data.
  - **Source Photos Moved/Missing**: Reopens smoothly from local cache; viewing a photo with missing disk source displays a clear "Source missing" badge, warning banner, placeholder, and disabled download button.
  - **Drive-Sourced Projects**: Reopen without requiring an API key, loading directly from cached thumbnails and crops.
- **Organizer Review Evidence Artifacts (Zero Real Faces)**:
  - `scratch/screenshots/review_01_open_saved_project_modal.png`: Open Saved Project modal with Risograph styling, recent project cards, folder-missing alert, and remove-entry action.
  - `scratch/screenshots/review_02_project_read_only_banner.png`: Persistent read-only mode banner displayed upon opening project with corrupt `edits.json`.
  - `scratch/screenshots/review_03_image_viewer_source_missing.png`: Image viewer displaying "Source missing" badge, red floating warning banner, fallback placeholder, and disabled download button for photos moved/deleted from disk.
- **Cold-Run Detection Speed (Check I)**: **7.49 s/photo** on dense event photos (~32.3 minutes for 259 photos) -> **UNVERIFIED against SPEC estimate** (~1 to 1.5 s/photo).
- **Startup Latency (Check K)**: Measured at average 23.35 s (Run 1: 27.33 s, Run 2: 23.88 s, Run 3: 18.84 s).
- **Fresh Clone Verification (Check J)**: Pinned HEAD `6e2b2ce` verified in fresh clone without local live caches: `pytest` passed 74 (3 cleanly skipped) in 8.49s; frontend Vitest passed 50/50 in 19.68s; viewer Vitest passed 6/6 in 4.20s.
- **Native Pickers (Check L)**: Marked **NEEDS ORGANIZER REVIEW** with full manual Cancel vs Confirm steps.
- **Phase 6 Method 1 Live Google Drive Integration (Check M)**: **COMPLETE**. Live verification on public folder `1SwPf5q_B6KpyNGIlOM3Qck6pdcOOyJZ3` verified: 152 total files (83 images, 69 videos skipped), 100% thumbnail availability, 0% alt=media fallbacks, 92.1% bandwidth savings (10.15 MB thumbnails vs 127.73 MB originals). Complete engine runs executed on Drive thumbnails and Drive originals; 64 px floor analysis documented in SPEC §18 (88.6% under 64 px on thumbnails vs 1.6% on originals; evidence table provided for proposed 40 px adaptive floor; SPEC §6.2 defaults kept unchanged). Resumable caching, sanitized error messages, and zero API key leakage verified. Raw evidence: `scratch/verify_drive_phase6_raw.txt` (SHA-256: `a546e96c095b9fd0683578a2d4eacc2c377cea6d40e97c5d1155fa3d4b1e2b5e`).
- **Privacy & Secrets (Section 4)**: Current git history is 100% clean of images/secrets. The 5 old commits with 27 JPEG face-crop contact sheets remain reachable on GitHub; reviewed and accepted by organizer on 2026-10-14.

---

## 6. PROJECT ISOLATION, DRIVE DIRECT LINKING, AUTO-NESTING & CLEANUP AUDIT (2026-10-17)

### Requirements Implemented and Verified
1. **Startup Isolation & Project Active Guard**:
   - `AppState.__init__` starts with `project_active = False` on cold boot unless explicitly configured via test fixture or env flag.
   - Added `GET /api/projects/active` endpoint returning `{active: bool, name: str, people_count: int, photos_count: int}`.
   - Frontend `App.tsx` guards the Review and Publish tabs so they are disabled if no project is active, redirecting cold boots to the Source (`home`) tab.
2. **"New Project" Button**:
   - Added `#header-new-project-btn` in `Header.tsx`.
   - Prompts for unexported work confirmation (`window.confirm`) if unexported changes exist, and calls `POST /api/projects/new`.
   - `POST /api/projects/new` executes `AppState.reset_to_empty()`, resetting runtime state cleanly to an empty project.
3. **Drive Folder Auto-Nesting on Export**:
   - When exporting to an output folder (e.g. `export/`), the bundle automatically creates and nests inside a subfolder titled with the Drive folder name (or active project name), e.g. `export/Echoes of reason 18th`.
   - Prevents duplicate nesting if the chosen directory already ends in that folder name.
4. **Temporary Directory Lifecycle & Cleanup**:
   - During scanning, temporary downloads are saved into `<folder_name>_temp` (e.g. `Echoes of reason 18th_temp`).
   - Upon bundle export, all temporary working directories and `<folder_name>_temp` are automatically deleted.
5. **Standalone HTML (`index.html`) & Google Drive Photo Linking**:
   - On public bundle export, generates a zero-server standalone `index.html` (and `gallery.html`).
   - Google Drive photos are linked directly via shareable URLs (`https://drive.google.com/file/d/<id>/view`).
   - In the standalone gallery, clicking photo cards or modal photos directly opens the full photo on Google Drive in a new tab.
   - Only avatars (`faces/`) and thumbnails (`thumbs/`) are stored locally; full photos are never bundled locally.
6. **Test Suite & Build Health**:
   - Pytest suite: **78 / 78 passed (100%)** in 57.69s.
   - Frontend build (`npm run build` in `frontend/`): **0 errors, exit code 0**.

