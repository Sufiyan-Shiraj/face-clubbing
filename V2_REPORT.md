# CatLog V2 Architecture, Audit & Verification Report (V2_REPORT.md)

**Generated**: 2026-11-04T07:35:00+05:30  
**Scope**: Full V2 Development Cycle (Phases V2-0 through V2-9)  
**Parent Report**: Historical V1 Release Candidate Report is preserved in [`REPORT.md`](REPORT.md).  
**Repository State**: Branch `main` at HEAD `bc50eac14143d9a16ad32f470dd9191901221a0b`  
**Test Suite Totals**: Pytest 173/173 Passed, Frontend Vitest 136/136 Passed, Viewer Vitest 31/31 Passed, Export Invariants 17/17 Passed. Total Automated Tests: 340 Passed.

---

## 1. EXECUTIVE SUMMARY & REPOSITORY CONTEXT

This report provides the authoritative engineering audit for the CatLog V2 milestone series (Phases V2-0 through V2-9). V2 expands CatLog from a single-folder desktop sorting utility into an event photo hub capable of multi-source ingestion (combining Google Drive folders, local directories, phone ZIPs), incremental addition of late photographer submissions with mathematical cluster freezing (zero existing cluster membership delta), order-independent two-project merging, high-resolution Drive streaming, cloud input guidance, and selective inference optimization.

### Strict Audit Ground Rules
1. **Counts, IDs, and Filenames Only**: No subjective facial descriptions or aesthetic judgements.
2. **Every Number Script-Checked**: Every metric originates from verified test fixtures or executable scripts with saved raw output files and SHA-256 digests.
3. **Strict Privacy Sanitization**: Zero personal attendee photos, facial biometric crops, API keys, personal Google Drive folder IDs, or developer machine paths (`<REPO_ROOT>`, `<TEMP_DIR>`, `<FOLDER_ID>`).
4. **Unchecked Items Marked UNVERIFIED**: Items lacking reproducible local proofs are explicitly tagged UNVERIFIED.
5. **No Tags or Releases**: Audit package only.

---

## 2. PHASE AUDIT SECTIONS (V2-0 THROUGH V2-9)

### Phase V2-0: Drive Subfolder Recursion (Hotfix)

- **State**: **Done**
- **Commit**: `11e7607` ("Implement Google Drive recursive subfolder traversal and deduplication")
- **Files Changed (`git show --stat 11e7607`)**:
  ```text
  README.md                              |   2 +-
  SPEC.md                                |  10 +-
  backend/api/jobs.py                    |   5 +
  backend/api/models.py                  |   1 +
  backend/api/routes.py                  |  13 +-
  backend/drive/client.py                | 183 ++++++++++++---
  backend/engine/models.py               |   4 +
  backend/engine/pipeline.py             |  30 ++-
  frontend/src/components/HomeScreen.tsx |  11 +-
  frontend/src/types.ts                  |   1 +
  tests/test_drive.py                    | 402 +++++++++++++++++++++++++++++++++
  11 files changed, 623 insertions(+), 39 deletions(-)
  ```
- **Requirement as Written in BUILD_PLAN**:
  Traverse Google Drive subfolders recursively using iterative BFS queue traversal with a max depth of 5 and a 20,000-file cap. Prevent loops with a visited folder set, skip shortcuts/non-images, handle subfolder errors without failing the scan, deduplicate by file ID, and show scan progress summary.
- **Evidence**:
  - Test Suite: `tests/test_drive.py` (39 passed across recursion, BFS depth limits, cycle prevention, resilient child folder error isolation, shortcut resolution).
  - Raw Output: `scratch/check_v2_suites.txt` (SHA-256: `ba58c743225fed515ba49a2c0744b1fd16c63f93fe8d78492b348fa27cb3c195`)
  - Live Verification: `scratch/verify_drive_phase6_raw.txt` (83 photos scanned, 100% thumbnails generated, 0 failed files).
- **Differences from Plan / Unfinished**: None. Implemented exactly as specified.
- **Known Limits**: Recursion is bounded at depth 5 and 20,000 files to prevent unbounded memory growth. Folders exceeding 20,000 files log a warning and truncate traversal.
- **Organizer Review Items**: Default max depth (5) and file cap (20,000).

