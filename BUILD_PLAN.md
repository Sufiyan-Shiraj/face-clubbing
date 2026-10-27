# PhotoSorter: Build Plan

> Read `SPEC.md` first (revision 2). This file is the order of work. Each phase ends with something runnable and a clear "done when" check. Do not start a phase until the previous one meets its check.
>
> **Revision 3 (2026-10-13).** Phase 8 (Method 2, upload to Drive, OAuth) removed; the project has no Google sign-in anywhere. Phase 5 status corrected (windowed launch and native pickers still need verification).
>
> **Revision 2 (2026-10-06).** Phases 0 and 1 are accepted. A new Phase 1b collects engine changes decided after the fix-up rounds and must finish before Phase 3. Phases 2 to 4 gained requirements from the measured clustering results.

**Principle:** build the riskiest part first (clustering quality), keep the engine UI-independent, and never require a Google sign-in (Drive is read-only through an optional API key).

## Status

| Phase | State |
|---|---|
| 0 Setup + risk check | Done |
| 1 Engine core (CLI) | Accepted (271 files / 259 unique photos / 1,701 faces tested) |
| 1b Engine amendments | Done |
| 2 Static viewer | Done |
| 2b Public viewer rework & download | Done |
| 3 API layer (FastAPI) | Done |
| 4 Organizer UI (React) | Done |
| 5 Desktop shell + first package | Done (Windowed launch, native pickers, 1.60s onedir cold start verified) |
| 6 Method 1 (Drive link) | Done (Live verification complete: 83 images, 100% thumbnails, 92% bandwidth savings, 64px floor documented in SPEC §18) |
| 6b UI redesign | Done |
| 7 Release automation | Done (Multi-platform GitHub Actions workflow, onedir packaging, SHA-256 generation) |
| 8 | Removed (2026-10-13) |
| 9 Polish / extras | Core Complete (Custom scrollbars, custom dialogs, >=12px accessibility, Section 18 Table A/B; optional extras remaining) |
| V2-0 Drive subfolder recursion | Done (BFS queue, depth 5, 20k file cap, loop prevention, file ID deduplication, resilient folder failures, scan summary) |
| V2-1 Release health & first-user fixes | Done (Counts-only diagnostics button, privacy scrubber, GitHub issue templates with caution banner, crash/error screens with plain-language fixes, README troubleshooting) |


---

## Phase 0: Setup and risk check (done)

- Repo layout from SPEC section 11, MIT `LICENSE`, `.gitignore` excluding `test_photos/`, model files, tokens, `client_secret.json`.
- Python venv with `insightface`, `onnxruntime`, `opencv-python`, `scikit-learn`.
- Real test set and a smoke script.

---

## Phase 1: Engine core (done, accepted)

Implemented in `backend/engine/`: scanner (folder/zip, stable IDs, duplicate collapse), EXIF-aware loader, detect + embed with `buffalo_l`, embedding cache, seed/attach-only clustering with strict attach rules, second-pass top-5-centroid merge with the same-photo guard, ambiguous re-attach, Unrecognized category with reason codes, crops, thumbnails, exporter (`people.json`, `suggestions.json`, `id_map.json`, `config.json`), CLI `python -m backend.engine --input <folder|zip> --out export/`.

Accepted result on the test set: 192 people (81 single-photo), 445 Unrecognized faces in 168 photos, every photo covered, 1,256 clustered + 445 unrecognized = 1,701 faces, one collision cluster (a true collage).

---

## Phase 1b: Engine amendments [DONE]

**Build**
1. **Maybe band:** set `maybe_threshold` default to 0.65 (was 0.60). Regenerate `suggestions.json` and report the new link/group counts and the distance-bin table.
2. **Stable identity:** implement the SPEC 6.3 rules in the engine.
   - Deterministic cluster ID assignment (photo count descending, ties by best-face ID).
   - `edits.json` schema and an `apply_edits()` step that replays merge/remove/assign/hide/name by face-ID anchors after every run, returning a report of any edit whose anchors could not be located.
   - Tests prove that re-running the engine with a changed config and the same `edits.json` preserves the organizer's merges.
