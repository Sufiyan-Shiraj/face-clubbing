# CatLog V2 User-Visible Changes & Migration Guide (V2_CHANGES.md)

**Generated**: 2026-11-04T07:40:00+05:30  
**Target Release**: CatLog V2 (Phases V2-0 through V2-9)  
**Audience**: Event Organizers, Maintainers, and Upgrading Users

---

## 1. USER-VISIBLE UI CHANGES

### 1.1 Home Screen (`HomeScreen.tsx`)
- **Multi-Source Input Card**: Organizers can now add multiple photo sources before starting a scan. The "+ Add Another Source" button allows mixing Google Drive folders, local directories, and ZIP archives in a single project.
- **Drive Image Quality Selector**: A quality dropdown allows choosing among 4 tiers (`fast` = 1000px [default, 94.9% bandwidth saving], `better` = 1600px, `best` = 2000px [7x face recovery], `original` = native camera files).
- **Google Drive Recursion Telemetry**: Scanning displays live recursion status ("Found N images in M folders"). Subfolders are traversed up to 5 levels deep.
- **Input Guidance Button**: A tactile "Need help with photos?" button opens the 4-tab `InputGuidanceModal`.

### 1.2 Review & People Screen (`ReviewPeopleScreen.tsx`)
- **Source Filter Dropdown (`#source-filter-select`)**: Filter the people grid and photos by origin source (e.g., "All Sources", "Folder A", "Photographer 2 ZIP").
- **Source Badges on Cards**: Each person and photo card displays a compact color-coded badge indicating its origin source and subfolder album label.
- **"+ Add Source" Top Action**: An action button in the header allows adding more photos to an active project at any time.
- **"Merge Projects" Action**: The Project menu includes an option to combine two existing projects into a unified event collection.

### 1.3 Add Source Modal (`AddSourceModal.tsx`) & What Changed Modal (`WhatChangedModal.tsx`)
- **Incremental Source Ingestion**: Step-by-step wizard to ingest additional photos. An explicit banner confirms **"Frozen Mode Active"**: existing people clusters will remain mathematically unchanged.
- **What Changed Diff Report**: Upon completion, a comprehensive summary shows:
  - Total new photos added and scanned.
  - New people discovered and seeded.
  - Faces that attached to existing people.
  - Confirmation that existing people membership delta is **0**.
  - **One-Click Rollback**: A button allows instantly reverting the project to its pre-mutation state using `.snapshots/`.

### 1.4 Merge Projects Modal (`MergeProjectsModal.tsx`)
- **Two-Project Combination Wizard**: Allows selecting two existing projects to merge into a new third project (parent projects remain immutable).
- **Settings Hash Validator**: Automatically checks whether both projects were processed with identical clustering settings. If settings differ, a warning is displayed.
- **Conflict Review Table**: Lists any conflicting person names or conflicting face assignments between the two projects, allowing the organizer to review and resolve them explicitly before finalizing.

### 1.5 Input Guidance Modal (`InputGuidanceModal.tsx`)
- **Google Photos Warning**: Directly informs users pasting `photos.google.com` or `photos.app.goo.gl` links that Google's March 2025 Library API restrictions prevent third-party app access, providing clear instructions for Google Takeout or Drive upload.
- **Cloud Links Guide**: Step-by-step instructions for Dropbox, OneDrive, Box, and iCloud sharing.
- **Nested Archives Guide**: Informs users that WhatsApp Media and phone backup ZIP files will be recursively unpacked automatically up to 3 levels deep.

### 1.6 App Update Banner (`AppUpdateBanner.tsx`)
- **Non-Intrusive Update Notice**: When connected to the internet, the app checks the GitHub Releases API (without sending any telemetry or user data). If a newer version is available, a subtle top banner displays: "CatLog vX.Y.Z is available" with a "View Release" button and a dismiss option.

