# CatLog Archive & Historical Evidence

This directory contains archived experimental artifacts, audit logs, performance benchmarks, and visual verification screenshots gathered during the development and optimization of CatLog.

## Structure

- **`screenshots/`**: Visual evidence captures from desktop review, mobile viewports, full-size lightboxes, and static viewer galleries across testing phases.
  - `01_top_of_page.png` through `06_person_without_drive_link.png`: Static gallery visual checks.
  - `desktop_person_p001*.png`: Desktop lightbox and attendee modal verification.
  - `desktop_unified_grid*.png`: Unified people grid with singleton visibility toggles.
  - `review_*.png`: Saved project reopening, read-only banner indicators, and source photo resolution.
  - `viewer_*.png`: Public static viewer layout, direct download triggers, and multi-photo select mode.
- **`evidence/`**: Quantitative verification reports and benchmark measurements:
  - `audit_step0_raw.json`: Complete repository baseline audit (counts, commits, fixtures).
  - `perf_before.json` / `perf_before.md`: Baseline benchmark measurements before engine optimizations.
  - `perf_after.json` / `perf_comparison.md`: Comparative post-optimization profiling results demonstrating a 43.1% speedup in end-to-end clustering pipeline.
  - `recall_false_pairs_report.json`: Verification of clustering precision ($F_1 = 0.999$, zero false pair violations).
  - `report_metrics.json` / `v2_metrics.json` / `stats_271.json`: Intermediate evaluation matrices across the 271-file test dataset.
