# PhotoSorter: Project Specification

> Working name: **PhotoSorter** (rename freely). This file is the single source of truth for what we are building and why. Read it fully before writing any code. See `BUILD_PLAN.md` for the build order.
>
> **Revision 2 (2026-10-06).** Updated after Phase 0/1 acceptance and three fix-up rounds on a real 271-file test set. Sections 3, 6, 8, 9, 16 and 17 changed materially; section 18 (evaluation) is new. Anything marked **[measured]** comes from that test set. Anything marked **[default]** is a configurable starting value, not a law.

---

## 1. Problem

At events, organizers share a Drive folder with hundreds of photos and no naming convention. Attendees must scroll through all of them to find the ones they appear in. Group photos make folder-per-person duplication impractical (a 20 MB photo in 20 folders = 400 MB).

## 2. Goal

A free, general-purpose tool that takes an event's photos, groups them **by person** using face recognition (like the "People" section in Google Photos), and publishes a static web page where each attendee finds their face, opens a gallery of every photo they appear in, and downloads those photos from the original Drive files (no duplication).

## 3. Hard constraints (decisions already made)

1. **Fully free.** No paid APIs, no LLM calls, no paid hosting. Free tiers only (GitHub Pages / Cloudflare Pages, free Google Drive API).
2. **General-purpose.** Not tied to any one club. **No "profiles."** Anyone who installs it brings their own setup. Event theming lives in each export's `config.json`, not in the app.
3. **No backend server or database** that we host. The organizer runs a desktop app locally. The public viewer is static files only.
4. **Cross-platform:** Windows, macOS, Linux. One codebase, per-OS builds automated via GitHub Actions.
5. **React-level modern UI.** Tkinter/CustomTkinter were explicitly rejected as dated.
6. **Works for only organizers** (the app is organizer-only; attendees only use the static viewer).
7. **Method 2 (upload) must be possible but not required** for the project to be complete.
8. **Nobody is discarded as "noise," and every photo is reachable.** Faces that pass the quality rules become people, including people who appear in only one photo. Faces that cannot be reliably placed go into an **Unrecognized** category with a reason code instead of being dropped or force-assigned. **Every photo must appear in at least one person cluster or in Unrecognized.** No face or photo is ever deleted or hidden automatically; hiding is a manual organizer action only.
   - *Revised in rev 2:* the original wording ("every detected person gets their own cluster") was replaced. Low-quality faces (small, profile, low-score) may only *attach* to an existing person; they never start a new one. Reason: letting every weak face start a cluster produced 353 clusters (59% single-photo) on the test set.
9. **Organizer decisions must survive re-runs.** Manual edits are keyed by face and photo IDs, never by cluster IDs (section 6.3).

## 4. Non-goals