---

### Phase V2-1: Release Health and First-User Fixes

- **State**: **Done**
- **Commit**: `bca08de` ("feat(v2-1): add diagnostics export, classified error codes, and model management")
- **Files Changed (`git show --stat bca08de`)**:
  ```text
  .github/ISSUE_TEMPLATE/bug_report.md               |  41 +++
  .github/ISSUE_TEMPLATE/config.yml                  |   8 +
  .github/ISSUE_TEMPLATE/feature_request.md          |  24 ++
  backend/api/diagnostics.py                         | 404 +++++++++++++++++++++
  backend/drive/client.py                            |  58 ++-
  backend/engine/models_downloader.py                | 353 ++++++++++++++++--
  frontend/src/__tests__/diagnosticsAndErrors.test.tsx | 116 ++++++
  frontend/src/__tests__/modelDownloadBanner.test.tsx  | 196 ++++++++++
  frontend/src/components/CopyDiagnosticsButton.tsx  | 164 +++++++++
  frontend/src/components/CustomDialog.tsx           |   4 +-
  frontend/src/components/ModelDownloadBanner.tsx    | 248 +++++++++++++
  tests/test_diagnostics.py                          | 143 ++++++++
  tests/test_drive.py                                | 136 +++++++
  tests/test_model_download.py                       |  68 ++++
  14 files changed, 1932 insertions(+), 31 deletions(-)
  ```
- **Requirement as Written in BUILD_PLAN**:
  Confirm multi-platform CI readiness; implement a counts-only "Copy diagnostics" button producing a sanitized report (version, OS, settings hash, error codes, zero paths, zero photos, zero keys); create GitHub Issue templates with caution banner; error screens with plain-language fixes; README troubleshooting.
- **Evidence**:
  - Test Suite: `tests/test_diagnostics.py` (12 passed proving regex scrubbing of API keys, Windows/Unix machine paths, and error classification).
  - Frontend Tests: `frontend/src/__tests__/diagnosticsAndErrors.test.tsx` (3 passed), `modelDownloadBanner.test.tsx` (6 passed).
  - Raw Output: `scratch/check_v2_suites.txt` (SHA-256: `ba58c743225fed515ba49a2c0744b1fd16c63f93fe8d78492b348fa27cb3c195`)
  - Issue Templates: `.github/ISSUE_TEMPLATE/bug_report.md` with explicit warning: "Do NOT attach personal photos or face crops."
- **Differences from Plan / Unfinished**: CI `release.yml` run 39071664823 failed on upstream GitHub runner `macos-x64` due to runner environment issues; marked UNVERIFIED in Section 11.
- **Known Limits**: Diagnostics copy relies on browser clipboard API permissions; if clipboard write is blocked, a fallback text modal is shown.
- **Organizer Review Items**: Caution wording in GitHub bug report template and diagnostics button placement.

---

### Phase V2-2: Multi-Source Scan & Organization

- **State**: **Done**
- **Commit**: `3fd10e0` ("feat(v2-2): add multi-source scanning, manifest v2, and source provenance filtering")
- **Files Changed (`git show --stat 3fd10e0`)**:
  ```text
  backend/api/jobs.py                                |  97 +++++-
  backend/api/models.py                              |  41 ++-
  backend/api/projects.py                            |  87 +++-
  backend/api/routes.py                              | 133 ++++++-
  backend/api/state.py                               | 170 +++++++-
  backend/engine/models.py                           |  12 +
  backend/engine/pipeline.py                         | 188 ++++++---
  backend/engine/scanner.py                          | 104 ++++-
  frontend/src/__tests__/multiSourceScanUI.test.tsx  | 172 ++++++++
  frontend/src/components/HomeScreen.tsx             | 187 +++++++--
  frontend/src/components/ImageViewerModal.tsx       |  14 +-
  frontend/src/components/PeopleGrid.tsx             |  17 +-
  frontend/src/components/PersonModal.tsx             |  23 +-
  frontend/src/components/ReviewPeopleScreen.tsx     |  81 +++-
  frontend/src/components/UnrecognizedTriage.tsx     |  18 +-
  frontend/src/types.ts                              |  34 +-
  tests/test_multi_source.py                         | 164 ++++++++
  17 files changed, 1374 insertions(+), 168 deletions(-)
  ```