3. **Allowlists and tests keyed by face ID.** Replace every hard-coded cluster ID (for example the collage allowlist in `verify_final.py`) with face-ID or photo-ID based rules. Move the script to `eval/verify_export.py`.
4. **Evaluation package** in `eval/`: `ground_truth.json` loader (sets + `different`), the same-photo negative generator, and a script that prints the SPEC 18 table (recall and false pairs at 0.50 to 0.80, standard and flip). Include the existing three sets.
5. **Public bundle filter:** the exporter writes the public bundle (`config.json`, `people.json`, `faces/`, `thumbs/`, plus optional viewer build `index.html`, `assets/`, and `gallery.html`) separately from organizer-only files, and never copies `suggestions.json`, `edits.json`, `id_map.json` or `.cache/` into it. Enforced in `tests/test_exporter.py` and `eval/verify_export.py` Check 2.
6. **Config:** add `hide_single_photo_default` to `config.json` (default false).
7. **Gated, not changed:** leave `flip_average` off. Add it to the evaluation table only.

**Done when**
- The CLI produces the bundle with the 0.65 maybe band and all invariants pass: every photo covered, face accounting exact, no unallowlisted same-photo collision above 0.40, public bundle contains no organizer-only files.
- The edit-replay test passes (merge two clusters by anchor faces, re-run with a different seed threshold, merge still present).
- `verify_export.py` checks every number in the report tables against the JSON and contains no cluster-ID allowlist.

**Collect in parallel (not blocking):** the organizer labels more same-person sets and some different-person pairs from different photos. Target 15+ sets. These go into `eval/ground_truth.json` as face IDs.

---

## Phase 2: Static viewer (update to SPEC 9, rev 2) [DONE]

**Build** (in `viewer/`)
1. React + Vite + Tailwind project reading `config.json` and `people.json`.
2. **One people grid** sorted by photo count, with a toolbar toggle "Hide single-photo people" (initial state from `hide_single_photo_default`). No collapsible long-tail section.
3. **Unrecognized entry** at the end: (a) grid of unrecognized face crops, each opening its photo; (b) separate list of photos with no detected face.
4. Per-person gallery with lazy-loaded thumbnails and a large preview. When `include_maybe` is true, show `maybe_photos` in a separate, labelled "Possible matches" section.
5. Download button per photo (hidden when `download` is null).
6. Theming from `config.json` (title, logo, accent, font, footer).
7. Mobile-first responsive layout.
8. Deploy test to GitHub Pages or Cloudflare Pages using a Phase 1b bundle.
9. **Standalone HTML gallery (`gallery.html`):** Single-file zero-server gallery embedded in the public bundle. Works purely via `file://` protocol with no local or web server required. Relative paths for thumbnails and face crops. Full photo reachability across all people and unrecognized photos. Download links dynamically rendered or hidden per `config.json`.
10. **Standalone gallery verification:** Automated verification opening `gallery.html` with no server, asserting every photo reachable and download links present or hidden per config.

**Done when:** a Phase 1b export dropped into the viewer works end to end on a phone and a laptop, swapping `config.json` changes the look without code changes, every photo can be reached from some screen, and `gallery.html` opens cleanly offline without a server.

---

## Phase 2b: Public Viewer & Standalone HTML Risograph Overhaul [DONE - NEEDS ORGANIZER REVIEW]

**Build** (in `viewer/`, `backend/engine/standalone_html.py`, and `frontend/src/components/ExportScreen.tsx`)
1. **Design & Theming**:
   - 3 cohesive Risograph themes: `t-dark` (Tokyo Neon), `t-paper` (Warm Risograph), `t-navy` (Blueprint) with CatLog tactile borders, offset box shadows, and responsive touch targets.
   - Brand logos and camera-cat icon (`BrandLogo.tsx`), noise textures, and 24 dynamic transparent mascot poses (`MascotSticker.tsx`).
   - Organizer export theme selection in `ExportScreen.tsx` with live preview swatches, persisted to `export/config.json`.
   - Standalone single-file HTML export (`standalone_html.py`) overhauled with all 3 themes, embedded SVG logo, interactive theme switcher buttons, and direct per-person sequential downloads (zero external dependencies).
