# Code-Signing, SmartScreen, and Gatekeeper Distribution Policy

This document records the official architectural decisions and operational guidance for CatLog application binaries distributed across Windows, macOS, and Linux (SPEC Revision 3 & BUILD_PLAN Phase V2-8).

---

## 1. Operating System Security Architecture

### Windows: SmartScreen & EV vs Standard Code Signing
1. **Windows SmartScreen Behavior**:
   - When an end user downloads and executes an unsigned binary or a newly released installer from GitHub Releases, Windows Defender SmartScreen displays a warning:
     > *"Windows protected your PC: Microsoft Defender SmartScreen prevented an unrecognized app from starting."*
   - Users can safely proceed by clicking **"More info"** &rarr; **"Run anyway"**.
2. **Code Signing Certificate Types**:
   - **Extended Validation (EV) Code Signing Certificate**:
     - *Cost*: ~$300 – $600 / year (requires hardware token or cloud HSM like Azure Key Vault / DigiCert ONE).
     - *Reputation*: Immediately establishes instant SmartScreen reputation without warnings.
   - **Standard (OV) Code Signing Certificate**:
     - *Cost*: ~$150 – $300 / year.
     - *Reputation*: Starts with neutral reputation; warnings disappear as download volume and reputation accumulate.
   - **SignPath Foundation / Open Source Signing**:
     - Open-source projects can qualify for free signing via SignPath.io if the project meets community activity and strict build pipeline isolation guidelines.
3. **Current CatLog Decision for Release Candidates (v0.1.0-rc1+)**:
   - **Decision**: CatLog is an open-source, non-profit community project built transparently on GitHub Actions. During the Release Candidate phase, we distribute unsigned binaries alongside cryptographic **SHA-256 checksums** (`SHA256SUMS.txt`).
   - All source code and build automation workflows (`.github/workflows/release.yml`) are 100% public and reproducible.
   - Documented bypass steps:
     1. Click **More info**.
     2. Verify publisher hash against published `SHA256SUMS.txt`.
     3. Click **Run anyway**.

---

## 2. macOS: Apple Gatekeeper & Notarization

1. **Gatekeeper Behavior**:
   - macOS blocks un-notarized applications downloaded from the internet with:
     > *"CatLog cannot be opened because the developer cannot be verified."*
2. **Requirements for Zero-Warning macOS Installation**:
   - Apple Developer Program Membership ($99 / year).
   - Code-signing with `Developer ID Application` certificate via `codesign`.
   - Apple Notarization ticket stapled via `xcrun notarytool` and `xcrun stapler`.
3. **Unsigned macOS Workaround for Users**:
   - Right-click (or Control-click) `CatLog.app` in Finder and select **Open**.
   - Click **Open** in the confirmation dialog.
   - Alternatively, remove the quarantine attribute in Terminal:
     ```bash
     xattr -d com.apple.quarantine /Applications/CatLog.app
     ```

---

## 3. Linux: WebKitGTK and Sandboxing

1. **Desktop Engine**:
   - CatLog uses `pywebview` with WebKitGTK on Linux.
   - Distributed as `CatLog-<version>-linux-x64.tar.gz`.
2. **Dependencies**:
   - Ubuntu 22.04 / 24.04: `libgl1`, `libglib2.0-0`, `gir1.2-webkit2-4.1`.
3. **Execution**:
   - Unpack archive and mark binary executable:
     ```bash
     tar -xzf CatLog-0.1.0-rc1-linux-x64.tar.gz
     cd CatLog
     chmod +x CatLog
     ./CatLog
     ```

---

## 4. In-App Version Update Privacy Policy

1. **No Auto-Install / No Telemetry**:
   - CatLog never downloads executable updates in the background.
   - CatLog never transmits analytics, device fingerprints, or attendee telemetry.
2. **GitHub Releases Query**:
   - CatLog checks `https://api.github.com/repos/Sufiyan-Shiraj/face-clubbing/releases/latest` with a 3.0s timeout.
   - If offline or unreachable, the check fails silently with zero interruption.
   - The user is presented with a non-intrusive link to review release notes on GitHub and download updates manually.