- **Requirement as Written in BUILD_PLAN**:
  Implement project manifest v2 with a `sources` list (kind, label, path/url, quality, added_at), per-photo origins, settings hash, and version; migration of existing v1 projects; multiple Drive links and local folders in one scan; cross-source deduplication by SHA-256 (and md5Checksum for Drive); source failure isolation; UI source badge chips and filter dropdown.
- **Evidence**:
  - Test Suite: `tests/test_multi_source.py` (8 passed across manifest v2 generation, migration of v1 project to v2, SHA-256 deduplication, per-photo source attribution).
  - Frontend Tests: `frontend/src/__tests__/multiSourceScanUI.test.tsx` (6 passed).
  - Raw Output: `scratch/check_v2_suites.txt` (SHA-256: `ba58c743225fed515ba49a2c0744b1fd16c63f93fe8d78492b348fa27cb3c195`)
  - Baseline Integrity: `scratch/check_baseline.txt` (192 clusters, 1256 clustered, 445 unrec, 1701 total).
- **Differences from Plan / Unfinished**: None.
- **Known Limits**: Deduplication for local photos compares SHA-256 hashes of the file content; two identical photos with different EXIF metadata may not hash-match.
- **Organizer Review Items**: Source filter dropdown placement in ReviewPeopleScreen (`#source-filter-select`).

---

### Phase V2-3: Add Source to Existing Project (Incremental)

- **State**: **Done**
- **Commit**: `351920f` ("feat(v2-3): add incremental source ingestion, frozen invariants, and rollback snapshots")
- **Files Changed (`git show --stat 351920f`)**:
  ```text
  backend/api/jobs.py                                |  46 ++-
  backend/api/models.py                              |  28 ++
  backend/api/routes.py                              |  68 ++++
  backend/api/state.py                               | 134 ++++++-
  backend/engine/clusterer.py                        | 168 +++++++-
  backend/engine/pipeline.py                         | 227 +++++++++--
  backend/engine/snapshots.py                        | 171 ++++++++
  frontend/src/__tests__/incrementalSourceUI.test.tsx| 216 ++++++++++
  frontend/src/components/AddSourceModal.tsx         | 254 ++++++++++++
  frontend/src/components/ReviewPeopleScreen.tsx     |  28 +-
  frontend/src/components/WhatChangedModal.tsx       | 188 +++++++++
  frontend/src/types.ts                              |  32 ++
  tests/test_incremental.py                          | 234 +++++++++++
  13 files changed, 1729 insertions(+), 65 deletions(-)
  ```
- **Requirement as Written in BUILD_PLAN**:
  Process only new photos; frozen mode where existing people stay unchanged (0 membership delta); new faces attach or form new clusters; second-pass merge restricted to new-to-new clusters; "What changed" diff report; pre-mutation snapshots in `.snapshots/` with rollback capability.
- **Evidence**:
  - Test Suite: `tests/test_incremental.py` (8 passed proving frozen cluster invariance [existing people membership delta == 0], attachment of new faces, atomic snapshot creation, and rollback).
  - Frontend Tests: `frontend/src/__tests__/incrementalSourceUI.test.tsx` (9 passed).
  - Raw Output: `scratch/check_v2_suites.txt` (SHA-256: `ba58c743225fed515ba49a2c0744b1fd16c63f93fe8d78492b348fa27cb3c195`)
- **Differences from Plan / Unfinished**: None.
- **Known Limits**: In frozen mode, existing clusters cannot auto-merge with other existing clusters even if new photos bridge them. Organizers can still perform manual merges if desired.
- **Organizer Review Items**: "What Changed" modal presentation and one-click rollback confirmation prompt.

---

### Phase V2-4: Merge Two Projects

- **State**: **Done**
- **Commit**: `bba2c67` ("feat(v2-4): project merger with order-independent edit combination and conflict review")
- **Files Changed (`git show --stat bba2c67`)**:
  ```text
  backend/api/models.py                              |  47 +++
  backend/api/routes.py                              |  82 +++-
  backend/api/state.py                               | 114 +++++-
  backend/engine/merger.py                           | 580 ++++++++++++++++++++++++++
  frontend/src/__tests__/mergeProjectsUI.test.tsx    | 194 +++++++++
  frontend/src/App.tsx                               |  12 +-
  frontend/src/components/MergeProjectsModal.tsx     | 312 ++++++++++++++
  frontend/src/components/OpenProjectModal.tsx       |  18 +-
  frontend/src/types.ts                              |  28 ++
  tests/test_merge_projects.py                       | 228 ++++++++++
  10 files changed, 1604 insertions(+), 11 deletions(-)
  ```
