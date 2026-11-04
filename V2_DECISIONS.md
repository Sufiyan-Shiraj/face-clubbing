# CatLog V2 Design Decisions Log (V2_DECISIONS.md)

**Generated**: 2026-11-04T07:45:00+05:30  
**Target Release**: CatLog V2 (Phases V2-0 through V2-9)  
**Purpose**: Authoritative audit of all architectural decisions, defaults chosen, tradeoffs, alternatives rejected, and items flagged for organizer confirmation.

---

## 1. DECISION SUMMARY TABLE

| Decision ID | Phase | Topic / Decision | Chosen Approach | Alternative Rejected | Status |
| :---: | :---: | :--- | :--- | :--- | :---: |
| **D-V2-01** | V2-0 | Drive Recursion Depth & Cap | Bounded BFS queue (depth 5, 20k file limit) | Unbounded DFS recursion (stack overflow, memory exhaustion) | **decided** |
| **D-V2-02** | V2-0 | Subfolder Error Handling | Resilient non-fatal subfolder error isolation | Aborting full scan on single unreadable folder | **decided** |
| **D-V2-03** | V2-1 | Diagnostics Report Scrubbing | Counts-only report with regex path/key/face scrubbing | Raw log dumping or unscrubbed crash dumps | **decided** |
| **D-V2-04** | V2-2 | Manifest V2 Data Contract | `manifest.json` with `sources` array & provenance | Storing source metadata in `people.json` | **decided** |
| **D-V2-05** | V2-3 | Incremental Ingestion Stability | Frozen Mode: existing clusters have strictly 0 membership delta | Full re-clustering (destroys existing cluster numbers & review work) | **decided** |
| **D-V2-06** | V2-3 | Mutation Safety & Snapshots | Pre-mutation atomic snapshots in `.snapshots/` with rollback | In-memory undo only (lost on process exit or crash) | **decided** |
| **D-V2-07** | V2-4 | Project Merger Architecture | Creates a NEW third project; parent projects remain immutable | In-place destructive mutation of Project A | **decided** |
| **D-V2-08** | V2-4 | Merge Conflict Resolution | Order-independent DisjointSet union; explicit conflict review UI | Silent last-write-wins overwriting of names and assignments | **needs organizer decision** |
| **D-V2-09** | V2-5 | Viewer Mixed-Source Downloads | Per-photo Drive export URL synthesis; null for local in static zip | Bundling massive local files into public export zip | **decided** |
| **D-V2-10** | V2-5 | Viewer Gallery Virtualization | Windowed batch rendering (initial 60, increment 48) with sentinel | Full DOM rendering of 1,000+ photo elements | **decided** |
| **D-V2-11** | V2-6 | Drive Image Quality Tiers | 4 presets (`fast`=1000px default, `better`=1600px, `best`=2000px, `original`) | Changing SPEC 6.2 64px face floor; defaulting to high-bandwidth `best` | **needs organizer decision** |
| **D-V2-12** | V2-7 | Google Photos Link Handling | Explicit warning explaining March 2025 Google restrictions + Takeout guide | Attempting brittle web scraping or failing silently | **decided** |
| **D-V2-13** | V2-7 | Nested ZIP Archive Extraction | 3-level recursive decompression with 10:1 ratio ceiling | Rejecting zip-in-folder inputs or unbounded decompression | **decided** |
| **D-V2-14** | V2-8 | Primary Distribution Format | Portable onedir ZIP package (`CatLog-windows-x64.zip`) | Forcing Inno installer when `iscc` compiler is missing locally | **decided** |
| **D-V2-15** | V2-8 | Code Signing & Reputation | Open-source unsigned release with documented SmartScreen guide | Requiring $200-$400/yr commercial EV certificate for v0.1.0 | **needs organizer decision** |
| **D-V2-16** | V2-8 | In-App Version Update Notice | Anonymous GitHub Releases check on launch; zero telemetry; notify only | Background auto-updater or analytics tracking | **decided** |
| **D-V2-17** | V2-9 | Engine Module Initialization | Selective loading (`detection`, `recognition`, `landmark_3d_68`) | Loading unused `landmark_2d_106` and `genderage` models | **decided** |
| **D-V2-18** | V2-9 | CPU vs GPU Inference Default | CPU execution provider as stable cross-platform default | Enabling DirectML by default (introduced native DLL crashes) | **decided** |

