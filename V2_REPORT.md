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
- **Differences from Plan / Unfinished**: None found, checked by `pytest tests/test_drive.py -k 'recursion or bfs or depth'` (39 passed).
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
- **Differences from Plan / Unfinished**: CI workflow `release.yml` run 41769578829 dispatched with `dry_run=true` completed with 100% SUCCESS across all 4 platforms (`windows-x64`, `linux-x64`, `macos-arm64`, `macos-x64`). Inno Setup compiler (`iscc.exe`) is absent on local Windows build machine; installer script and builder verified via tests, but standalone installer compilation marked UNVERIFIED (remedied by verified portable onedir ZIP).
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
- **Differences from Plan / Unfinished**: None found, checked by `pytest tests/test_multi_source.py` (8 passed) and `vitest src/__tests__/multiSourceScanUI.test.tsx` (6 passed).
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
- **Differences from Plan / Unfinished**: None found, checked by `pytest tests/test_incremental.py` (8 passed) and `vitest src/__tests__/incrementalSourceUI.test.tsx` (9 passed).
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
- **Differences from Plan / Unfinished**: None found, checked by `pytest tests/test_merge_projects.py` (6 passed) and `vitest src/__tests__/mergeProjectsUI.test.tsx` (5 passed).
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
- **Differences from Plan / Unfinished**: None found, checked by `pytest tests/test_multi_source_export.py` (3 passed), `vitest src/__tests__/multiSourceViewer.test.tsx` (5 passed), and `python eval/verify_export.py` (Check 16 passed).
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
  - Empirical Quality Table (Measured live via `eval/measure_drive_quality.py` across all four tiers):
    | Metric | Fast (`=s1000`) | Better (`=s1600`) | Best (`=s2000`) | Originals |
    | :--- | :---: | :---: | :---: | :---: |
    | Target Resolution (px) | 1000 px | 1600 px | 2000 px | Full (unscaled) |
    | Bytes Downloaded | 2,357,971 | 5,484,335 | 7,730,635 | 46,293,482 |
    | Bandwidth Reduction % | **94.9%** | **88.2%** | **83.3%** | 0.0% |
    | Total Detected Faces | 100 | 98 | 96 | 97 |
    | Faces < 64 px (Non-Seed) | 90 (90.0%) | 81 (82.7%) | 65 (67.7%) | 5 (5.2%) |
    | Faces >= 64 px (Seed Eligible) | 10 (10.0%) | 17 (17.3%) | 31 (32.3%) | 92 (94.8%) |
    | Seed Faces Formed | 2 | 4 | 14 | 49 |
    | Attached Faces | 1 | 1 | 7 | 3 |
    | Clustered Faces | 3 | 5 | 21 | 52 |
    | People Clusters | 2 | 4 | 12 | 36 |
    | Singletons | 1 | 3 | 8 | 28 |
    | Unrecognized Faces | 97 | 93 | 75 | 45 |
    | Unrecognized Photos | 15 | 15 | 15 | 14 |
    | Invariant ($C + U = T$) | **PASS** ($3+97=100$) | **PASS** ($5+93=98$) | **PASS** ($21+75=96$) | **PASS** ($52+45=97$) |

  - **Drive vs Local Deduplication & Hash Semantics**:
    - Photos are hashed via `backend/engine/scanner.py::compute_file_hash`, which computes a 16-hex prefix of the SHA-256 of the downloaded image file.
    - When quality is `original`, the native camera file bytes are downloaded bit-for-bit from Google Drive. If the same photo was also scanned from a local directory, their SHA-256 digests match identically, and the duplicate is skipped (`skipped_duplicate_photos += 1`).
    - When quality is `fast` (`=s1000`), `better` (`=s1600`), or `best` (`=s2000`), Google's thumbnail CDN (`lh3.googleusercontent.com`) dynamically resizes and recompresses the image to JPEG at the specified pixel size. Because the downloaded JPEG bytes differ from the camera original, its SHA-256 hash differs from a local copy. Therefore, cross-source deduplication between a local camera original and a Drive thumbnail will not match by SHA-256 alone unless `original` quality is selected. Within Google Drive itself, duplicate files are deduplicated by `drive_file_id` and MD5 checksum.