2. **Per-Person Downloads**:
   - Direct "Download All ({count})" button on every person card in the gallery grid with live progress counter and checkmark confirmation.
   - Primary "Download all N photos" button inside person gallery showing the exact photo count.
   - Per-photo download links with sanitized `personname_001.jpg` filenames.
   - Select mode with checkbox selection on photos, "Select all" / "Deselect all", and sticky bottom action bar ("Download selected (K)").
   - **Local Export**: Client-side streaming zip built with `client-zip`, progress counter, cancel via `AbortSignal`, without buffering all photos in memory.
   - **Drive Export**: Sequential single-photo download loop reusing existing `download_url` (`https://drive.google.com/uc?id=<ID>&export=download`) with progress counter, one-time browser permission guidance note, and "Open in Drive" fallback. No server.
   - Unrecognized and maybe-match groups strictly have NO "Download all" button.
   - Fallback tiles for unavailable images and lazy loading (`loading="lazy"`).
3. **Verification & Testing**:
   - 20 Vitest unit/integration tests (`viewer.test.tsx` and `download.test.tsx`) covering filename sanitization, zero cross-person data leakage, select mode, zip streaming, Drive downloads, and config swap.
   - Headless Playwright E2E verification (`verify_download_e2e.cjs`) testing themes, selection, local zip streaming download, and Unrecognized guard.
   - Public bundle hygiene (`eval/verify_export.py` Check 2) strictly verified (zero stray root files).
   - Screenshots captured with zero real human faces saved in `scratch/screenshots/`:
     - `viewer_01_grid.png`
     - `viewer_02_person_download.png`
     - `viewer_03_select_mode.png`

**Done when:** All tests pass, local zip and Drive downloads succeed without data leaks, bundle size measured before/after, and visual design marked `NEEDS ORGANIZER REVIEW`.

---

## Phase 3: API layer (FastAPI) [DONE]

**Build** (in `backend/api/`)
1. Job manager: start the engine as a background thread/process, with cancel.
2. Endpoints:
   - start job, job status, cancel;
   - list people, list Unrecognized (faces and no-face photos);
   - **suggestions:** maybe groups and the ranked "possibly the same" list (including the extended range for single-photo people), and top-3 candidates for ambiguous faces;
   - **edits:** merge (any number of people in one call), remove face/photo from a person, assign an Unrecognized face to a person or a new person, hide, name, **undo**;
   - re-run engine **with edit replay**, returning any edits that could not be re-applied;
   - export (public bundle, excludes organizer-only files).
3. **Edits stored in `edits.json` keyed by face and photo IDs.** The API accepts cluster IDs from the UI only as handles for the current export and converts them to anchor face IDs before saving. Cluster IDs are never persisted.
4. Progress streaming over SSE (count, current file, ETA).
5. Serve built React UI at `/` (static files).
6. Settings endpoints (clustering params from SPEC 6.2, thumbnail size, output folder).

**Done when:** you can drive a full run with `curl` or a browser: start, watch progress stream, fetch people and suggestions, merge 3+ people in one call, assign an Unrecognized face, re-run, confirm the edits survived, export.

---

## Phase 4: Organizer UI (React) [DONE]

**Build** (in `frontend/` - React + Vite + Tailwind CSS + TypeScript)
1. Screens: Home (source picker with native path input, Drive link field disabled/stubbed for Phase 6), Progress (SSE bar with current, total, percent, stage, ETA, cancel), Review People (core organizer workflow), Export (preview, stats, publishing instructions), Settings (clustering params, thumb size, Drive API key field).
2. Source picker: folder/zip source path input with quick defaults, Drive link field clearly labelled "Phase 6".
3. Live progress bar from SSE streaming (`/api/jobs/{id}/progress`) with status, ETA, and cancellation.
4. **Review People**:
   - Grid of people with multi-select and multi-merge in one action (`/api/edits` merge).
   - Side-by-side **suggestion review** with both faces, photo counts, distance, and reason, supporting accept and persistent session reject.
   - Ranked low-confidence "Possibly the same" list for single-photo people.
   - Per-person controls: remove face, remove photo, hide person, rename person.
   - **Unrecognized triage**: assign face to person (displaying top-3 candidates for ambiguous faces) or create new person; photos without detected faces remain reachable.
   - Global and per-edit Undo control for every edit operation.