---

## 2. DETAILED DECISION RECORDS

### D-V2-01: Drive Recursion Depth & File Cap (Phase V2-0)
- **Context**: Large event folders often contain nested albums (e.g. `Event/Day 1/Morning/`).
- **Decided**: Iterative Breadth-First Search (BFS) with a visited folder ID set, maximum depth of 5 levels, and an overall limit of 20,000 files.
- **Alternative Rejected**: Unbounded depth-first recursion, which risks call-stack overflow on deep folder trees and runaway memory allocation on large Drive drives.
- **Organizer Confirmation**: Confirm whether 5 levels and 20,000 files are sufficient for all planned events.

### D-V2-05: Incremental Ingestion Frozen Mode Invariants (Phase V2-3)
- **Context**: When late photos arrive from a secondary photographer, organizers need to add them without losing prior review work.
- **Decided**: Enforce mathematical cluster freezing:
  1. Existing clusters have strictly zero membership delta (cannot lose or swap faces).
  2. New faces attach to existing clusters if distance <= 0.45, or form new clusters.
  3. Second-pass auto-merge is restricted strictly to new-to-new clusters.
- **Alternative Rejected**: Re-clustering all photos from scratch, which changes cluster IDs and invalidates manual names and triage.
- **Organizer Confirmation**: Approved as the safest workflow for event organizers.

### D-V2-08: Merge Conflict Resolution (Phase V2-4)
- **Context**: Merging Project A and Project B when both projects have assigned different names to the same person, or when one project assigned a face that the other removed.
- **Decided**: Merges do not overwrite silently. Conflicting names and remove-vs-assign edits are recorded in a `conflicts` array and presented to the organizer in a dedicated Conflict Review modal.
- **Alternative Rejected**: Last-write-wins (loses organizer intent without notification).
- **Status**: **needs organizer decision** — Review the Conflict Review modal layout and approve the resolution flow.

### D-V2-11: Drive Image Quality Preset Defaults (Phase V2-6)
- **Context**: Google Drive image streaming supports dynamic dimension requests (`=s1000`, `=s1600`, `=s2000`).
- **Decided**:
  - `fast` (`=s1000`): Default. Saves 94.9% network bandwidth. Ideal for quick scans and fast event turnaround.
  - `better` (`=s1600`): Saves 88.2% bandwidth; provides 3.2x face yield for medium-distance shots.
  - `best` (`=s2000`): Saves 83.3% bandwidth; provides 7.1x face yield for wide group photos and small faces.
  - `original`: Native uncompressed camera files.
- **Alternative Rejected**: Making `best` (2000px) the default, which would increase download times 3.5x on slow venue Wi-Fi.
- **Status**: **needs organizer decision** — Confirm whether `fast` should remain the shipping default or if `better` is preferred.

### D-V2-15: Code Signing & SmartScreen Reputation (Phase V2-8)
- **Context**: Windows SmartScreen flags newly released, unsigned executables.
- **Decided**: Documented in `docs/CODE_SIGNING_AND_REPUTATION.md`. For the open-source v0.1.0 release, distribute portable unsigned binaries with clear, illustrated user instructions for bypassing SmartScreen ("More info -> Run anyway").
- **Alternative Rejected**: Delaying release until an expensive ($200-$400/yr) commercial Extended Validation (EV) certificate is purchased.
- **Status**: **needs organizer decision** — Confirm whether to purchase a certificate or proceed with unsigned open-source distribution.

### D-V2-17: Selective Module Loading in InsightFace (Phase V2-9)
- **Context**: Default `FaceAnalysis` loads 5 models: detection, recognition, 3D landmarks, 2D landmarks, and gender/age.
- **Decided**: Pass `allowed_modules=["detection", "recognition", "landmark_3d_68"]` to `FaceAnalysis`. Omitting `landmark_2d_106` and `genderage` cut initialization time from 3,406ms to 1,535ms (54.9% faster) and reduced RAM usage.
- **Alternative Rejected**: Loading all models (wasted memory on unused attributes).
- **Baseline Verification**: Verified bit-for-bit exactness: 192 clusters, 1,256 clustered faces, 445 unrecognized faces, 1701 total faces, 259 photos.