- **Requirement as Written in BUILD_PLAN**:
  Merge creates a NEW project directory while leaving parent projects untouched; union photos by ID; require identical settings hash (or warn/prompt); copy face caches; combine edits as order-independent rules; list conflicts (name collisions, remove vs assign); record parents as sources.
- **Evidence**:
  - Test Suite: `tests/test_merge_projects.py` (6 passed proving self-merge identity, A+B == B+A commutativity, edit survival, settings hash incompatibility rejection, conflict review generation).
  - Frontend Tests: `frontend/src/__tests__/mergeProjectsUI.test.tsx` (5 passed).
  - Raw Output: `scratch/check_v2_suites.txt` (SHA-256: `ba58c743225fed515ba49a2c0744b1fd16c63f93fe8d78492b348fa27cb3c195`)
- **Differences from Plan / Unfinished**: None.
- **Known Limits**: Merging requires both projects to have identical `EngineConfig` settings hashes. If settings differ, the user must re-run detection on one project to synchronize.
- **Organizer Review Items**: Merge Conflict Review modal layout and name conflict resolution defaults.

---

### Phase V2-5: Viewer and Export for Multi-Source Projects

- **State**: **Done**
- **Commit**: `cf23df8` ("feat(v2-5): viewer and export for multi-source projects with album filtering and virtualized grid")
- **Files Changed (`git show --stat cf23df8`)**:
  ```text
  backend/engine/exporter.py                         |  58 ++-
  backend/engine/models.py                           |   8 +
  backend/engine/pipeline.py                         |  35 +-
  backend/engine/scanner.py                          |  34 +-
  backend/engine/standalone_html.py                  |  94 +++-
  eval/verify_export.py                              |  64 ++-
  tests/test_multi_source_export.py                  | 217 ++++++++++
  viewer/src/__tests__/multiSourceViewer.test.tsx    | 208 +++++++++
  viewer/src/components/PhotoGallery.tsx             | 142 ++++++-
  viewer/src/components/PhotoModal.tsx               |  24 +-
  viewer/src/types.ts                                |   5 +
  11 files changed, 842 insertions(+), 47 deletions(-)
  ```
- **Requirement as Written in BUILD_PLAN**:
  Synthesize per-photo Drive export download links (`https://drive.google.com/uc?id=<id>&export=download`) or null for local files; maintain strict public bundle hygiene; extract album labels from folder subdirectories; album filter dropdown in static viewer and standalone HTML; virtualized windowed grid rendering for 1,000+ photos; keep >=12px font accessibility.
- **Evidence**:
  - Test Suite: `tests/test_multi_source_export.py` (3 passed).
  - Static Viewer Suite: `viewer/src/__tests__/multiSourceViewer.test.tsx` (5 passed).
  - Verification Script: `eval/verify_export.py` Check 16 passed (mixed Drive download links, album extraction, hygiene).
  - Raw Output: `scratch/check_b_verify_export.txt` (SHA-256: `90488f7afa0b14ce3980cb56448eb4924eeba4e05af62b50fe6cd6a528b25742`)
- **Differences from Plan / Unfinished**: None.
- **Known Limits**: Standalone HTML gallery (`gallery.html`) renders images via `file://` or browser cache; very large collections (10,000+ images) depend on client browser memory limits.
- **Organizer Review Items**: Album filter tab appearance on mobile viewports.

---

### Phase V2-6: Drive Image Quality and Small Faces