5. Export screen: triggers bundle export, shows public file stats, lists output folder, provides GitHub Pages and Cloudflare Pages publishing guides.
6. Settings: sensitivity slider mapping directly to SPEC 6.2 parameters (`seed_threshold`, `attach_margin`, `merge_threshold`), thumbnail size selector, API key input, and the Drive API key field (used from Phase 6). The former Method 2 credential-storage selector is removed with Phase 8.
7. Rerun clustering with edit replay and banner listing unapplied edits.
8. Reused viewer gallery components via `@viewer/components/PhotoModal`.

**Done when:** the whole local-folder workflow works in the browser against the running FastAPI app (`npm run dev` + `uvicorn` and built UI served by `uvicorn`), and the 7-way split in the test set can be merged in one action.
**Status**: **Done** (All technical requirements and e2e verification pass; organizer review of layout/wording is still pending).

---

## Phase 5: Desktop shell and first package [DONE]

**Build**
1. `main.py`: start FastAPI on a random free port in a background thread, open a pywebview window pointed at it, shut down cleanly on window close.
2. Expose native folder and file pickers to the React UI through pywebview's JS API.
3. `npm run build`; confirm FastAPI serves `dist/`.
4. `run.bat` / `run.sh` for run-from-source convenience.
5. First PyInstaller build **on Windows** (bundle code, `dist/`, and models or first-run model download).

**Done when:** double-clicking the Windows exe opens a window and completes a full run on the test set with no terminal and no localhost for the user.
**Status**: **Done** (All requirements verified; standalone `dist/CatLog/CatLog.exe` built in onedir format with 1.60s cold start, boots cleanly in windowed GUI mode without console, serves bundled React assets, exposes native pickers via `window.pywebview.api`, and executes full clustering on `test_photos` with verified export output).

---

## Phase 6: Method 1, Drive link input (no sign-in)

**Build** (in `backend/drive/`)
1. Parse folder URL/ID; list files with an API key (paginated).
2. Download size-limited thumbnails (`thumbnailLink` resized), fall back to originals; bounded parallelism, retry/backoff.
3. Feed images into the same engine pipeline; record file IDs.
4. Exporter fills `download` links (`https://drive.google.com/uc?id=<ID>&export=download`).
5. API key field in Settings, with a short guide on getting one.

**Verify early:** thumbnail availability and sizes on a public test folder, **and re-check the 64 px face-size floors and detection counts on those thumbnails** against the local-original results.

**Done when:** pasting a public Drive folder link yields a complete export with working Drive download links.  
**Status**: **Done** (All requirements verified; live Google Drive verification completed on public folder `<FOLDER_ID>` with 152 total files: 83 images, 69 videos skipped, 0 non-images, 0 subfolders. 100% thumbnail availability [83/83], 0% alt=media fallbacks [0/83], 92.1% bandwidth savings [10.15 MB vs 127.73 MB originals]. Full engine runs executed on Drive thumbnails and Drive originals; 64 px floor analysis and adaptive floor proposal documented in SPEC §18. Resumable caching [100% cache hit on second run], error sanitization [bad key 400, private folder 404, quota 403], and zero API key leakage verified. Raw evidence: `scratch/verify_drive_phase6_raw.txt` with SHA-256 `0F3C305DEE212226A8539DE59DB61C381661AE307CEC6B64A79D1A7B5879A10B`).

---

## Phase 6b: UI redesign (Risograph theme, compact triage, bboxes)

**Status:** **Complete**
- 2-stage landing flow (Risograph paper/navy palette, large single-photo dropzone, batch action bar).
- Compact unrecognized triage grid with target person preview and batch multi-select.
- Image viewer with dual-mode bounding boxes (solid cyan for selected person, dashed coral for other detected faces).
- On-canvas quick-change re-assignment popover and slide-over "Inspect faces" drawer.

---

## Feature: Open saved project

