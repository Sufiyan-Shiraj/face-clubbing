# CatLog V2 Risk Analysis & Unverified Items (V2_RISKS.md)

**Generated**: 2026-11-04T07:50:00+05:30  
**Target Release**: CatLog V2 (Phases V2-0 through V2-9)  
**Status**: Comprehensive Pre-Release Risk Audit

---

## 1. EXECUTIVE RISK MATRIX

| Risk ID | Category | Description | Severity | Likelihood | Mitigation / Status |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **R-01** | **Packaging** | Inno Setup compiler (`iscc.exe`) absent on local build machine | Medium | High | **UNVERIFIED**: Primary distribution relies on verified onedir portable ZIP (`CatLog-0.1.0-rc1-windows-x64.zip`). |
| **R-02** | **CI / Platform** | GitHub Actions multi-platform release CI | Low | Low | **VERIFIED GREEN**: CI workflow `release.yml` run 41769578829 passed 100% across all 4 platforms (`windows-x64`, `linux-x64`, `macos-arm64`, `macos-x64`). |
| **R-03** | **OS Security** | Windows SmartScreen warning on launching unsigned binary | Medium | High | Documented in `docs/CODE_SIGNING_AND_REPUTATION.md` with step-by-step user bypass instructions ("More info -> Run anyway"). |
| **R-04** | **API / Quota** | Google Drive API daily quota exhaustion (1M queries/day) | High | Very Low | A 2,000-photo scan uses ~2,020 queries (0.2% of daily quota). Exponential backoff handles transient rate limits. |
| **R-05** | **Cloud Source** | Google Photos March 2025 API restrictions | Medium | High | Addressed in Phase V2-7: explicit link detection blocks silent failures and guides users to Google Takeout or Drive upload. |
| **R-06** | **Deduplication** | Re-encoded images (JPEG vs PNG) bypass SHA-256 dedupe | Low | Medium | Documented limitation: dedupe relies on exact bitstream SHA-256 and Drive md5Checksum. Perceptual hashing deferred to future. |
| **R-07** | **Platform Gap** | Linux missing `webkit2gtk-4.0` / `webkit2gtk-4.1` for desktop GUI | Medium | Low | Documented in `README.md` with `apt-get install` prerequisites; headless web-mode (`--no-gui`) provides complete fallback. |
| **R-08** | **Viewer Scale** | Standalone `gallery.html` memory pressure on 10,000+ photos | Low | Low | Virtualized windowed rendering (60 initial, 48 increment) implemented in V2-5 keeps active DOM nodes low. |

---

## 2. UNVERIFIED ITEMS (EXPLICIT AUDIT DECLARATION)

### 2.1 Inno Setup Windows Installer Executable (`iscc`)
- **Audit Declaration**: **UNVERIFIED**
- **Details**: The Inno Setup compiler (`iscc.exe`) is not installed on this local build machine. The installer script (`installer/catlog_setup.iss`) and build script (`scripts/build_inno_installer.py`) are fully implemented and verified via unit tests (`tests/test_distribution.py`), but the final compiled `CatLog-Setup-0.1.0-rc1.exe` binary has not been compiled or executed locally.
- **Remedy / Safety**: The primary standalone onedir ZIP distribution (`dist_release/CatLog-0.1.0-rc1-windows-x64.zip`, 181 MB) is verified locally and passes all verification checks (`eval/verify_exe.py`, `eval/verify_windowed.py`, `eval/smoke_test.py`).

### 2.2 Multi-Platform CI Release Workflow
- **Audit Declaration**: **VERIFIED GREEN (ALL 4 PLATFORMS PASSING)**
- **Details**: In GitHub Actions workflow `release.yml` run 41769578829 (dispatched with `dry_run=true`), all four matrix platforms completed with conclusion `success`:
  - `Build (windows-x64)`: **success** (All 33 steps passed, Pytest passed, Vitest passed, PyInstaller built, artifact uploaded)
  - `Build (linux-x64)`: **success** (All 33 steps passed, Pytest passed, Vitest passed, PyInstaller built, artifact uploaded)
  - `Build (macos-arm64)`: **success** (All 33 steps passed, Pytest passed, Vitest passed, PyInstaller built, artifact uploaded)
  - `Build (macos-x64)`: **success** (All 33 steps passed, Pytest passed, Vitest passed, PyInstaller built, artifact uploaded)
  - Raw JSON saved: `scratch/check_ci_run.json` (SHA-256: `a7e8c6a8c032f4580a7265936acb66037c91096df2da3fd936e7a1fd2e275348`).

---

## 3. KNOWN LIMITS & CORNER CASES

### 3.1 Google Drive Recursive BFS Limits
- **Max Recursion Depth**: 5 levels. Folders nested deeper than 5 subdirectories are not enqueued.
- **File Cap**: 20,000 files per scan. Scanning stops after enqueuing 20,000 files to prevent memory exhaustion.
- **Third-Party Shortcuts**: Shortcuts pointing to external shared folders outside the organizer's permission scope emit non-fatal warnings.

### 3.2 Deduplication Constraints
- Deduplication across multiple sources relies on exact file content SHA-256 hashes (and Google Drive `md5Checksum`).
- If an image is cropped, re-saved with different compression quality, or stripped of EXIF metadata by a chat application (e.g., WhatsApp vs camera original), the files will have distinct hashes and will be treated as distinct photos. Both will cluster by face identity.

### 3.3 Large Event Browser Memory
- For static web exports containing over 5,000 photos, the static React viewer utilizes windowed batch rendering.
- The standalone single-file `gallery.html` loads all photo metadata into memory upon page load; on low-memory mobile browsers (e.g., devices with <2 GB RAM), opening a 10,000-photo `gallery.html` may cause mobile browser tab reloading.

---

## 4. SECURITY, PRIVACY & QUOTA EVALUATION

### 4.1 Sensitive Credential Isolation
- Google Drive API keys (`AIzaSy...`) are never written to exported viewer bundles, `manifest.json`, `people.json`, or diagnostic reports.
- Keys are stored locally in the user's home directory (`~/.catlog/settings.json`) with standard operating system user-profile permissions.
- In `backend/api/diagnostics.py`, all API keys matching regex `AIzaSy[A-Za-z0-9_-]{33}` are stripped and replaced with `[MASKED_API_KEY]`.

### 4.2 Biometric Face Data Protection
- No facial biometric embedding vectors (ArcFace 512-dimensional float arrays) are ever exported into the public viewer bundle.
- Only cropped JPEG thumbnail images (`faces/f_*.jpg`) and compressed photo previews (`thumbs/t_*.jpg`) are written to the public export directory.

### 4.3 Google Drive API Rate Limits
- The standard Google Drive v3 API allows 20,000 requests per 100 seconds per project and 1,000,000 requests per day.
- CatLog's BFS recursive crawler batches metadata requests (`fields="files(id,name,mimeType,size,md5Checksum)"`, `pageSize=1000`), using only 1 API call per 1,000 files in a directory.
- Image streaming requests download thumbnail bytes directly via Google's content CDN (`lh3.googleusercontent.com` / `drive.google.com/thumbnail`), which do not count against Drive API quota.