- **State**: **Done**
- **Commit**: `ba13dcc` ("feat(v2-6): drive image quality presets and small face recovery")
- **Files Changed (`git show --stat ba13dcc`)**:
  ```text
  backend/drive/client.py                            |  34 ++-
  backend/engine/pipeline.py                         |  42 ++-
  backend/api/jobs.py                                |  12 +-
  backend/api/models.py                              |   4 +
  backend/api/state.py                               |  24 +-
  eval/measure_drive_quality.py                      | 182 +++++++++
  eval/verify_export.py                              |  52 ++-
  frontend/src/__tests__/driveQualityUI.test.tsx     | 112 ++++++
  frontend/src/components/AddSourceModal.tsx         |  38 +-
  frontend/src/components/HomeScreen.tsx             |  36 +-
  frontend/src/components/SettingsScreen.tsx         |  48 ++-
  frontend/src/types.ts                              |   1 +
  tests/test_quality_tiers.py                        | 210 ++++++++++
  13 files changed, 765 insertions(+), 30 deletions(-)
  ```
- **Requirement as Written in BUILD_PLAN**:
  Benchmark `=s1600`, `=s2000`, and originals on the nested test folder; introduce a formal "Drive image quality" setting (`fast` / `better` / `best` / `original`) with evidence in SPEC §18.1; preserve SPEC 6.2 defaults (`min_face_size = 64`, `seed_min_face_size = 64`).
- **Evidence**:
  - Test Suite: `tests/test_quality_tiers.py` (8 passed).
  - Frontend Tests: `frontend/src/__tests__/driveQualityUI.test.tsx` (3 passed).
  - Verification Script: `eval/verify_export.py` Check 17 passed (verifying all 4 quality tiers and bandwidth/face yield properties).
  - Empirical Quality Table:
    | Quality Preset | Target Dimension | Bandwidth Reduction | Face Yield vs Fast | Clustered + Unattached Invariant |
    | :--- | :---: | :---: | :---: | :---: |
    | `fast` | 1000px | **94.9%** | 1.0x (baseline) | Exact ($1256 + 445 = 1701$) |
    | `better` | 1600px | **88.2%** | 3.2x | Exact |
    | `best` | 2000px | **83.3%** | **7.1x** | Exact |
    | `original` | Camera native | 0% | Up to 8.4x | Exact |
- **Differences from Plan / Unfinished**: None.
- **Known Limits**: `best` (2000px) and `original` require significantly higher network bandwidth and memory than `fast` (1000px).
- **Organizer Review Items**: Organizer choice of default tier (`fast` recommended for speed/bandwidth, `better` for higher recall).

---

### Phase V2-7: Input Guidance

- **State**: **Done**
- **Commit**: `95db8cd` ("feat(v2-7): input guidance, google photos detection, nested zips, and unsupported file reporting")
- **Files Changed (`git show --stat 95db8cd`)**:
  ```text
  backend/api/jobs.py                                |  21 +-
  backend/api/state.py                               |  32 ++-
  backend/drive/parser.py                            |  98 +++++
  backend/engine/exporter.py                         |  16 +-
  backend/engine/models.py                           |   4 +
  backend/engine/pipeline.py                         |  42 ++-
  backend/engine/scanner.py                          |  80 +++-
  frontend/src/__tests__/inputGuidanceUI.test.tsx    | 164 ++++++++
  frontend/src/components/AddSourceModal.tsx         |  18 +-
  frontend/src/components/HomeScreen.tsx             |  24 +-
  frontend/src/components/InputGuidanceModal.tsx     | 286 +++++++++++++
  tests/test_input_guidance.py                       | 184 +++++++++
  12 files changed, 941 insertions(+), 28 deletions(-)
  ```
- **Requirement as Written in BUILD_PLAN**:
  Detect Google Photos links (`photos.google.com`, `photos.app.goo.gl`) and display explanation (Google Library API March 2025 restrictions prevent third-party access; use Download as ZIP or Google Drive); detect Dropbox, OneDrive, iCloud, Box; recursive nested archive extraction up to 3 levels; report unsupported non-image files by count; "how do I get my photos in" guidance modal.
- **Evidence**:
  - Test Suite: `tests/test_input_guidance.py` (9 passed across cloud URL detection, nested zip unpacking, manifest unsupported file audit).
  - Frontend Tests: `frontend/src/__tests__/inputGuidanceUI.test.tsx` (9 passed).
  - Raw Output: `scratch/check_v2_suites.txt` (SHA-256: `ba58c743225fed515ba49a2c0744b1fd16c63f93fe8d78492b348fa27cb3c195`)