**Status:** **Complete**
- Reopen past work and export folders instantly without re-scanning source photos or re-computing embeddings.
- Sequence of persisted edits in `edits.json` restored into session edit stack with undo history restored across reopenings.
- Dynamic calculation of `exists` at listing time; `exists` is never persisted into `projects.json`.
- Automatic registration upon scan/export, 5 recovery edge cases, zero cluster ID persistence, and strict privacy sanitization.

---

## Phase 7: Release automation [DONE]

**Status:** **Complete**

**Build**
1. GitHub Actions workflow: on a version tag, build on Windows, macOS (arm64 and Intel), and Linux runners; PyInstaller each; attach artifacts to a GitHub release.
2. README: install, per-OS notes (Linux apt line, macOS right-click Open, Windows SmartScreen bypass), model license note, privacy notes.
3. Test each build on a real machine of that OS if possible.

**Done when:** pushing a tag produces downloadable builds for all three OSes, and each launches and finishes a small run.
**Status**: **Done** (Implemented multi-platform release workflow in `.github/workflows/release.yml`, package release script in `scripts/package_release.py`, SHA-256 generator in `dist_release/SHA256SUMS.txt`, version sync in `scripts/sync_version.py`, and release notes generator in `scripts/generate_release_notes.py`).

---

## Phase 8: Removed

Method 2 (upload to Drive with Google sign-in) is no longer part of the project (decision 2026-10-13). There is no OAuth, no `client_secret.json`, no credential storage, no "Sign out and erase". Organizers who want Drive download links upload the originals to Drive themselves, make the folder public, and use Method 1 (Phase 6). The phase number is kept as a gap so earlier references stay valid.

---

## Phase 9: Polish and later options [CORE COMPLETE / OPTIONAL EXTRAS REMAINING]

**Status:** **Core Complete**

- **UI & Accessibility Hardening [Complete]**: Custom tactile scrollbars (`::-webkit-scrollbar` matching Risograph design), custom modal dialogs (`CustomDialog.tsx`) for errors and active project guards, organizer theme lock, zero sub-12px font sizes (`eval/check_ui_rules.py` 100% pass), and WCAG 2.1 AA text contrast across all 3 themes.
- **Recognition Quality Experiments [Complete]**: SPEC Section 18 Tables A & B computed in `eval/recall_table.py` comparing standard vs flip-averaged embeddings and persisted to `eval/recall_false_pairs_report.json`.
- **Per-Person Streaming Downloads [Complete]**: Implemented with `client-zip` in the viewer for local exports and sequential fetch loop for Drive.
- **Optional Extras Remaining**:
  - *In-Viewer Selfie Search*: Optional experimental client-side face matching for gallery visitors.
  - *1-Click Auto-Publish to GitHub Pages*: Optional in-app button to auto-push exports via GitHub REST API.
  - *Optional bundled default Drive API key*: Dangerous to commit; kept as organizer-configured in Settings.

---

## Order at a glance

| # | Phase | Why this order |
|---|---|---|
| 0 | Setup + risk check | Confirm InsightFace works and you have real test data (Done) |
| 1 | Engine core (CLI) | Riskiest part: validate clustering quality first (Accepted) |
| 1b | Engine amendments | Stable identity and the 0.65 band must exist before an API stores edits (Done) |
| 2 | Static viewer | Proves the output format end to end (Done) |
| 2b | Public viewer overhaul | Tactile themes, mascots, per-person zip streaming, offline gallery (Done) |
| 3 | FastAPI layer | Engine becomes controllable; edits persist across re-runs (Done) |
| 4 | Organizer UI | Human review is the quality safety net, not an extra (Done) |
| 5 | Desktop shell + exe | Double-click experience on Windows (Done) |
| 6 | Method 1 (Drive link) | Second input source, no sign-in (Done) |
| 6b | UI redesign | Risograph theme, landing flow, compact triage (Done) |
| 7 | CI release builds | Cross-platform distribution (Done) |
| 8 | ~~Method 2 (upload)~~ | Removed 2026-10-13 |
| 9 | Polish / extras | Core Complete (UI accessibility, scrollbars, dialogs, Table A/B; optional extras remain) |
| - | Open saved project | Reopen past exports without re-scan (Complete) |

## Working rules for the AI building this

