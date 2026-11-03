# CatLog Official Release Checklist & Verification Protocol

This checklist governs the release promotion procedure from Release Candidate (`-rcX`) to Official Production (`vX.Y.Z`).

---

## 1. Pre-Flight Verification & Automated Audits

Before tagging any release, execute all automated validation suites:

- [ ] **Backend Pytest Suite**:
  ```powershell
  python -m pytest tests -q
  ```
  *(Must achieve 100% pass across all test modules).*

- [ ] **Frontend & Viewer Vitest Suites**:
  ```powershell
  npm --prefix frontend test
  npm --prefix viewer test
  ```
  *(Must achieve 100% pass across all component suites).*

- [ ] **Accessibility & UI Rules Audit**:
  ```powershell
  python eval/check_ui_rules.py
  ```
  *(Enforces minimum 12px text size, WCAG 2.1 AA 4.5:1 contrast, and keyboard reachability).*

- [ ] **Settings Spec & Default Invariance**:
  ```powershell
  python eval/check_settings_spec.py
  ```
  *(Asserts identical 15 clustering parameter defaults across backend models, pipeline, and UI).*

- [ ] **Export & Public Bundle Hygiene Verification**:
  ```powershell
  python eval/verify_export.py
  ```
  *(Passes all 17 automated checks: zero organizer files leaked into public bundle, deterministic cluster ordering, and exact face accounting).*

- [ ] **Status Integrity Audit**:
  ```powershell
  python eval/check_status_integrity.py
  ```

---

## 2. Platform Promotion Criteria (Beta & Production)

| Platform | Current Stage | Promotion Criteria to Official Stable |
| :--- | :--- | :--- |
| **Windows x64** | **Production Ready** | Onedir cold startup <= 2.0s, pywebview Native Pickers verified, Inno Setup installer verified, zero popup launch. |
| **macOS Apple Silicon (arm64)** | **Beta &rarr; Stable** | Verified on physical M-series Mac hardware: WebKit Cocoa bridge, native file pickers, Gatekeeper workaround instructions documented. |
| **macOS Intel (x64)** | **Beta &rarr; Stable** | Verified on physical or runner `macos-15-intel`: clean cold start, InsightFace ONNX dylib linking, zero crash on launch. |
| **Linux x64** | **Beta &rarr; Stable** | Verified on Ubuntu 22.04 / 24.04 with WebKitGTK 4.0 / 4.1: headless smoke test under Xvfb passes, GUI runs on local display. |

---

## 3. Release Artifact Generation & Checksums

- [ ] Build release packages:
  ```powershell
  python scripts/package_release.py --version <version>
  ```
- [ ] Inspect generated archives in `dist_release/`:
  - `CatLog-<version>-windows-x64.zip`
  - `CatLog-<version>-windows-x64-onefile.zip`
  - `CatLog-Setup-<version>.exe` (if Inno Setup compiler is present)
  - `SHA256SUMS.txt`
- [ ] Verify `SHA256SUMS.txt` against computed hashes:
  ```powershell
  Get-FileHash dist_release/* -Algorithm SHA256
  ```

---

## 4. Git Tagging & GitHub Release Publishing

- [ ] Verify clean git state on `main`:
  ```powershell
  git status
  ```
- [ ] Create and push signed git tag:
  ```powershell
  git tag -a v<version> -m "Release v<version>"
  git push origin v<version>
  ```
- [ ] Monitor GitHub Actions release workflow:
  `.github/workflows/release.yml`
- [ ] Review published GitHub Release:
  - Verify release notes match `RELEASE_NOTES.md`.
  - Verify all 4 platform archives + checksums are attached.
  - Verify in-app update checker (`/api/app/check-update`) detects the new release online.