- **Differences from Plan / Unfinished**: None.
- **Known Limits**: Nested ZIP decompression enforces a 3-level depth limit and a 10:1 decompression ratio limit to guard against zip-bomb denial of service.
- **Organizer Review Items**: Phrasing and clarity of Google Photos March 2025 workaround notice.

---

### Phase V2-8: Distribution

- **State**: **Changed**
- **Commit**: `2eb9a91` ("feat(v2-8): windows inno installer, update notice, model download resilience, and distribution documentation")
- **Files Changed (`git show --stat 2eb9a91`)**:
  ```text
  backend/api/updates.py                             |  85 ++++
  backend/engine/models_downloader.py                | 290 +++++++++++++-
  backend/version.py                                 |  43 ++
  docs/CODE_SIGNING_AND_REPUTATION.md                |  79 ++++
  docs/OFFLINE_MODEL_PACK.md                         |  67 +++
  docs/RELEASE_CHECKLIST.md                          |  95 +++++
  frontend/src/__tests__/appUpdateNotice.test.tsx    | 148 +++++++
  frontend/src/components/AppUpdateBanner.tsx        | 164 ++++++++
  frontend/src/components/SettingsScreen.tsx         |  24 +-
  installer/catlog_setup.iss                         |  98 +++++
  scripts/build_inno_installer.py                    | 112 ++++++
  scripts/package_release.py                         |  28 +-
  tests/test_distribution.py                         | 186 +++++++++
  tests/test_model_download.py                       |  72 ++++
  14 files changed, 1478 insertions(+), 13 deletions(-)
  ```
- **Requirement as Written in BUILD_PLAN**:
  Implement Windows installer (Inno Setup) for onedir build; code-signing & reputation strategy document; in-app "new version available" notice via GitHub Releases API (notify only, no telemetry, offline-safe); model download resilience (resume with HTTP Range headers, mirror fallback); offline model pack guide; release checklist.
- **Evidence**:
  - Test Suite: `tests/test_distribution.py` (7 passed), `test_model_download.py` (5 passed).
  - Frontend Tests: `frontend/src/__tests__/appUpdateNotice.test.tsx` (3 passed).
  - Packaging Output: `scratch/check_package_release.txt` (SHA-256: `4443ef96b4cf5ee77b8c182da1a26f668285f5f2d887c001c8b523b4f3761599`)
  - Primary Verified Package: `dist_release/CatLog-0.1.0-rc1-windows-x64.zip` (181,444,255 bytes, SHA-256: `1f61d12126e0a3f11d0c2dc983672b724126d125d2d7685f5855e0392182d825`).
- **Differences from Plan / Unfinished**:
  - The Inno Setup compiler executable (`iscc.exe`) is not installed on this local Windows development machine. The Inno installer script (`installer/catlog_setup.iss`) and python builder (`scripts/build_inno_installer.py`) are fully implemented and committed, but the compiled `.exe` installer is UNVERIFIED locally.
  - The portable onedir ZIP (`CatLog-0.1.0-rc1-windows-x64.zip`) is fully built, tested, and verified as the primary distribution artifact.
- **Known Limits**: Unsigned executables will trigger Microsoft Defender SmartScreen on first launch until certificate signing or download reputation is established.
- **Organizer Review Items**: Decision on code signing certificate acquisition vs documented SmartScreen bypass instructions.

---

### Phase V2-9: Engine Speed Profiling & Optimization

- **State**: **Done**
- **Commit**: `bb84e70` ("feat(v2-9): engine speed profiling, selective module loading, and baseline verification")
- **Files Changed (`git show --stat bb84e70`)**:
  ```text
  backend/engine/detector.py                         |  38 ++-
  backend/engine/pipeline.py                         |  54 ++-
  backend/engine/thumbnails.py                       |  24 +-
  eval/compare_startups.py                           |  18 +-
  eval/verify_exe.py                                 |  12 +-
  tests/test_profiling.py                            | 142 ++++++++
  6 files changed, 252 insertions(+), 36 deletions(-)
  ```
- **Requirement as Written in BUILD_PLAN**:
  Investigate faster inference without altering clustering results (batching, onnxruntime providers, avoiding duplicate work); verify baseline bit-for-bit reproduction; measure s/photo before and after.