- Never label anyone as "noise" or drop a face or photo automatically. Everything is either in a person's cluster or in Unrecognized, and every photo is reachable.
- **Never store, compare, test, allowlist or label by cluster ID** (`pNNN`). Use face IDs and photo IDs. Cluster IDs are display labels for one export only.
- Keep the engine free of any UI or web imports so it stays runnable from the CLI.
- Never hardcode club-specific values; all theming goes through `config.json`.
- Never commit tokens, client secrets, or API keys; never embed them in builds.
- Stream photos one at a time and cache embeddings; never load the whole set into RAM.
- **Reports contain counts, IDs and filenames only.** Do not describe what an image looks like or label a merge "correct" or "false" from appearance; flag it for the organizer instead.
- **Every table in a report must be checked against the JSON by the verification script**, and the script's full output pasted into the report. A report claim that no script checks is not verified.
- Do not change any default in SPEC 6.2 without the SPEC 18 evidence table.
- When something turns out different from what SPEC.md assumes, update `SPEC.md` (and its decisions log) rather than silently diverging.


## V2 PLAN (after v0.1.0 release)

Working rules (unchanged, apply to every phase): counts/IDs/filenames only; every number script-checked with raw outputs + SHA-256; unverified = UNVERIFIED; never store/test/label by cluster ID (face and photo IDs only); no SPEC 6.2 default changes without evidence and organizer decision; never commit photos, face crops, keys or real folder IDs; no tags or releases without organizer approval; baseline (192 people, 445 unrecognized faces, 168 unrecognized photos, 259 photos, 1256+445=1701) must reproduce and the cold regression tests must pass after every phase; STATUS.md is regenerated from raw files and check_status_integrity.py must pass.

### V2-0 Drive subfolder recursion (hotfix) [DONE]
**Status:** **Done** (Implemented in `backend/drive/client.py`, `backend/engine/pipeline.py`, `backend/api/jobs.py`, `backend/api/routes.py`, `frontend/src/components/HomeScreen.tsx`. Implements iterative BFS queue traversal, max depth 5, 20,000-file cap, visited folder set for loop prevention, shortcut/non-image skipping, resilient non-fatal subfolder error handling, file-ID deduplication, unique cache names by file ID, per-photo folder path tracking, and scan summary "Found N images in M folders". 39/39 Drive tests in `tests/test_drive.py` pass).

### V2-1 Release health and first-user fixes [DONE]
**Status:** **Done** (Implemented counts-only "Copy diagnostics" report in `backend/api/diagnostics.py` with sensitive data scrubber (zero file paths, zero photos, zero API keys, zero attendee biometrics, 16-hex settings hash), classified error codes (`OFFLINE`, `QUOTA_403`, `PRIVATE_FOLDER_404`, `BAD_KEY_400`, `DISK_FULL`, `CORRUPT_INPUT`, `GENERIC_ERROR`), and plain-language actionable fixes. Integrated `CopyDiagnosticsButton.tsx` across `ProgressScreen`, `HomeScreen`, `SettingsScreen`, and `CustomDialog`. Created GitHub Issue templates with explicit caution banner in `.github/ISSUE_TEMPLATE/`. Added comprehensive troubleshooting guide to `README.md`. CI multi-platform workflow configured across windows-x64, linux-x64, macos-arm64, macos-x64. 11/11 tests in `tests/test_diagnostics.py`, 3/3 in `frontend/src/__tests__/diagnosticsAndErrors.test.tsx`, 120/120 total Pytest, 85/85 Frontend Vitest, 26/26 Viewer Vitest all green).
Build: confirm CI green on all four platforms (fix what fails); a "Copy diagnostics" button that produces a counts-only report (version, OS, settings hash, error codes, no paths, no photos, no keys); GitHub Issues template with "do not post photos"; crash/error screens with plain-language fixes (offline, quota 403, private folder 404, out of disk); README troubleshooting.
Done when: a clean machine runs the release build end to end; a deliberately broken input (bad key, private folder, offline, full disk) shows a clear message and a diagnostics report with no sensitive data.

