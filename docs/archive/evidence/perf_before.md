# CatLog Baseline Performance Measurements (Before Optimization)

**Date**: 2026-10-18  
**Dataset**: Canonical 259-photo dataset (`scratch/photos_259`)  
**Raw JSON**: `scratch/perf_before.json`  
**Raw SHA-256**: `91821a68e0d15ef029d08a39dfed355b1bce355436a3cf5d9986e89f45cb9ef5`  

---

## 1. Executive Summary Table

| Metric | Measured Baseline (Before) | Invariant / Target Status |
| :--- | :---: | :--- |
| **Executable Size** | 171,065,458 bytes (163.14 MB) | `photosorter.exe` (onefile) |
| **Cold Startup Time (3 runs)** | 11.934 s, 11.778 s, 29.640 s | **17.784 s average** |
| **Time to Open Saved Project** | **10.92 ms** (min: 6.51 ms) | Instant deserialization |
| **Full Run Total Pipeline (259 photos)** | **1050.440 s** (~17.5 min) | End-to-end cold cache |
| **Throughput** | **4.056 s/photo** | Across all 259 photos |
| **Peak RAM** | **920.21 MB** (964,915,200 bytes) | Monitored via psutil |
| **Frontend Bundle (gzip)** | JS: 108,464 B \| CSS: 14,826 B | Total: 123,290 B gzip (120.4 KB) |
| **Viewer Bundle (gzip)** | JS: 59,691 B \| CSS: 5,765 B | Total: 65,456 B gzip (63.9 KB) |
| **Export Folder Size** | 31,421,179 bytes (29.97 MB) | 898 files (`thumbs/`, `faces/`, metadata) |
| **Viewer First-Load Time** | **243.74 ms** (22 requests) | 1,753,301 bytes transferred |

---

## 2. Per-Stage Timing Breakdown (259 Photos / 1,701 Faces)

| Stage | Duration (seconds) | Share (%) | Notes |
| :--- | :---: | :---: | :--- |
| **Model Init** | 2.688 s | 0.3% | InsightFace FaceAnalysis & session init |
| **Decode** | 62.275 s | 5.9% | Sequential EXIF transpose & Pillow HEIF/JPEG decode |
| **Detect** | 75.904 s | 7.2% | SCRFD 10G on downscaled 1600px |
| **Embed** | 717.420 s | 68.3% | ArcFace ResNet100 + 3D 68-pt landmark per face |
| **Thumbs & Crops** | 57.834 s | 5.5% | PIL LANCZOS thumbnailing + 384px square crops (q=95) |
| **Clustering** | 4.468 s | 0.4% | Cosine matrix + 2-pass merge + disambiguation |
| **Export** | 7.928 s | 0.8% | File copying, JSON manifests, and static HTML generation |
| **Total Pipeline** | **1050.440 s** | **100.0%** | **4.056 s/photo** |

---

## 3. Baseline Invariant Reproduction

| Invariant Item | Target Count | Measured Count | Status |
| :--- | :---: | :---: | :---: |
| **People Clusters** | 192 | 192 | **PASS** |
| **Clustered Faces** | 1,256 | 1,256 | **PASS** |
| **Unrecognized Faces** | 445 | 445 | **PASS** |
| **Total Detected Faces** | 1,701 | 1,701 | **PASS** |
| **Unrecognized Photos** | 168 | 168 | **PASS** |
| **Total Photos** | 259 | 259 | **PASS** |