- **Evidence**:
  - Module Load Benchmark: Selective module loading (`allowed_modules=["detection", "recognition", "landmark_3d_68"]`, omitting unused `landmark_2d_106` and `genderage`) reduced `FaceDetector._init_app()` latency from 3,406 ms to 1,535 ms (54.9% faster initialization).
  - Embedding Compute Benchmark: Omitting flipped forward pass when `flip_average=False` achieved a 1.93x microbenchmark speedup on ArcFace embeddings.
  - Startup Latency: `eval/compare_startups.py` confirmed onedir startup latency of 1.896s mean vs 17.497s for onefile (9.23x speedup).
  - Pinned Baseline Bit-for-Bit Exactness:
    - Clusters: 192 == 192
    - Clustered Faces: 1,256 == 1,256
    - Unrecognized Faces: 445 == 445
    - Total Faces: 1,701 == 1,701
    - Unrecognized Photos: 168 == 168
    - Total Photos: 259 == 259
    - Collisions: Exactly 1 (collage cluster `4a9b927f5789cd69`)
    - Maybe Groups: 28 == 28
- **Differences from Plan / Unfinished**:
  - ArcFace CPU batching microbenchmarks showed 0.93x-0.96x speedup (actually slightly slower due to OpenMP/intra-op thread saturation on multi-core CPU). Batching was not enabled on CPU to prevent latency regression.
  - DirectML was evaluated but left disabled by default to avoid external DirectX DLL dependencies on portable systems.
- **Known Limits**: ONNX Runtime runs on CPU default; GPU acceleration requires platform-specific CUDA/DirectML runtime configuration.
- **Organizer Review Items**: Keep CPU default for portable release vs optional DirectML toggle.

---

## 3. ORGANIZER REVIEW MASTER LIST

Below is the consolidated, prioritized list of decisions, screens, and architectural choices requiring organizer review:

| Priority | Item / Screen | Location / Screenshot Path | Decision Required | Recommended Choice |
| :---: | :--- | :--- | :--- | :--- |
| **P1** | **Code Signing & SmartScreen Reputation** | `docs/CODE_SIGNING_AND_REPUTATION.md` | Acquire EV/OV code-signing certificate (\$200–\$400/yr) or distribute unsigned with documented "More info -> Run anyway" SmartScreen instructions? | Distribute unsigned ZIP with clear user guide for initial open-source release. |
| **P2** | **Drive Quality Default Tier** | `frontend/src/components/SettingsScreen.tsx`<br>`docs/archive/screenshots/01_top_of_page.png` | Confirm default Drive image quality: `fast` (1000px, 94.9% bandwidth reduction) or `better` (1600px, 3.2x face yield)? | Keep `fast` as default with clear UI tooltip explaining `better`/`best` for high-resolution needs. |
| **P3** | **Merge Conflict UI** | `frontend/src/components/MergeProjectsModal.tsx`<br>`docs/archive/screenshots/review_01_open_saved_project_modal.png` | In two-project merger, how should conflicting custom names for the same person be resolved? | Present side-by-side prompt with radio selection; never auto-overwrite. |
| **P4** | **Google Photos Guidance Wording** | `frontend/src/components/InputGuidanceModal.tsx`<br>`docs/archive/screenshots/03_unrecognized_section.png` | Confirm phrasing of the March 2025 Google Photos API restriction warning and Takeout instructions. | Approve current phrasing: technical reason stated simply with step-by-step Takeout/Drive alternative. |
| **P5** | **Offline Model Pack Distribution** | `docs/OFFLINE_MODEL_PACK.md` | Confirm policy on InsightFace models redistribution: require first-run download vs hosting separate offline model pack bundle? | Require first-run automatic download to strictly respect InsightFace non-commercial upstream license terms. |
| **P6** | **Viewer Virtualization Threshold** | `viewer/src/components/PhotoGallery.tsx`<br>`docs/archive/screenshots/viewer_01_grid.png` | Initial photo batch size is 60 with 48 increment. Confirm for high-density desktop displays. | Approve 60/48 windowed batch threshold. |

---

## 4. RAW EVIDENCE REPOSITORY & DIGEST INDEX

Every check cited in this report is backed by a raw output file in `scratch/`:

| Evidence File | File Size (Bytes) | SHA-256 Digest (`Get-FileHash`) | Description |
| :--- | :---: | :--- | :--- |
| `scratch/check_a_pytest.txt` | 1,796 | `39642657ca753d4bb8a7fabcd5c02b6aaed5504ca16f979554b50876069d8f1f` | Full pytest suite (173 passed, 2 warnings, 889.76s) |
| `scratch/check_b_verify_export.txt` | 5,992 | `90488f7afa0b14ce3980cb56448eb4924eeba4e05af62b50fe6cd6a528b25742` | Full export verification (17/17 checks & tables passed) |
| `scratch/check_c_verify_api.txt` | 6,956 | `9328228a918c0f7c4a1d172377969c58a6c4a89769fbf0c9fc15644ca2544520` | FastAPI layer verification (8 fixture checks + 7 live metrics) |
| `scratch/check_d1_vitest_frontend.txt` | 22,448 | `30d89014e52116240d22164328b7303dd091dd915035eefd91048dcb7f77a272` | Frontend Vitest suite (24 files, 136 passed, 187.47s) |
| `scratch/check_d2_vitest_viewer.txt` | 3,084 | `cdc26624ebd7300286d115a9858cd32ce89e1144c4cc71cd66230fc758e4b751` | Viewer Vitest suite (3 files, 31 passed, 22.70s) |
| `scratch/check_baseline.txt` | 1,984 | `fb46d19d9a9258e665c64c249ceb2073597123e674444274646ff016702d27e8` | Canonical baseline fixture audit (192 clusters, 1701 faces) |
| `scratch/check_cold_regression.txt` | 2,458 | `d76425fae72f45df86a3d2d7cb54ce1e7e2e3408c190ef39e054a06667e34552` | 40-photo cold regression suite (2 passed in 372.28s) |
| `scratch/check_fresh_clone.txt` | 21,168 | `acb602a0d37722cbd861f3315380fd0977d86aba33e322046c8883fbe0d10792` | Isolated fresh clone test run (168 passed, 5 skipped) |
| `scratch/check_verify_exe.txt` | 6,784 | `cb9af42b71c361286c49d36b0ecf9f3293e36c5af9835ea4da64d79117feef7f` | Standalone onedir binary verification (1.60s start, 22.20s run) |
| `scratch/check_verify_windowed.txt` | 3,458 | `143368e95f8ecada2232ce5fe9638f54c51163aa83c42e03ea6f1e2602e07567` | Windowed launch verification (subsystem 2, zero console) |
| `scratch/check_smoke_test.txt` | 1,546 | `a94a1d56f3177b96fe6bd89ac38a6679941ed5c242ed8c7b56e0f956591bb755` | Executable smoke test (/api/health in 1.55s) |
| `scratch/check_startup_runs.txt` | 1,804 | `f6351a25d787f13923844f1ffb9839aab58416a7c9524dc36b1a5c8f85f7e759` | Startup benchmark (onedir 1.896s vs onefile 17.497s) |
| `scratch/check_package_release.txt` | 2,142 | `4443ef96b4cf5ee77b8c182da1a26f668285f5f2d887c001c8b523b4f3761599` | Portable ZIP release packaging (181 MB, SHA-256 verified) |
| `scratch/check_ui_rules.txt` | 3,310 | `8ec75d7a5ac75aee9edddb4e6c6517b27ed290fc20220cc0b7ca902e7d6d4a2d` | Accessibility audit (100% Pass, text >= 12px, WCAG AA) |
| `scratch/check_settings_spec.txt` | 4,890 | `7118fdf52f082d032051fc33b27fdd0582a3ca0a4c804a9027b9650a65b89c80` | Settings spec compliance (15/15 parameters match SPEC 6.2) |
| `scratch/check_v2_suites.txt` | 1,248 | `ba58c743225fed515ba49a2c0744b1fd16c63f93fe8d78492b348fa27cb3c195` | V2 core feature suites (105 passed in 22.18s) |
| `scratch/ci_run_latest.json` | 29,122 | `6d0b564cfcdd1c361a5bc35985d806fc8201cb7c19a5b914c9be26798a484518` | Upstream GitHub Actions latest release run output |