### 1.7 Static Web Viewer & Standalone HTML Gallery
- **Album Subfolder Tabs**: If photos were organized into subdirectories (e.g., `Day 1/`, `Reception/`), the viewer renders interactive album filter tabs.
- **Per-Photo Drive Download**: When viewing a photo originating from Google Drive, a direct export download button (`https://drive.google.com/uc?id=<id>&export=download`) allows downloading the full original file.
- **Windowed Batch Virtualization**: Collections with over 1,000 photos utilize windowed batch rendering (initial batch 60, increment 48) with an intersection sentinel, ensuring fast scrolling on mobile devices and older laptops.

---

## 2. NEW SETTINGS & DEFAULTS

| Setting Key | Default Value | Available Options | Notes |
| :--- | :---: | :--- | :--- |
| `drive_quality` | `"fast"` | `"fast"`, `"better"`, `"best"`, `"original"` | Controls Drive image streaming dimension. `fast` (1000px) provides 95% bandwidth saving; `best` (2000px) recovers small faces. |
| `update_check_enabled` | `true` | `true`, `false` | Enables offline-safe GitHub Releases version check on launch. Zero telemetry. |
| `max_depth` | `5` | `1` to `10` | Bounded BFS recursion depth for Google Drive subfolders. |
| `max_files_cap` | `20000` | Fixed ceiling | Prevents unbounded memory growth during recursive scanning. |

---

## 3. NEW FILE FORMATS & DATA CONTRACTS

### 3.1 Project Manifest Schema V2 (`manifest.json`)
Every project directory now contains a `manifest.json` with schema version 2:
```json
{
  "schema_version": 2,
  "created_at": "2026-11-04T00:00:00Z",
  "settings_hash": "4a9b927f5789cd69",
  "sources": [
    {
      "id": "src_01j7b...",
      "kind": "drive",
      "label": "Day 1 Drive Folder",
      "path_or_url": "https://drive.google.com/drive/folders/<FOLDER_ID>",
      "quality": "fast",
      "added_at": "2026-11-04T00:00:00Z",
      "photo_count": 259,
      "face_count": 1701
    }
  ],
  "unsupported_files": {
    "count": 2,
    "extensions": {
      ".mp4": 1,
      ".txt": 1
    }
  }
}
```

### 3.2 Enhanced `people.json`
Photo entries within `people.json` now include:
- `source_id`: The ID of the originating source from `manifest.json`.
- `album`: Subfolder path or album name extracted during recursive ingestion.
- `download`: Direct Google Drive download URL for Drive photos, or `null` for local photos in a static bundle.

### 3.3 Atomic Rollback Snapshots (`.snapshots/`)
Before modifying an existing project during incremental source ingestion, the engine creates an atomic snapshot under `.snapshots/<timestamp>/` containing exact copies of `people.json`, `manifest.json`, and `edits.json`.

---

## 4. MIGRATION BEHAVIOR FOR EXISTING PROJECTS

### 4.1 What Happens to a V1 Project?
- When an organizer opens a project created in CatLog V1 (which lacks `manifest.json`):
  1. The project loader detects `schema_version` is missing.
  2. The engine transparently migrates the project by synthesizing a V2 `manifest.json` containing a single default source (`kind: "local"`, `label: "Original Import"`).
  3. All existing photo IDs, face IDs, cluster IDs, and `edits.json` entries remain 100% untouched.
  4. The project is immediately compatible with all V2 features (incremental source addition, merging, source filtering).

### 4.2 What Happens to `projects.json`?
- The application project registry located in the user's workspace/app data records project paths and metadata.
- V1 entries in `projects.json` are preserved. Opening or saving a project updates its registry entry with `manifest_version: 2` and the count of sources.

### 4.3 What Happens to `~/.catlog` and Legacy `~/.photosorter`?
- Application settings are stored in `~/.catlog/settings.json` (such as `drive_api_key`).
- If legacy `~/.photosorter/settings.json` exists on first run, CatLog automatically migrates it to `~/.catlog/settings.json` with zero data loss.