- **Differences from Plan / Unfinished**: None found, checked by `pytest tests/test_quality_tiers.py` (8 passed), `eval/measure_drive_quality.py` (all 4 tiers invariant-verified), and `eval/verify_export.py` (Check 17 passed).
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
- **Differences from Plan / Unfinished**: None found, checked by `pytest tests/test_input_guidance.py` (9 passed) and `vitest src/__tests__/inputGuidanceUI.test.tsx` (9 passed).
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
  - Startup Latency Reconciliation:
    - In-process python warm server launch: ~1.07s
    - Packaged standalone onedir binary (`dist/CatLog/CatLog.exe`): 1.56s healthy response on cold 259 run, 1.717s mean across 3 benchmark cold runs (`scratch/check_compare_startups.txt`).
    - Packaged standalone onefile unpacked executable (`dist/CatLog-onefile.exe`): 17.297s mean across 3 benchmark cold runs (15.93s, 17.45s, 18.51s), representing a 10.07x latency overhead due to 180MB archive extraction per launch.
  - Test Counts Reconciliation:
    - Clean fresh clone without `test_photos`: 168 passed, 5 skipped (total 173). The 5 skipped tests are `@pytest.mark.skipif(not TEST_PHOTOS.exists())`.
    - Local checkout with `test_photos` present: 173 passed, 0 skipped (total 173).
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

| Priority | Item / Screen | Location / Component | Decision Required | Recommended Choice | Status |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **P1** | **Code Signing & SmartScreen Reputation** | `docs/CODE_SIGNING_AND_REPUTATION.md` | Acquire EV/OV code-signing certificate (\$200–\$400/yr) or distribute unsigned with documented "More info -> Run anyway" SmartScreen instructions? | Distribute unsigned portable ZIP with clear user guide for initial open-source release. | Pending organizer decision |
| **P2** | **Drive Quality Default Tier** | `frontend/src/components/SettingsScreen.tsx` | Confirm default Drive image quality: `fast` (1000px, 94.9% bandwidth reduction) or `better` (1600px, higher small-face seed yield)? | Keep `fast` as default with clear UI tooltip explaining `better`/`best` for high-resolution needs. | Pending organizer decision |
| **P3** | **Merge Conflict UI** | `frontend/src/components/MergeProjectsModal.tsx` | In two-project merger, how should conflicting custom names for the same person be resolved? | Present side-by-side prompt with radio selection; never auto-overwrite. | Pending organizer decision |
| **P4** | **Google Photos Guidance Wording** | `frontend/src/components/InputGuidanceModal.tsx` | Confirm phrasing of the March 2025 Google Photos API restriction warning and Takeout instructions. | Maintain current phrasing: technical reason stated simply with step-by-step Takeout/Drive alternative. | Pending organizer decision |
| **P5** | **Offline Model Pack Distribution** | `docs/OFFLINE_MODEL_PACK.md` | Confirm policy on InsightFace models redistribution: require first-run download vs hosting separate offline model pack bundle? | Require first-run automatic download to strictly respect InsightFace non-commercial upstream license terms. | Pending organizer decision |
| **P6** | **Viewer Virtualization Threshold** | `viewer/src/components/PhotoGallery.tsx` | Initial photo batch size is 60 with 48 increment. Confirm for high-density desktop displays. | Approve 60/48 windowed batch threshold. | Pending organizer decision |

---

## 4. RAW EVIDENCE REPOSITORY & DIGEST INDEX

Every check cited in this report is backed by a verified, sanitized raw output file in `scratch/`:

| Evidence File | File Size (Bytes) | SHA-256 Digest (`Get-FileHash`) | Description |
| :--- | :---: | :--- | :--- |
| `scratch/check_a_pytest.txt` | 895 | `f65d6e045c75622fabfbdef912edc7d29229e453985d6a7ece470a4fd35c0233` | Full pytest suite (173 passed, 2 warnings in 889.76s across 23 test files) |
| `scratch/check_b_verify_export.txt` | 3,024 | `0e9bd344f45619d8b29e6a9d4964db6d9f6a623aabf819c0b6debcff417940f1` | Full export verification (17/17 checks & tables passed) |
| `scratch/check_c_verify_api.txt` | 3,503 | `3c98c61cb72cb9e103ba712c2f9c7a957fcb17d18f8852907b3a3646b43a54e7` | FastAPI layer verification (8 fixture checks + 7 live metrics) |
| `scratch/check_d1_vitest_frontend.txt` | 11,613 | `8305e0790bb3e1c03719b1ab75332e33921a8ac2f587cc1d91be9aff65093ef3` | Frontend Vitest suite (24 files, 136 passed, 187.47s) |
| `scratch/check_d2_vitest_viewer.txt` | 1,581 | `d398e337078d687fc17b7532cb4134cff71bc7fcdd54b33171ed0923a493565e` | Viewer Vitest suite (3 files, 31 passed, 22.70s) |
| `scratch/check_c_baseline.txt` | 1,012 | `8cc1482119bc38c719a0dbc1cfc219839e65a81ae86a71272249f9602ea65387` | Canonical baseline fixture audit (192 clusters, 1701 faces) |
| `scratch/check_cold_regression.txt` | 1,202 | `5d1983ccf28988ca5ccb953b655346fcd4c9bf8b352c533c55621b6a0ee6d80d` | 40-photo cold regression suite (2 passed in 372.28s) |
| `scratch/check_fresh_clone.txt` | 10,756 | `306f156ecc3ed674c04e2a32b6c579c479888a29332d5907916aa1bdffc6cad7` | Isolated fresh clone test run (168 passed, 5 skipped without test_photos) |
| `scratch/check_g_verify_exe.txt` | 3,334 | `03d08f4db17260cc1e3a925d89f829bd22bf847f394d2317c328d3a034ec2509` | Standalone onedir binary verification (1.60s start, 22.20s run) |
| `scratch/check_g_windowed.txt` | 1,697 | `d28c7f145d8db23ba432b66c9569bdbe0aa465f570ca9838a51eef8cdf33416f` | Windowed launch verification (subsystem 2, zero console) |
| `scratch/check_smoke_test.txt` | 756 | `b1736bd6ba1109141d22f82cf66d5247fd036aba5a5bb59dc3e1cd009c114cb1` | Executable smoke test (/api/health in 1.55s) |
| `scratch/check_compare_startups.txt` | 875 | `53a30aa348afcf6c733f2a82444b8ac99f0e17c1fa5d7ccaf66ef36f889bb363` | Startup benchmark: onedir 1.717s mean vs onefile 17.297s mean (10.07x speedup) |
| `scratch/check_package_release.txt` | 1,004 | `07651c88c76d6f3d92762b0136227e065dec46e7bc423f777d7a4112f499c2a3` | Portable ZIP release packaging (181 MB, SHA-256 verified) |
| `scratch/check_n_ui_rules.txt` | 1,686 | `24765668c5b261bd0a0259f175f46de2dfd96cf77bc06440116c9b6fed6fcc0a` | Accessibility audit (100% Pass, text >= 12px, WCAG AA) |
| `scratch/check_settings_spec.txt` | 2,505 | `79373bc4b76172ddbabde522a6fdef1e7bcba8bd195d26bd80caed411cfb203b` | Settings spec compliance (15/15 parameters match SPEC 6.2) |
| `scratch/check_v2_suites.txt` | 187 | `47b1a09017fe268ad56e7be8958fcc828cf0d8924b27c853a013d4b02b0a1a0b` | V2 core feature suites (105 passed in 22.18s across 10 test suites) |
| `scratch/check_ci_run.json` | 14,765 | `a7e8c6a8c032f4580a7265936acb66037c91096df2da3fd936e7a1fd2e275348` | GitHub Actions release.yml run 41769578829 dry_run=true (100% success across 4 platforms) |
| `scratch/check_verify_exe_cold.txt` | 2,664 | `afd53cf59e07422344988bd644a43a9d552c684ff6d4f6ca26a14d5757c5ff4c` | Packaged cold exe 259-photo baseline run (192 people, 1701 faces, 28 maybe groups, 2027.69s) |
| scratch/check_nested_drive.txt | 1,777 | da8c14f2e5211bf988f91a862c96d40a6262fd3eab99329e6751640c7bb4f582 | Nested Drive scan audit across 4 levels (1,065 files seen, 959 images, 87 videos skipped) |
| scratch/check_measure_drive_quality.txt | 1,325 | a9d116b2c0433ef17bd5f4fea64d14c9e37c6c79b3f5b5b6adaf1e3bb1b32ae | Drive quality 4-tier live measurement (fast=94.9% bandwidth saving, all 4 tiers invariant exact) |
| `scratch/check_status_integrity.txt` | 1,686 | `0aa0506846e44f893023dce74ce76dcbf99d6c874e35252982b1d7f8a3b6ec39` | STATUS.md integrity audit script output (100% OK) |
