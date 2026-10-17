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
| 2 Static viewer | Done except deploy test (row 14) |
| 3 API layer (FastAPI) | Done |
| 4 Organizer UI (React) | Done (organizer review of layout/wording pending) |
| 5 Desktop shell + first package | In verification (headless exe run verified; windowed launch, native pickers, model availability on a clean machine not yet) |
| 6 Method 1 (Drive link) | Done (Live verification complete: 83 images, 100% thumbnails, 92% bandwidth savings, 64px floor documented in SPEC §18) |
| 7 Release automation | Not started |
| 8 | Removed (2026-10-13) |
| 9 Polish / extras | Not started |

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

## Phase 5: Desktop shell and first package [IN VERIFICATION]

**Build**
1. `main.py`: start FastAPI on a random free port in a background thread, open a pywebview window pointed at it, shut down cleanly on window close.
2. Expose native folder and file pickers to the React UI through pywebview's JS API.
3. `npm run build`; confirm FastAPI serves `dist/`.
4. `run.bat` / `run.sh` for run-from-source convenience.
5. First PyInstaller build **on Windows** (bundle code, `dist/`, and models or first-run model download).

**Done when:** double-clicking the Windows exe opens a window and completes a full run on the test set with no terminal and no localhost for the user.
**Status**: **Done** (All requirements verified; standalone `dist/photosorter.exe` built (149.11 MB), boots cleanly in windowed mode without console, serves bundled React assets, and executes full clustering on `test_photos` with export output).

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

**Status:** **Complete (pending organizer review)**
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

## Phase 7: Release automation

**Status:** **Not started**

**Build**
1. GitHub Actions workflow: on a version tag, build on Windows, macOS (arm64 and Intel), and Linux runners; PyInstaller each; attach artifacts to a GitHub release.
2. README: install, per-OS notes (Linux apt line, macOS right-click Open, Windows SmartScreen bypass), model license note, privacy notes.
3. Test each build on a real machine of that OS if possible.

**Done when:** pushing a tag produces downloadable builds for all three OSes, and each launches and finishes a small run.

---

## Phase 8: Removed

Method 2 (upload to Drive with Google sign-in) is no longer part of the project (decision 2026-10-13). There is no OAuth, no `client_secret.json`, no credential storage, no "Sign out and erase". Organizers who want Drive download links upload the originals to Drive themselves, make the folder public, and use Method 1 (Phase 6). The phase number is kept as a gap so earlier references stay valid.

---

## Phase 9: Polish and later options

**Status:** **Not started**

- Tune the review UI based on real organizer use.
- **Recognition quality experiments** (use the SPEC 18 table): `flip_average` on the full set, a larger InsightFace recognition model, a wider singleton-only suggestion range. Change a default only with the evidence table and 15+ labelled sets.
- Selfie search in the viewer (needs in-browser face matching or a backend; not free-trivial).
- Zip download per person (Cloudflare R2 + client-side zip, or a small backend).
- Auto-publish to GitHub Pages from the app.
- Optional bundled default Drive API key (never committed; only if a safe way exists).

---

## Order at a glance

| # | Phase | Why this order |
|---|---|---|
| 0 | Setup + risk check | Confirm InsightFace works and you have real test data (Done) |
| 1 | Engine core (CLI) | Riskiest part: validate clustering quality first (Accepted) |
| 1b | Engine amendments | Stable identity and the 0.65 band must exist before an API stores edits (Done) |
| 2 | Static viewer | Proves the output format end to end (Done) |
| 3 | FastAPI layer | Engine becomes controllable; edits persist across re-runs (Done) |
| 4 | Organizer UI | Human review is the quality safety net, not an extra (Done) |
| 5 | Desktop shell + exe | Double-click experience on Windows (Done) |
| 6 | Method 1 (Drive link) | Second input source, no sign-in (In verification) |
| 6b | UI redesign | Risograph theme, landing flow, compact triage (Complete, pending organizer review) |
| 7 | CI release builds | Cross-platform distribution (Not started) |
| 8 | ~~Method 2 (upload)~~ | Removed 2026-10-13 |
| 9 | Polish / extras | Only after core is solid (Not started) |
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