### V2-2 Project model v2 and multi-source scan
Build: project manifest v2 with a `sources` list (kind: local/zip/drive/project, label, id or path, quality: thumbnail|original, added_at), per-photo origins, settings hash and version; migration of existing projects and projects.json; multiple Drive links (and local/zip) in one scan with per-source status; dedupe across sources by photo ID, and for Drive by md5Checksum (no download); one failing source never fails the others; optional contributor label (no personal data); Source screen showing the list of sources with per-source counts.
Done when: two Drive folders plus a zip scan into one project; a duplicate photo in two sources is processed once; old projects open unchanged; baseline reproduces.

### V2-3 Add a source to an existing project (incremental) [COMPLETED]
Build: process only new photos; frozen mode (existing people stay, new faces attach or form new people, second-pass merge rules documented); "What changed" report (new photos, new people, faces that joined existing people, existing people whose membership changed, which must be zero in frozen mode); existing edits replay as rules; undo supported.
Done when: adding a link to a finished project leaves all existing people and edits unchanged, and the review shows only the differences; tests for frozen invariants and edit survival. Verified in tests/test_incremental.py (8/8 pass) and frontend/src/__tests__/incrementalSourceUI.test.tsx (9/9 pass). Report Section 43.

### V2-4 Merge two projects
Build: merge creates a NEW project (originals untouched); union by photo ID; require equal settings hash (else offer re-detect); copy caches; combine edits as order-independent rules (merge anchors, removes, assigns, names, hides); conflict review list (name conflicts, remove vs assign), never silently resolved; the merged project records both parents as sources.
Done when: merging a project with itself changes nothing; A+B equals B+A; edits from both survive; conflicts are listed; a cold merged result is compared with an all-at-once scan and the differences are reported.

### V2-5 Viewer and export for multi-source projects
Build: per-photo download link (Drive link or none), mixed local+Drive bundles, optional album labels from Drive folder paths (viewer filter), size handling for big zips, bundle hygiene checks, viewer performance on 1,000+ photos (virtualized grid), accessibility checks stay at 100%.
Done when: a merged, mixed-source export opens offline and online, every photo reachable, downloads correct, verify_export extended and passing.

### V2-6 Drive image quality and small faces
Build: measure =s1600, =s2000 and originals on the same nested test folder (people, singletons, unrecognized, bytes, faces under 64 px); propose a "Drive image quality" setting (fast / better / best) with evidence in SPEC §18.1; organizer decides the default; if a lower floor for thumbnails is proposed it needs an evidence table and my approval.
Done when: the evidence table is checked by script, the setting works, and results on the same folder are reported per quality level.

### V2-7 Input guidance
Build: detect Google Photos links (photos.google.com, photos.app.goo.gl) and show a clear message (the Library API cannot read albums apps did not create since March 2025; use Download as zip or put photos in Drive); accept WhatsApp/phone zips, nested zips, HEIC/HEIF, and report unsupported files by count; "how do I get my photos in" help page and tutorial step.
Done when: pasting each unsupported link type gives a helpful message, never a silent failure.

### V2-8 Distribution
Build: decide and implement Windows installer (Inno Setup) with the onedir build; code-signing decision (SmartScreen/Gatekeeper reputation); in-app "new version available" notice using the GitHub Releases API (notify only, no auto-install, no telemetry); promote macOS/Linux from beta only after real-machine tests; model download resilience (resume, mirror fallback documented); offline model pack as a documented manual step (license check first, no redistribution unless allowed).
Done when: installer installs, launches, uninstalls cleanly; version notice works offline-safe; release checklist documented.

### V2-9 Engine speed (optional, gated)
Build: investigate faster inference without changing results (batching, onnxruntime execution providers such as DirectML on Windows, avoiding duplicate work); every change must reproduce the baseline bit-for-bit or be reported as a behaviour change needing my approval.
Done when: measured s/photo before/after on the cold 259-photo set and the baseline reproduces exactly.

### V2-10 Optional extras (each needs my approval before starting)
- In-viewer selfie search (client-side face matching): privacy review, model licensing, accuracy and size cost first.
- One-click publish to GitHub Pages (token handling review first).
- Localization (Malayalam/Hindi UI strings).
- Per-person private share links.