- Hosting a multi-user service or accounts system.
- Attendee-side face matching (selfie search is an optional later feature, see section 16).
- Video support.
- Commercial use (InsightFace's pretrained models are licensed for non-commercial use; flag this in the README).
- Perfect automatic clustering. The tool is *automatic grouping plus fast human review* (section 6.4).

## 5. Architecture

```
+--------------------------------------------------------------+
|  Desktop app (one exe/app per OS)                            |
|                                                              |
|  pywebview window  --->  React UI (built, served statically) |
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
|  Static viewer site (React build, on user's domain)          |
|  reads people.json + config.json + thumbs/faces              |
|  download buttons -> original files on Google Drive          |
+--------------------------------------------------------------+
```

### Components

| Component | Tech | Responsibility |
|---|---|---|
| Engine | Python module | Face detection, embeddings, clustering, thumbnails, bundle export. Must be usable from the command line with no UI and must import nothing from the API or UI layers. |
| API layer | FastAPI + uvicorn | Wraps engine as endpoints; streams progress via server-sent events (SSE); serves the built React UI at `/`; stores organizer edits. |
| UI | React + Vite + Tailwind + shadcn/ui | Pick source, show progress, review/edit people, export. |
| Shell | pywebview (+ PyInstaller) | Native window, native folder/file pickers, single double-click exe. |
| Viewer | React (separate static build) | Public people grid + per-person gallery. Shares components with the UI where possible. |
| CI | GitHub Actions | Builds Windows, macOS (arm64 + Intel), Linux; attaches to a release on a version tag. |

### Why this shape
- React and FastAPI only talk over HTTP, so the shell can later be swapped for Electron or Tauri without rewriting either part.
- Python gives full InsightFace accuracy; browser-only face models were weaker, and Drive CORS blocks browser-side image fetching.
- Java was considered and rejected (would require rewriting InsightFace's Python logic; users would need Java; UI story is no better).

## 6. Engine pipeline

### 6.1 Steps

1. **Scan** a source into a list of images (local folder, zip auto-extracted to a temp dir, or Drive folder). Photo IDs are stable hashes of content/path. Byte-identical duplicates collapse to one photo record **[measured: 271 files = 259 unique photos]**.
2. **Load + downscale** each image (cap longest side at `max_image_dim`, [default] 1600 px). Handle EXIF rotation. Face sizes used by the quality rules are measured **on the original image**, not the downscaled copy.
3. **Detect + embed** with InsightFace `buffalo_l` via `onnxruntime` (CPU by default; GPU provider if available). Each face yields a bounding box, detection score, yaw estimate and a normalized 512-d embedding. Optional `flip_average` (embedding of the face and its mirror image, averaged): [default] **off**, see section 18 for the gate to switch it on.
4. **Assign each face a role (nothing is dropped):**
   - **Seed face:** `det_score >= seed_min_det_score` (0.70), `min(w,h) >= seed_min_face_size` (64 px), `|yaw| <= seed_max_yaw` (60 degrees). Seeds are the only faces allowed to *start* a person.
   - **Attach-only face:** passes the basic floors (`min_det_score` 0.50, `min_face_size` 64, `max_yaw` 70) but not the seed rules.
   - **Unrecognized at source:** fails the basic floors. Kept, with a reason code (below).
5. **Cluster seed faces** with agglomerative clustering (`metric="cosine"`, `linkage="average"`, `distance_threshold` = `distance_threshold` [default 0.50], `n_clusters=None`). No noise concept; a seed that matches nobody forms a cluster of one.
   - **Do not use DBSCAN** (with `min_samples=1` or otherwise). It chains clusters and merges different people.
   - Needs an O(n^2) distance matrix (~400 MB at 10,000 faces). If a set is far larger, cluster in chunks or use an approximate method.
6. **Attach pass:** each attach-only face joins its nearest cluster only if **all** hold: distance to the cluster `< attach_max_distance` (0.45), nearest beats second-nearest by `>= attach_margin` (0.05), and the cluster does not already contain a face from the **same photo**. Otherwise it goes to Unrecognized.
7. **Second-pass merge (duplicate reduction):** for each cluster compute a normalized centroid from its **top-5 faces** (by detection score, then face size). For every cluster pair at centroid cosine distance `d`:
   - `d < merge_threshold` (0.50): **auto-merge** (connected components), **unless blocked by the same-photo guard**.
   - `merge_threshold <= d <= maybe_threshold` ([default] **0.65**): record a **maybe link**; never merged automatically.
   - `d > maybe_threshold`: nothing.
   - **Same-photo guard:** a merge is blocked if the merged cluster would contain two faces from one photo whose pairwise distance is greater than `same_photo_merge_max` (0.40). Two faces in one photo are different people, except in collage/multi-frame shots, where the same person appears several times at distance <= ~0.29 **[measured]** and the merge is allowed. A blocked merge becomes a maybe link with `reason: "same_photo_conflict"`.
8. **Re-attach ambiguous faces:** after the merge, retry the faces rejected as `ambiguous` with the same attach rules (merging removes many near-duplicate-cluster ambiguities). **[measured: 77 of 157 recovered]**
9. **Unrecognized category** collects (a) faces rejected at any stage, each with a `rejection_reason`, and (b) photos with no detected face. A photo may be in both a person's cluster and Unrecognized.
   - Reasons: `unattached_profile` (yaw above limit), `unattached_small`, `unattached_lowscore`, `ambiguous` (two clusters nearly equally close, or margin/same-photo rule failed).
10. **Per person:** best representative face (largest, highest score, most frontal) saved as a square crop (`face_crop_size` 256).
11. **Per photo:** thumbnail (`thumb_size` ~400 px JPEG).
12. **Export bundle** (section 8) plus organizer-only files.

**Invariant check (run on every export):** every photo ID appears in a person cluster or in Unrecognized; clustered faces + Unrecognized faces = total detected faces; no cluster holds two same-photo faces farther apart than `same_photo_merge_max` unless that cluster is on the collage allowlist (allowlist entries are **face IDs**, never cluster IDs).

**Reference result [measured, 271 files, 259 unique photos, 1,701 faces]:** 192 people (81 single-photo), 445 Unrecognized faces in 168 photos (only 6 photos are Unrecognized-only), 38 maybe links in 23 groups (counted with the earlier 0.50 to 0.60 band; the 0.65 default will add more), one collision cluster (a true collage).

### 6.2 Configuration defaults

| Key | Default | Notes |
|---|---|---|
| `max_image_dim` | 1600 | Longest side before detection |
| `min_det_score` / `min_face_size` / `max_yaw` | 0.50 / 64 / 70 | Basic floors |
| `seed_min_det_score` / `seed_min_face_size` / `seed_max_yaw` | 0.70 / 64 / 60 | Seed rules |
| `distance_threshold` | 0.50 | Seed clustering cut |
| `attach_max_distance` / `attach_margin` | 0.45 / 0.05 | Attach rules |
| `second_pass_merge` / `merge_threshold` | true / 0.50 | Auto-merge |
| `maybe_threshold` | **0.65** | Raised from 0.60 in rev 2, see section 18 |
| `same_photo_merge_max` | 0.40 | Same-photo guard |
| `flip_average` | false | Gated, section 18 |
| `include_maybe` | false | Show maybe photos in the public viewer |
| `thumb_size` / `face_crop_size` | 400 / 256 | |

Changing any default requires the evidence table described in section 18.

### 6.3 Identity and organizer edits (stability rule)

Cluster IDs (`p001`...) are **display labels assigned at export time and are not stable**: they changed three times during fix-up rounds (242, then 189, then 192 clusters; a collage cluster moved from `p041` to `p040` after a re-attach). Therefore:

- **Never** use a cluster ID in a stored edit, a test, an allowlist, a ground-truth label, or a bug report.
- Organizer edits are stored in `edits.json` (organizer-only), keyed by **face IDs and photo IDs**:
  - `merge`: a set of anchor face IDs that must end up in one person.
  - `remove`: a face ID that must not be in a given person (anchor face IDs of that person).
  - `assign`: a face ID (e.g. from Unrecognized) pinned to the person containing given anchor face IDs, or a new person.
  - `hide`: anchor face IDs of a person to exclude from the public export.
  - `name`: anchor face IDs + label.
- After any engine re-run, edits are **replayed** by locating the clusters that contain the anchor faces. An edit whose anchors can no longer be located is reported to the organizer, never silently dropped.
- Cluster IDs are assigned deterministically (photo count descending, ties broken by best-face ID) so exports are diffable.
- `id_map.json` (pre-merge to final) is a debugging aid only.

### 6.4 Behavior requirements

- **Stream one photo at a time**; free the decoded image after processing so RAM does not grow with photo count.
- **Checkpoint progress** to disk (cache of embeddings per photo ID) so a crash or closed window can resume, and re-runs skip finished photos. The cache stores both standard and flipped embeddings if `flip_average` has ever been on, so toggling it does not force re-detection.
- Run in a **background thread/process** so the UI never freezes; report progress (count, current file, ETA).
- **Cancel** support.
- Clustering must scale to ~10,000+ faces.

### 6.5 Human review (central to quality, not a nice-to-have)

Automatic clustering is deliberately conservative: it avoids wrong merges and accepts that the same person is often split. On the test set, true same-person pairs commonly sit at distance 0.60 to 0.70 (section 18). The review UI therefore has to make merging fast:

- **Merge many:** multi-select any number of people and merge them in one action (one person was split into 7 clusters in the test set).
- **Suggestions:** a ranked "possibly the same person" list built from `suggestions.json` (maybe links, with the evidence: both faces, photo counts, distance). For single-photo people the list extends past the maybe band (up to ~0.75, ranked by distance, clearly labelled as low confidence).
- **Remove** a face/photo from a person.
- **Hide** a person from the public export (manual only, e.g. on request).
- **Assign** an Unrecognized face to a person or create a person from it; for `ambiguous` faces show the stored top-3 candidate people.
- **Name** a person (optional label).
- Undo for every edit.

## 7. Input methods

### Method 1: Drive link (read-only), NO Google sign-in
- Folder must be shared "anyone with the link."
- Use the Drive API with a **free API key** (not a login, not tied to a person). Users paste their own key in Settings; optionally a bundled default can be added later.
- List files in the folder (paginate), download each photo's **thumbnail/size-limited version** instead of the 20 MB original where possible (the `thumbnailLink` can be resized, e.g. `=s1000`). Fall back to the original if no thumbnail.
- Download with bounded parallelism (not hundreds at once) and retry/backoff on rate limits.
- Output download links per file: `https://drive.google.com/uc?id=<FILE_ID>&export=download`.
- Nothing sensitive is stored in this method.
- Note: detection runs on the downloaded thumbnail, so face sizes in the quality rules refer to that image. Re-check the 64 px floors against real Drive thumbnails.

### Method 2: Local folder or zip, upload to Drive (OPTIONAL, built last)
- User picks a local folder or a zip (auto-extracted).
- Engine runs locally on the originals.
- App uploads originals to a new Drive folder, then makes the **folder** public (`permissions.create`, `type: anyone`, `role: reader`; files inherit it), then collects file IDs for links.
- **Requires Google sign-in** (OAuth, "Desktop app" client type). No anonymous upload exists. Service accounts were considered and rejected (no storage quota of their own, upload failures).
- Scope: `drive.file` (app can only touch files it created). Believed not to need full Google verification, **verify this when implementing**.
- Check total size vs. the account's free 15 GB before uploading and warn.
- Resumable uploads, with parallelism and retry.
- **Each user brings their own `client_secret.json`** (one-time ~10 min Google Cloud setup: create project, enable Drive API, create OAuth client). Provide a setup guide and an "Import client_secret.json" button. A bundled default client ID is an optional later fallback. Note: in "Testing" mode only listed test emails can log in and tokens expire every 7 days; publishing the consent screen removes both limits.
- **Simple alternative that avoids OAuth entirely:** the user drag-and-drops the folder into Drive in the browser, makes it public, and uses Method 1. Document this in the README.

## 8. Export bundle (the contract between engine and viewer)

### 8.1 Public bundle (this is what gets published)

```
export/
  config.json        # theme + event info
  people.json        # people and their photos
  faces/             # person crops (p001.jpg ...) and unrecognized-face crops (u001.jpg ...)
  thumbs/            # one thumbnail per photo: <photo_id>.jpg
```

### 8.2 Organizer-only files (never published; excluded from the public bundle)

```
suggestions.json     # maybe links + ambiguous faces, for the review UI
edits.json           # organizer decisions keyed by face/photo IDs
id_map.json          # pre-merge -> final cluster IDs (debug)
.cache/              # embeddings, per-photo detection results
```

### people.json (schema, version 1)
```json
{
  "version": 1,
  "generated_at": "2026-10-06T08:42:34+05:30",
  "photos": {
    "<photo_id>": {
      "name": "IMG_0001.jpg",
      "thumb": "thumbs/<photo_id>.jpg",
      "download": "https://drive.google.com/uc?id=<FILE_ID>&export=download",
      "width": 4000,
      "height": 3000
    }
  },
  "people": [
    {
      "id": "p001",
      "label": null,
      "face": "faces/p001.jpg",
      "photo_ids": ["<photo_id>", "..."],
      "photos": ["<photo_id>", "..."],
      "faces": [
        { "face_id": "f_<photo_id>_003", "photo_id": "<photo_id>", "file_name": "IMG_0001.jpg",
          "det_score": 0.82, "bbox": [x1, y1, x2, y2] }
      ],
      "merged_from": ["p001", "p084"],
      "merged_from_numbering": "pre-merge 242",
      "maybe_photos": []
    }
  ],
  "unrecognized": {
    "photo_ids": ["<photo_id>", "..."],
    "faces": [
      { "face_id": "f_<photo_id>_001", "photo_id": "<photo_id>", "file_name": "IMG_0002.jpg",
        "face": "faces/u001.jpg", "rejection_reason": "unattached_profile", "det_score": 0.63 }
    ]
  }
}
```
- `photo_ids` is canonical. `photos` is a version-1 alias that is always equal to it and may be dropped in version 2.
- `maybe_photos` is empty unless `config.include_maybe` is true, in which case entries are `{ "photo_id", "source_cluster", "distance" }`. The viewer must show these separately and labelled as possible matches.
- `faces` and `merged_from` are organizer/debug data; the viewer ignores them. A publish step may strip `faces[].bbox` and `merged_from` to shrink the file.
- For local-folder input without Drive upload, `download` is null; the viewer hides the button.

### suggestions.json (organizer-only, version 1)
```json
{
  "version": 1,
  "threshold_range": [0.5, 0.65],
  "maybe_groups": [
    { "group_id": 1, "clusters": ["p001", "p144"], "cluster_count": 2, "photos_count": 72,
      "links": [
        { "cluster_a": "p001", "cluster_b": "p144", "distance": 0.5104,
          "cluster_a_photos": 71, "cluster_b_photos": 1,
          "cluster_a_best_face": "f_...", "cluster_a_best_det_score": 0.91,
          "cluster_b_best_face": "f_...", "cluster_b_best_det_score": 0.79,
          "reason": "centroid_band" } ] } ],
  "ambiguous_faces": [
    { "face_id": "f_...", "photo_id": "...",
      "top_clusters": [ { "cluster_id": "p040", "distance": 0.3095 } ] } ],
  "stats": { "total_faces": 1701, "seed_faces": 1003, "unattached_breakdown": { } }
}
```
`reason` is `centroid_band` or `same_photo_conflict`. Cluster IDs inside this file are valid only for the export that produced it.

### config.json (theming, the only per-event customization)
```json
{
  "title": "Event Name",
  "subtitle": "Photos from ...",
  "logo": "logo.png",
  "accent": "#2563eb",
  "font": "Inter",
  "footer": "Hosted by ...",
  "show_labels": true,
  "include_maybe": false,
  "hide_single_photo_default": false
}
```

## 9. Viewer site (public, static)

- Reads `config.json` and `people.json`; no backend.
- **People grid:** one grid of face thumbnails sorted by photo count (most frequent first). A toolbar toggle, **"Hide single-photo people"**, filters out people with one photo (its initial state comes from `hide_single_photo_default`). The toggle never changes the data; nobody is removed from the export. *(Replaces the earlier "collapsible long-tail section".)*
- **Unrecognized entry** at the end of the grid. It opens two parts: (a) a grid of the unrecognized **face crops**, each opening its photo, and (b) a separate list of photos in which no face was detected. Every photo is therefore reachable.
- **Gallery:** clicking a person shows their photos (thumbnails, lazy-loaded), with an enlarged preview view. If `include_maybe` is true, possible matches appear in a separate, labelled section.
- **Downloads:** per-photo download button linking to the Drive original. **Zip download is deferred:** Drive's CORS blocks client-side zipping, and the alternatives (a small backend, or Cloudflare R2) need extra setup. Start with individual downloads only.
- Responsive and mobile-friendly (attendees will open it on phones).
- Hosting: GitHub Pages or Cloudflare Pages, linked to the club's domain. Use an **unguessable URL slug** for privacy.
- Only thumbnails live on the static host (tens of MB), never the originals.

## 10. Credential storage (Method 2 only)

The sensitive item is the **OAuth refresh token** (grants Drive access). `client_secret.json` is far less sensitive (Google treats desktop-app secrets as non-confidential) but is stored the same way.

Three user-selectable levels in Settings:
1. **Don't save (default):** sign in each run; token held in memory only. Safest for shared computers.
2. **OS keychain:** Python `keyring` (Windows Credential Manager, macOS Keychain, Linux Secret Service). Encrypted, tied to OS login; does not re-prompt on read.
3. **App passphrase:** encrypt with `cryptography` Fernet, key derived from a passphrase via scrypt. App prompts for the passphrase whenever the token is needed or "Reveal" is clicked.

- **"Sign out and erase"** button: call Google's token revoke endpoint **and** wipe local data.
- Never put tokens or client secrets in the repo or in the built exe.
- Honest limit: this cannot defend against someone with full control of a running, unlocked computer. Prompting for the *OS* admin password is not portable and is not attempted.

## 11. Repo layout (proposed)

```
photosorter/
  README.md
  SPEC.md
  BUILD_PLAN.md
  requirements.txt
  main.py                  # starts FastAPI thread + opens pywebview window
  run.bat / run.sh         # dev convenience: venv + install + launch
  backend/
    engine/                # scan, detect, embed, cluster, merge, export, cache, edits replay
    drive/                 # read (API key), upload (OAuth), auth storage
    api/                   # FastAPI routes, SSE progress, job manager, edits store
  frontend/                # React app (organizer UI), committed dist/ build
  viewer/                  # React static viewer template
  eval/                    # ground_truth.json, evaluation scripts, verify_export.py
  .github/workflows/       # release builds for all OSes
  tests/
```

## 12. Dependencies (initial)

Python 3.10 to 3.12 (3.13 may break ML wheels): `fastapi`, `uvicorn`, `pywebview`, `insightface`, `onnxruntime`, `numpy`, `scikit-learn`, `opencv-python`, `Pillow`, `google-api-python-client`, `google-auth-oauthlib`, `keyring`, `cryptography`, `pyinstaller` (build only).
Frontend: React, Vite, Tailwind, shadcn/ui. Node is needed only to modify the UI; the built `dist/` is committed so end users never need it.

## 13. Packaging and release

- Dev: `npm run dev` + `uvicorn` in two terminals (hot reload). Only during development.
- Release: `npm run build` produces `dist/`; FastAPI serves it; `main.py` launches FastAPI on a random local port in a background thread and opens a pywebview window pointed at it; PyInstaller bundles code, models, and `dist/`.
- PyInstaller cannot cross-compile, so **GitHub Actions** builds each OS on its own runner when a version tag is pushed (free for public repos): Windows exe, macOS `.app` (arm64 and Intel separately), Linux binary/AppImage.
- Windows: WebView2 is preinstalled on Windows 10/11. macOS: built-in WebKit. Linux: needs system GTK/WebKit2GTK (e.g. Ubuntu: `sudo apt install python3-venv python3-gi gir1.2-webkit2-4.1`; package names vary by distro).
- Unsigned builds trigger SmartScreen (Windows) and Gatekeeper (macOS). Document the bypass in the README (Windows: "More info, Run anyway"; macOS: right-click, Open). Code signing costs money and is out of scope.
- Expect 300 to 500 MB per build (models + ML libraries). Models download (~300 MB) on first run unless bundled.
- Fallback if Linux/pywebview is troublesome: swap the shell for Electron without touching React or FastAPI.

### Run from source (all OSes)
```
git clone <repo-url> && cd photosorter
python -m venv .venv              # python3 on macOS/Linux
.venv\Scripts\activate            # source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
python main.py
```
On Linux create the venv with `--system-site-packages` so pywebview sees the system GTK bindings. On Windows, InsightFace may need "Microsoft C++ Build Tools" to compile; if that proves painful, pin a prebuilt wheel or use an alternative package serving the same models.

## 14. Performance and resource estimates

- **Time (CPU):** ~1 to 1.5 s per large photo, so ~1,000 photos is about 15 to 30 minutes. GPU provider speeds this up. `flip_average` roughly doubles the embedding cost per face.
- **RAM peak:** ~2 to 4 GB (models ~1 to 2 GB; one decoded 20 MB JPEG is ~70 MB transient; embeddings are tiny). An 8 GB laptop is fine.
- **Disk:** venv ~1 to 1.5 GB; models ~300 MB; thumbnails and crops for 1,000 photos ~50 to 100 MB.
- The venv is only a folder; RAM is used by the running Python process and freed when the app closes.

## 15. Privacy and ethics

- Faces are biometric data. Get the organizer's/attendees' consent; don't retain data longer than needed.
- A public viewer shows every attendee's face to anyone with the link: use an unguessable URL slug and share only with attendees.
- Support "hide person" and photo removal so people can be excluded on request.
- The public Drive folder exposes originals to anyone with the link; keep the link unguessable.
- The public bundle must exclude `suggestions.json`, `edits.json`, `id_map.json` and `.cache/`.
- **Licensing:** the project's own code is under the **MIT license** (`LICENSE` file in the repo root). The InsightFace pretrained models (`buffalo_l`) carry a separate **non-commercial** license that MIT does not override. Do not commit or bundle model files in the repo; download them on first run, and state the model license in the README and wherever the exe is distributed. Anyone wanting commercial use must swap in a differently licensed model.

## 16. Risks and open questions

| Item | Status |
|---|---|
| Same person split across clusters (recall) | **Measured, the main quality limit.** On 22 independent labelled same-person pairs, 0 fall at or below distance 0.50 and 6 at or below 0.60 (standard embeddings). Mitigation: conservative auto-merge, maybe tier to 0.65, ranked suggestions, fast multi-merge UI. |
| Wrong merges (precision) | Auto-merge at 0.50 plus the same-photo guard. **Not yet measured with cross-photo negatives**; only same-photo negatives exist. |
| Unrecognized volume | 445 of 1,701 faces (26%) after re-attach **[measured]**: profile 174, small 111, low score 80, ambiguous 80. Mostly crowd/profile faces; photos stay reachable. Do not raise `attach_max_distance` without labelled precision (collision counts cannot see wrong-person attachments). |
| Labelled data is thin | 30 positive pairs from 3 sets, no listed negatives. One Set C face is an outlier (0.60 to 0.89 from the rest) and needs the organizer to confirm the label. Target: 15+ sets before changing defaults. |
| Cluster IDs unstable between runs | Handled by section 6.3. Any code that stores or compares `pNNN` IDs across runs is a bug. |
| Drive thumbnail availability / size via API key on public folders | Verify behavior in Method 1 before committing; re-check the 64 px face-size floors on Drive thumbnails. |
| `drive.file` scope not needing Google verification | Believed true; verify at implementation. |
| InsightFace install on Windows | May need C++ Build Tools or pinned wheel. |
| pywebview on Linux (system deps) | Document; Electron is the fallback. |
| Drive download throttling under heavy traffic | Low concern at club scale. |
| Many single-photo people (background strangers) | Accepted by design. Mitigated by sorting by photo count, the "Hide single-photo people" toggle, and organizer merge/hide tools. |
| Recognition model accuracy | `buffalo_l` is the baseline. A larger InsightFace recognition model (same non-commercial license) may recall more; untested. Evaluate with section 18 before adopting. |
| Zip download of a person's photos | Deferred (needs backend or R2). |
| Optional: selfie search in viewer (attendee uploads photo to find theirs) | Future feature; would need in-browser face matching or a backend. |
| Viewer default for the single-photo toggle in public exports | Open: currently off (`hide_single_photo_default: false`). |

## 17. Decisions log (chronological summary)

1. Approach: face clustering (detect, embed, cluster), not just detection.
2. Output via a static page + Drive links to originals; avoid duplicating files (Drive shortcuts considered, index page chosen).
3. Fully free stack only.
4. Browser-only processing considered; desktop app chosen for accuracy and no Drive CORS issues.
5. Two input methods: Drive link (read-only, API key) and folder/zip upload (OAuth). Upload is optional.
6. No profiles; general-purpose tool; credentials get 3 storage levels with encrypted + erasable options.
7. UI: React inside pywebview (not Tkinter), FastAPI backend, PyInstaller packaging.
8. Cross-platform builds via GitHub Actions; Python kept over Java.
9. No noise label; unrecognizable faces and face-less photos go into an Unrecognized category; clustering switched from DBSCAN to average-linkage agglomerative.
10. Code licensed MIT; InsightFace models keep their separate non-commercial license (downloaded on first run, never committed to the repo).
11. **(rev 2)** Seed + attach-only clustering: weak faces may only attach to an existing person, never start one. Replaces "every detected face clusters".
12. **(rev 2)** Strict attach rules (distance < 0.45, margin >= 0.05, same-photo barred); ambiguous faces re-attached after the merge pass.
13. **(rev 2)** Three-tier matching: auto-merge below 0.50, maybe link up to 0.65 (raised from 0.60 after same-photo negatives showed 0 of 3,246 pairs at or below 0.60 and 3 of 3,246 at or below 0.65), nothing above.
14. **(rev 2)** Same-photo guard on second-pass merges (`same_photo_merge_max` 0.40, collages allowed). It removed two false-merge clusters that the unguarded merge had created.
15. **(rev 2)** Organizer edits keyed by face/photo IDs and replayed after re-runs; cluster IDs are display-only.
16. **(rev 2)** Viewer: single people grid with a "Hide single-photo people" toggle; Unrecognized shows face crops plus a separate no-face photo list.
17. **(rev 2)** `flip_average` stays off by default until ground truth has 15+ labelled sets showing a gain; measured so far: +2 true pairs at or below 0.50 and 16 fewer clusters, with no extra collisions or negatives below 0.60.
18. **(rev 2)** Engine-report rule: reports contain counts, IDs and filenames only; every report table is checked against the JSON by a verification script.

## 18. Evaluation and ground truth

Quality changes are judged against data, not impressions.

- **`eval/ground_truth.json`:**
  ```json
  { "sets": { "A": ["f_...", "f_..."], "B": ["..."] },
    "different": [["f_...", "f_..."]] }
  ```
  Each set lists faces the organizer says are one person (by **face ID**). `different` lists faces the organizer says are different people.
- **Free negatives:** any two faces in the same photo are different people (excluding collage allowlist). The evaluation uses all same-photo seed-face pairs as negatives **[measured: 3,246 pairs; minimum distance 0.6144; none at or below 0.60]**.
- **Required table for any threshold or model change:** at thresholds 0.50 to 0.80, true-pair recall (count and %) and false-pair count (count and %), for standard and flip-averaged embeddings, with the number of positive pairs and sets stated.
- **Measured baseline (3 sets, 30 pairs; standard embeddings):** recall 1/30 at <=0.50, 7/30 at <=0.60, 10/30 at <=0.65, 18/30 at <=0.70, 24/30 at <=0.75; false pairs 0, 0, 3, 19, 75 of 3,246. Excluding the near-duplicate pair and the outlier face, 22 independent pairs: 0, 6, 16, 22 at <=0.50, 0.60, 0.70, 0.80.
- **Base-rate warning:** a 0.59% false rate at 0.70 over roughly 18,000 possible cluster pairs is on the order of 100 spurious suggestions. Distances above the maybe band are for ranked review only, never for automatic action.
- **Cross-photo negatives** (organizer-labelled different people in different photos) are still missing and are needed before loosening any auto-merge or attach threshold.
- Gate to enable `flip_average` by default: 15+ labelled sets, recall gain confirmed, no increase in false pairs at or below 0.65.
