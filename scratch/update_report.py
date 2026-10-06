import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def update_report():
    report_path = Path("REPORT.md")
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Top of file: Add Executive Stage Reconciliation Table and ID Numbering Note
    reconciliation_table = """# Phase 0 & 1 Verification & Re-Verification Report (Engine V2)

**Date**: 2026-10-06  
**Project**: Face Sorting Engine (`face-clubbing`)  
**Status**: Pre-Phase 3 Fix-Up Round Completed. Phase 3 NOT started.  

---

## EXECUTIVE ENGINE STAGE RECONCILIATION TABLE

The table below reconciles all key clustering metrics across the four development stages of the clustering engine on the complete 271-photo dataset (259 unique photo records):

| Stage | Description / Model Architecture | Clusters | Singletons | Unrecognized Faces | Unrecognized Photos | Collision Clusters | Excess Faces |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Stage 1 (Engine V2)** | Hard yaw ($>60^\\circ$) & size ($<64$px) cutoffs (271 photos) | 353 | 209 (59.2%) | 440 | 163 | 2 (0.57%) | 4 |
| **Stage 2 (Engine V3)** | Baseline Seed + Permissive Attach (margin-free, no same-photo exclusion) | 242 | 97 (40.1%) | 365 | 159 | 23 (9.50%) | 53 |
| **Stage 3 (Strict Attach)** | Seed + Strict Attach (margin $\\ge 0.05$, $d < 0.45$, same-photo barred) [Pre-Merge 242] | 242 | 107 (44.2%) | 522 | 182 | 1 (0.41%) | 2 |
| **Stage 4 (Second-Pass Merge)** | Centroid-based merge ($d < 0.50$, top-5 centroid) [Final 189] | 189 | 82 (43.4%) | 522 | 182 | 3 (1.59%) | 5 |

---

"""

    # Replace top header up to ## 1. CODE ANSWERS
    idx_sec1 = content.find("## 1. CODE ANSWERS (NO GUESSING)")
    if idx_sec1 != -1:
        content = reconciliation_table + content[idx_sec1:]

    # 2. Add ID numbering note to top of every section
    # Section 1
    content = content.replace(
        "## 1. CODE ANSWERS (NO GUESSING)\n",
        "## 1. CODE ANSWERS (NO GUESSING)\n\n> **ID Numbering Context**: N/A (Code and Photo Dimension Analysis)\n"
    )
    # Section 2
    content = content.replace(
        "## 2. BEFORE / AFTER COMPARISON (RE-RUN METRICS)\n",
        "## 2. BEFORE / AFTER COMPARISON (RE-RUN METRICS)\n\n> **ID Numbering Context**: Uses V1 / V2 Numbering (59 test photos)\n"
    )
    # Section 3
    content = content.replace(
        "## 3. THRESHOLD SWEEP & SAME-PHOTO COLLISION DIAGNOSTIC\n",
        "## 3. THRESHOLD SWEEP & SAME-PHOTO COLLISION DIAGNOSTIC\n\n> **ID Numbering Context**: Uses V2 Numbering (59 test photos)\n"
    )
    # Section 4
    content = content.replace(
        "## 4. NEAR-DUPLICATE PHOTO ANALYSIS (PERCEPTUAL HASHING)\n",
        "## 4. NEAR-DUPLICATE PHOTO ANALYSIS (PERCEPTUAL HASHING)\n\n> **ID Numbering Context**: N/A (Perceptual Hashing on Photo Files)\n"
    )
    # Section 5
    content = content.replace(
        "## 5. BORDER FACE CROPS & THE `p138` INVESTIGATION\n",
        "## 5. BORDER FACE CROPS & THE `p138` INVESTIGATION\n\n> **ID Numbering Context**: Uses V1 / V2 Numbering\n"
    )
    # Section 6
    content = content.replace(
        "## 6. VISUAL INSPECTION OF CONTACT SHEETS (`report_assets_v2/`)\n",
        "## 6. VISUAL INSPECTION OF CONTACT SHEETS (`report_assets_v2/`)\n\n> **ID Numbering Context**: Uses V2 Numbering (59 test photos)\n"
    )
    # Section 7
    content = content.replace(
        "## 7. DEVIATIONS FROM SPEC.MD (DOCUMENTED)\n",
        "## 7. DEVIATIONS FROM SPEC.MD (DOCUMENTED)\n\n> **ID Numbering Context**: N/A (Specification Deviations)\n"
    )
    # Section 8
    content = content.replace(
        "## 8. FILES CREATED OR MODIFIED\n",
        "## 8. FILES CREATED OR MODIFIED\n\n> **ID Numbering Context**: N/A (File Inventory)\n"
    )
    # Section 9
    content = content.replace(
        "## 9. 271-PHOTO SCALE VERIFICATION (FULL DATASET BENCHMARK)\n",
        "## 9. 271-PHOTO SCALE VERIFICATION (FULL DATASET BENCHMARK)\n\n> **ID Numbering Context**: Uses V2 Numbering (271 photos)\n"
    )
    # Section 10
    content = content.replace(
        "## 10. ATTACH-ONLY CLUSTERING & EVIDENCE VERIFICATION (ENGINE V3)\n",
        "## 10. ATTACH-ONLY CLUSTERING & EVIDENCE VERIFICATION (ENGINE V3)\n\n> **ID Numbering Context**: Uses V3 Numbering (Baseline Attach, 242 clusters)\n"
    )
    # Section 11
    content = content.replace(
        "## 11. STRICT ATTACH RECONCILIATION & FINAL EVIDENCE REPORT\n",
        "## 11. STRICT ATTACH RECONCILIATION & FINAL EVIDENCE REPORT\n\n> **ID Numbering Context**: Uses Pre-Merge 242 Numbering\n"
    )

    # 3. Mark §10.3 suggestion-range statement as superseded
    content = content.replace(
        "- **Empirical Threshold Conclusion**: Purity remains $\\ge 80\\%$ up to distance 0.58, but degrades severely between 0.58 and 0.60. Keeping automatic clustering at 0.50 while offering merges up to 0.58 in `suggestions.json` is optimal.",
        """> **SUPERSEDED NOTE**: The suggestion-range statement below (offering merges up to 0.58 in `suggestions.json`) is **superseded by Section 12.4** (which establishes the 0.50–0.60 range, yielding 31 links across 20 groups). Furthermore, the 70% false merge measurement in the 0.58–0.60 bin was computed under average-linkage cluster distance on the V2 run, NOT top-5 centroid distance on the post-merge clusters; see §12.7.

- **Empirical Threshold Conclusion (Historical V2 Baseline)**: Purity remains $\\ge 80\\%$ up to distance 0.58, but degrades severely between 0.58 and 0.60 under average-linkage metric."""
    )

    # 4. Retract "Confirmed False Merge" verdicts on IMG_2415 pairs in §10.3 Part 3
    old_enlarged_text = """#### 3. Enlarged Inspection of Pairs #13, #19, #24, #32: [`report_assets_v4/contact_sheet_enlarged_pairs_13_24_32_19.jpg`](file:///c:/Users/DELL/face-clubbing/report_assets_v4/contact_sheet_enlarged_pairs_13_24_32_19.jpg)
Rendered with 4 enlarged face crops (150x150 px) per side:
- **Pair #13** ($d = 0.5068$): Side A (`IMG_2415.HEIC`, `IMG_2207.HEIC`, `IMG_2072.HEIC`, `IMG_2147.JPG`) vs Side B (`IMG_2169.HEIC`, `IMG_2207.HEIC`, `IMG_2072.HEIC`, `IMG_2182.JPG`). Side A is a subject wearing tinted glasses; Side B is a different subject with clear glasses and distinct head shape. **Confirmed False Merge**.
- **Pair #19** ($d = 0.5106$): Side A (`IMG_2311.HEIC`, `IMG_2203.JPG`, `IMG_2202.JPG`, `IMG_2270.HEIC`) vs Side B (`IMG_2155.JPG`, `IMG_2072.HEIC`, `IMG_2172.JPG`, `IMG_2074.HEIC`). Side A is a young subject with dark frames; Side B is a bearded subject without glasses. **Confirmed False Merge**.
- **Pair #24** ($d = 0.5123$): Side A (`IMG_2415.HEIC` cluster) vs Side B (`IMG_2372.HEIC`, `IMG_2280.HEIC`, `IMG_2290.HEIC`, `IMG_2339.HEIC`). Distinct male subject vs female subject. **Confirmed False Merge**.
- **Pair #32** ($d = 0.5159$): Side A (`IMG_2415.HEIC` cluster) vs Side B (`IMG_2372.HEIC` cluster). Distinct male subject vs female subject. **Confirmed False Merge**."""

    new_enlarged_text = """#### 3. Enlarged Inspection of Pairs #13, #19, #24, #32: [`report_assets_v4/contact_sheet_enlarged_pairs_13_24_32_19.jpg`](file:///c:/Users/DELL/face-clubbing/report_assets_v4/contact_sheet_enlarged_pairs_13_24_32_19.jpg)
Rendered with 4 enlarged face crops (150x150 px) per side:
- **Pair #13** ($d = 0.5068$): Side A (`IMG_2415.HEIC`, `IMG_2207.HEIC`, `IMG_2072.HEIC`, `IMG_2147.JPG`) vs Side B (`IMG_2169.HEIC`, `IMG_2207.HEIC`, `IMG_2072.HEIC`, `IMG_2182.JPG`). Side A subject wearing tinted glasses vs Side B subject with clear glasses. **Retraction**: Earlier label 'Confirmed False Merge' was an unverified subjective assertion; re-classified as **unverified by me, needs organizer eyes**.
- **Pair #19** ($d = 0.5106$): Side A (`IMG_2311.HEIC`, `IMG_2203.JPG`, `IMG_2202.JPG`, `IMG_2270.HEIC`) vs Side B (`IMG_2155.JPG`, `IMG_2072.HEIC`, `IMG_2172.JPG`, `IMG_2074.HEIC`). Distinct subjects; re-classified as **unverified by me, needs organizer eyes**.
- **Pair #24** ($d = 0.5123$): Side A (`IMG_2415.HEIC` cluster) vs Side B (`IMG_2417.HEIC` / `IMG_2372.HEIC` cluster). **Retraction**: Earlier verdict 'Confirmed False Merge (distinct male subject vs female subject)' is retracted. The face-to-face distance between `IMG_2415` (`f_23fc030f0bb086b3_004`) and `IMG_2417` (`f_d358e80f8872f6ef_004`) is **0.4792**, and the top-5 centroid distance is **0.3170** ($< 0.50$), causing automatic second-pass merging into `p001`. Re-classified as **unverified by me, needs organizer eyes**.
- **Pair #32** ($d = 0.5159$): Side A (`IMG_2415.HEIC` cluster) vs Side B (`IMG_2401.HEIC` cluster). **Retraction**: Earlier verdict 'Confirmed False Merge (distinct male subject vs female subject)' is retracted. Face-to-face distance between `IMG_2415` and `IMG_2401` is **0.5159**, and centroid distance is **0.3669** ($< 0.50$), causing automatic second-pass merging into `p001`. Re-classified as **unverified by me, needs organizer eyes**. See §12.1 for complete 6x6 pairwise numerical matrix."""

    content = content.replace(old_enlarged_text, new_enlarged_text)

    # 5. Mark §10.5 as superseded
    content = content.replace(
        "### 10.5 Viewer Enhancements Implemented\n",
        """### 10.5 Viewer Enhancements Implemented

> **SUPERSEDED NOTE**: Section 10.5 (two-section viewer with separate single-photo accordion) is **superseded by Section 12.5** (Unified People Grid with single-photo filter toggle and enhanced data model).

"""
    )

    # 6. Mark §11.3 as superseded
    content = content.replace(
        "### 11.3 Enhanced Merge Suggestions (`export/.cache/suggestions.json`)\n",
        """### 11.3 Enhanced Merge Suggestions (`export/.cache/suggestions.json`)

> **SUPERSEDED NOTE**: Section 11.3 (0.50–0.54 distance range, 35 suggestions) is **superseded by Section 12.4** (0.50–0.60 distance range, 31 pairwise links, 20 connected groups).

"""
    )

    # 7. Update Section 12 completely with verified information
    from scratch.generate_section_12_4 import generate_section_12_4
    sec_12_4_table = generate_section_12_4()

    section_12_text = f"""## 12. PHASE 2 PRE-RELEASE REFINEMENT: DUPLICATE REDUCTION & DATA MODEL UPDATE

> **ID Numbering Context**: Uses Final 189 Numbering (with explicit cross-references to Pre-Merge 242 cluster IDs).

**Date**: 2026-10-06  
**Test Set**: 271 physical files: 259 unique photo records (12 byte-duplicate .heif copies), 253 photos in at least one person cluster, 255 photos with at least one detected face, 4 photos with no detected face, and 6 photos in Unrecognized only (4 no-face plus 2 with only unrecognized faces).  
**Status**: Pre-Phase 3 Fix-Up Round Completed. Phase 3 NOT started.

---

### 12.1 Cluster & Singleton Reconciliation (Before vs After Second-Pass Merge)

A second-pass cluster merge was implemented:
- For each cluster, a normalized centroid vector $\\vec{{c}}$ was computed from its top-5 best faces only (ranked by highest `det_score` and face dimension $\\min(w, h)$).
- Clusters were compared pairwise by centroid cosine distance $d = 1.0 - \\vec{{c}}_A \\cdot \\vec{{c}}_B$.
- **Three Tiers**:
  1. $d < 0.50$: Auto-merged into connected components. Same-photo co-occurrences tracked as diagnostic only (legitimate for multi-shot collages).
  2. $0.50 \\le d \\le 0.60$: "Maybe" link (not merged; grouped into connected components for organizer review).
  3. $d > 0.60$: No action.

| Metric | Before Second-Pass Merge (Pre-Merge 242) | After Second-Pass Merge (Final 189) | Delta |
| :--- | :---: | :---: | :---: |
| **Total Person Clusters** | 242 | **189** | **-53 clusters (-21.9%)** |
| **Single-Photo Clusters** | 107 (44.2%) | **82 (43.4%)** | **-25 singletons (-23.4%)** |
| **Multi-Photo Clusters (2+)** | 135 (55.8%) | **107 (56.6%)** | **-28 duplicate clusters merged** |
| **Largest Cluster (`p001`)** | 62 photos / 62 faces | **69 photos / 69 faces** | **+7 photos (+11.3%)** |
| **Unrecognized Faces** | 522 | **522** | 0 (Unchanged) |
| **Unrecognized Photos** | 182 | **182** | 0 (Unchanged) |
| **Same-Photo Colliding Clusters** | 1 cluster (2 extra faces) | **3 clusters (5 extra faces)** | Diagnostic only (collages) |

#### Known Split Pairs Consolidation & ID Numbering Reconciliation
In earlier working notes, split pairs were referenced as `p080`, `p121`, and `p129`. In the final export, those IDs represent entirely different clusters (`p080` has 2 photos, `p121` is `IMG_2114.HEIC` alone, and `p129` is `IMG_2148.JPG` alone). In the pre-merge 242 numbering, these clusters were canonical IDs **`p084`**, **`p122`**, and **`p133`**.

All three clusters auto-merged into **`p001`** at centroid distances $< 0.50$:
1. **Pre-merge `p084`** (formerly referred to as `p080`; final `p001`):
   - Centroid distance to `p001`: **0.3170** ($< 0.50 \\rightarrow$ auto-merged into `p001`)
   - Added **3 photos and 3 faces**:
     - Photo `d358e80f8872f6ef` (`IMG_2417.HEIC`): face `f_d358e80f8872f6ef_004` (det_score: 0.7711, bbox: `[722.2, 1494.2, 1054.8, 1890.1]`)
     - Photo `e0ad7d5d2701102e` (`IMG_2267.HEIC`): face `f_e0ad7d5d2701102e_002` (det_score: 0.7788, bbox: `[3000.7, 1085.1, 3144.1, 1251.5]`)
     - Photo `e96a040cf77cd194` (`IMG_2150.HEIC`): face `f_e96a040cf77cd194_004` (det_score: 0.7570, bbox: `[2290.3, 1148.0, 2404.7, 1289.4]`)
2. **Pre-merge `p122`** (formerly referred to as `p121`; final `p001`):
   - Centroid distance to `p001`: **0.3713** ($< 0.50 \\rightarrow$ auto-merged into `p001`)
   - Added **2 photos and 2 faces**:
     - Photo `72100be076f21ac7` (`IMG_2161.JPG`): face `f_72100be076f21ac7_002` (det_score: 0.8284, bbox: `[2613.5, 1207.4, 2807.6, 1441.1]`)
     - Photo `f72c01c72c056c0f` (`IMG_2179.HEIC`): face `f_f72c01c72c056c0f_008` (det_score: 0.7523, bbox: `[2989.5, 1387.5, 3088.5, 1511.0]`)
3. **Pre-merge `p133`** (formerly referred to as `p129`; final `p001`):
   - Centroid distance to `p001`: **0.3669** ($< 0.50 \\rightarrow$ auto-merged into `p001`)
   - Added **2 photos and 2 faces**:
     - Photo `cd5cf1f9b616d68a` (`IMG_2401.HEIC`): face `f_cd5cf1f9b616d68a_009` (det_score: 0.7053, bbox: `[2577.0, 1355.4, 2653.0, 1447.6]`)
     - Photo `7739152de91187cf` (`IMG_2400.HEIC`): face `f_7739152de91187cf_010` (det_score: 0.5977, bbox: `[2654.5, 1431.4, 2724.9, 1519.1]`)

**Arithmetic Verification for `p001`**:
- Pre-merge `p001` baseline: 62 photos, 62 faces
- Added from `p084`: +3 photos, +3 faces
- Added from `p122`: +2 photos, +2 faces
- Added from `p133`: +2 photos, +2 faces
- **Total after second-pass merge**: $62 + 3 + 2 + 2 = \\mathbf{{69}}$ photos, and $62 + 3 + 2 + 2 = \\mathbf{{69}}$ faces.
- Backwards tracking: In `export/people.json`, person `p001` has `merged_from: ["p001", "p084", "p122", "p133"]` and `merged_from_numbering: "pre-merge 242"`. Complete mapping is published in [`id_map.json`](file:///c:/Users/DELL/face-clubbing/id_map.json).

#### Reconciliation of Earlier "False Merge" Verdicts
REPORT §10.3 previously labelled pairs involving `IMG_2415` vs `IMG_2179` ($d=0.5068$), vs `IMG_2417` ($d=0.5123$), and vs `IMG_2401` ($d=0.5159$) as "Confirmed False Merge (distinct male subject vs female subject)". In §12.1, those same faces auto-merged into `p001` at centroid distances 0.3170–0.3713.

**Honesty Rule Verdict**: These two claims cannot both be right. We plainly retract the earlier "confirmed" verdicts as unverified subjective assertions. They are now officially classified as **unverified by me, needs organizer eyes**.

To establish empirical transparency without subjective bias, the 6 constituent faces were extracted and evaluated with exact bounding boxes, detection scores, and a full 6x6 pairwise embedding cosine distance matrix:

| Face ID | Photo Filename | det_score | Bounding Box `[x1, y1, x2, y2]` |
| :--- | :--- | :---: | :--- |
| `f_23fc030f0bb086b3_004` | `IMG_2415.HEIC` | 0.8472 | `[889.5, 1149.6, 1192.2, 1492.9]` |
| `f_d358e80f8872f6ef_004` | `IMG_2417.HEIC` | 0.7711 | `[722.2, 1494.2, 1054.8, 1890.1]` |
| `f_72100be076f21ac7_002` | `IMG_2161.JPG` | 0.8284 | `[2613.5, 1207.4, 2807.6, 1441.1]` |
| `f_f72c01c72c056c0f_008` | `IMG_2179.HEIC` | 0.7523 | `[2989.5, 1387.5, 3088.5, 1511.0]` |
| `f_cd5cf1f9b616d68a_009` | `IMG_2401.HEIC` | 0.7053 | `[2577.0, 1355.4, 2653.0, 1447.6]` |
| `f_7739152de91187cf_010` | `IMG_2400.HEIC` | 0.5977 | `[2654.5, 1431.4, 2724.9, 1519.1]` |

##### 6x6 Pairwise Cosine Distance Table
| Face ID / Photo | IMG_2415 | IMG_2417 | IMG_2161 | IMG_2179 | IMG_2401 | IMG_2400 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `f_23fc030f0bb086b3_004` (IMG_2415) | 0.0000 | 0.4792 | 0.5125 | 0.4242 | 0.5159 | 0.4518 |
| `f_d358e80f8872f6ef_004` (IMG_2417) | 0.4792 | 0.0000 | 0.5209 | 0.4846 | 0.6306 | 0.5938 |
| `f_72100be076f21ac7_002` (IMG_2161) | 0.5125 | 0.5209 | 0.0000 | 0.4317 | 0.6438 | 0.6194 |
| `f_f72c01c72c056c0f_008` (IMG_2179) | 0.4242 | 0.4846 | 0.4317 | 0.0000 | 0.5557 | 0.6514 |
| `f_cd5cf1f9b616d68a_009` (IMG_2401) | 0.5159 | 0.6306 | 0.6438 | 0.5557 | 0.0000 | 0.4228 |
| `f_7739152de91187cf_010` (IMG_2400) | 0.4518 | 0.5938 | 0.6194 | 0.6514 | 0.4228 | 0.0000 |

Evidence contact sheet rendered with 260x260 px tiles: [`report_assets_v4/contact_sheet_split_pairs_reconciliation.jpg`](file:///c:/Users/DELL/face-clubbing/report_assets_v4/contact_sheet_split_pairs_reconciliation.jpg).

---

### 12.2 Default Configuration Status & Parameter Specifications

- **Flip-Averaged Embeddings**: **OFF by default** (`flip_average: False`).
  - The published 189-cluster export was generated using **standard embeddings** (189 clusters).
  - The flip-averaging experiment yielded 174 clusters (an experimental reduction of 15 clusters), but is not enabled in production.
- **Small Face Sharpening & Upscaling**: **OFF by default**.
  - Evaluated purely as a standalone research experiment in `scratch/run_b5_experiment.py`. It is disabled in the engine pipeline.
- **Configuration Keys & Defaults**:
  - **Engine Pipeline Configuration (`EngineConfig`)**:
    - `input_path`: `test_photos`
    - `output_dir`: `"export"`
    - `cache_dir`: `"export/.cache"`
    - `distance_threshold`: `0.50`
    - `min_det_score`: `0.50`
    - `min_face_size`: `64`
    - `max_yaw`: `70.0`
    - `seed_min_face_size`: `64`
    - `seed_max_yaw`: `60.0`
    - `seed_min_det_score`: `0.70`
    - `max_image_dim`: `1600`
    - `thumb_size`: `400`
    - `face_crop_size`: `256`
    - `second_pass_merge`: `True`
    - `merge_threshold`: `0.50`
    - `maybe_threshold`: `0.60`
    - `flip_average`: `False` (off)
    - `include_maybe`: `False` (off)
  - **Viewer Bundle Configuration (`export/config.json`)**:
    - `title`: `"Event Gallery"`
    - `subtitle`: `"Photos grouped by person"`
    - `logo`: `null`
    - `accent`: `"#2563eb"`
    - `font`: `"Inter"`
    - `footer`: `"Published with PhotoSorter"`
    - `show_labels`: `true`
    - `include_maybe`: `false`

---

### 12.3 Small Faces Sharpening / Upscaling Experiment (B.5)

*Experiment only; off by default in engine config.*  
The effect of unsharp masking (Gaussian blur $\\sigma=2.0$, weight $1.5$, subtraction $-0.5$) and bicubic upscaling ($2\\times$ cubic upsampling + unsharp mask) on faces under 112 px was measured on the known split pairs (`p001` vs `p084`, `p122`, `p133`). Centroid cosine distances:

| Pair Comparison | Without Enhancement (Baseline) | With Sharpening (Small Faces < 112px) | With Upscaling + Sharpening (< 112px) |
| :--- | :---: | :---: | :---: |
| **`p001` vs `p084`** | **0.3170** | **0.3170** (+0.0000) | **0.3170** (+0.0000) |
| **`p001` vs `p122`** | **0.3713** | **0.3709** (-0.0004) | **0.3696** (-0.0017) |
| **`p001` vs `p133`** | **0.3669** | **0.3695** (+0.0025) | **0.3688** (+0.0018) |

*Note*: In all three conditions, all three pairs remain well below the 0.50 threshold ($d < 0.38$) and merge into `p001`.

---

### 12.4 Connected Maybe Groups ($0.50 \\le d \\le 0.60$)

Between the 189 merged clusters, exactly **31 pairwise maybe links** were identified in the $[0.50, 0.60]$ cosine distance range. These edges form **20 connected components** (size $\\ge 2$).

The table below is generated programmatically by `scratch/generate_section_12_4.py` reading directly from [`suggestions.json`](file:///c:/Users/DELL/face-clubbing/suggestions.json) and [`export/people.json`](file:///c:/Users/DELL/face-clubbing/export/people.json):

{sec_12_4_table}

---

### 12.5 Data Model & Viewer UI Updates

1. **Viewer UI**:
   - **Unified People Grid**: Removed the two-section split. All 189 clusters are presented in a single grid sorted by photo count descending (`p001` with 69 photos down to `p189` with 1 photo).
   - **Hide Single-Photo People Toggle**: Added a toggle switch in the toolbar (off by default). When enabled, filters display to 107 multi-photo clusters; when disabled, displays all 189 clusters. No cluster is removed from the underlying data.
   - **Unrecognized Card**: Kept at the end of the unified grid, displaying the 522 unattached faces.
2. **Data Model**:
   - Each person record in [`export/people.json`](file:///c:/Users/DELL/face-clubbing/export/people.json) contains:
     - `photos`: Array of confirmed photo IDs.
     - `photo_ids`: Array of confirmed photo IDs (backwards-compatible; strictly equal to `photos`).
     - `faces`: List of detected face metadata.
     - `merged_from`: Array of constituent cluster IDs from pre-merge 242 numbering.
     - `merged_from_numbering`: `"pre-merge 242"`.
     - `maybe_photos`: Populated with `{{ photo_id, source_cluster, distance }}` only if `config.include_maybe` is `true` (default `false`).
   - [`id_map.json`](file:///c:/Users/DELL/face-clubbing/id_map.json): Complete dictionary mapping all 242 pre-merge IDs to final 189 IDs.
   - [`suggestions.json`](file:///c:/Users/DELL/face-clubbing/suggestions.json): Organizer-only file containing the 20 connected maybe groups and their pairwise link distances. Excluded from public export bundles.

---

### 12.6 Final Export Same-Photo Collision Audit

In the final 189-cluster export, exactly **3 clusters** contain faces originating from the same photograph (5 extra faces total):
1. **Cluster `p014`** (22 photos, 24 faces; 2 extra faces):
   - Photo `e25688a0ee978709` (`IMG_2093.HEIC`):
     - Face 1: `f_e25688a0ee978709_006` (det_score: 0.5604, bbox: `[388.7, 1275.5, 572.7, 1625.3]`)
     - Face 2: `f_e25688a0ee978709_003` (det_score: 0.7247, bbox: `[2897.1, 466.4, 3085.0, 704.5]`)
     - Pairwise Distance: **0.6478**
   - Photo `de8394820ab47c98` (`IMG_2225.JPG`):
     - Face 1: `f_de8394820ab47c98_008` (det_score: 0.6617, bbox: `[464.5, 1456.3, 608.3, 1750.0]`)
     - Face 2: `f_de8394820ab47c98_006` (det_score: 0.7501, bbox: `[2752.2, 1323.8, 2867.5, 1442.9]`)
     - Pairwise Distance: **0.8006**
2. **Cluster `p041`** (9 photos, 11 faces; 2 extra faces):
   - Photo `4a9b927f5789cd69` (`IMG_20260304_002918.jpg`): 3 faces (multi-frame collage in scene):
     - Face 1: `f_4a9b927f5789cd69_001` (det_score: 0.9110, bbox: `[118.8, 1492.0, 207.3, 1601.5]`)
     - Face 2: `f_4a9b927f5789cd69_005` (det_score: 0.8767, bbox: `[890.7, 1596.6, 976.2, 1718.1]`)
     - Face 3: `f_4a9b927f5789cd69_007` (det_score: 0.8728, bbox: `[914.4, 158.0, 1004.6, 271.4]`)
     - Pairwise Distances: $d(001, 005) = \\mathbf{{0.2321}}$, $d(001, 007) = \\mathbf{{0.1237}}$, $d(005, 007) = \\mathbf{{0.2878}}$.
3. **Cluster `p062`** (3 photos, 4 faces; 1 extra face):
   - Photo `df7e608ffd3212b2` (`IMG_20260304_080950.jpg`):
     - Face 1: `f_df7e608ffd3212b2_013` (det_score: 0.5846, bbox: `[794.4, 1221.0, 814.4, 1245.8]`)
     - Face 2: `f_df7e608ffd3212b2_008` (det_score: 0.7093, bbox: `[533.7, 1556.4, 558.5, 1587.2]`)
     - Pairwise Distance: **0.5349**

Evidence contact sheet rendered with 250x250 px tiles: [`report_assets_v4/contact_sheet_collision_audit.jpg`](file:///c:/Users/DELL/face-clubbing/report_assets_v4/contact_sheet_collision_audit.jpg).

---

### 12.7 Maybe-Tier Distance Reliability & Bin Breakdown

**Reliability Note**: The earlier §10.3 finding of 70% false merges in the $[0.58, 0.60]$ distance bin was measured under pairwise average-linkage cluster distance on the V2 clustering run, NOT top-5 centroid distance on the post-merge clusters. Historical purity numbers do not directly carry over to top-5 centroid distances.

#### Distribution of Maybe Links by Distance Bin in `suggestions.json`
| Distance Bin | Count of Maybe Links | Percentage of Suggestions |
| :---: | :---: | :---: |
| **[0.50, 0.52)** | 8 links | 25.8% |
| **[0.52, 0.55)** | 10 links | 32.3% |
| **[0.55, 0.58)** | 6 links | 19.4% |
| **[0.58, 0.60]** | 7 links | 22.6% |
| **Total** | **31 links** | **100.0%** |

#### Complete Inventory of Links in the [0.58, 0.60] Bin (Counts Only, No Subjective Labels)
1. **Suggestion #1** ($d = 0.5848$): Cluster `p140` (1 photo, `IMG_2181.JPG`, face `f_34a0bab12251055a_003`) $\\leftrightarrow$ Cluster `p141` (1 photo, `IMG_2182.JPG`, face `f_10bae275a2e5daf8_002`)
2. **Suggestion #2** ($d = 0.5854$): Cluster `p004` (36 photos, rep `IMG_2186.JPG`, face `f_9daaa0b713782e05_001`) $\\leftrightarrow$ Cluster `p145` (1 photo, `IMG_2218.JPG`, face `f_d696c5b7f1335d94_005`)
3. **Suggestion #3** ($d = 0.5992$): Cluster `p006` (29 photos, rep `IMG_2199.JPG`, face `f_8353ef3d4d422bcb_001`) $\\leftrightarrow$ Cluster `p174` (1 photo, `IMG_6745.JPG`, face `f_8696fce71e76094b_014`)
4. **Suggestion #4** ($d = 0.5933$): Cluster `p009` (27 photos, rep `IMG_2213.HEIC`, face `f_55d0c5bc79a5f5bc_002`) $\\leftrightarrow$ Cluster `p055` (5 photos, rep `IMG_2114.HEIC`, face `f_3a9077105f8e5efe_008`)
5. **Suggestion #5** ($d = 0.5907$): Cluster `p030` (14 photos, rep `IMG_2083.HEIC`, face `f_52909eb97d1ead92_002`) $\\leftrightarrow$ Cluster `p119` (1 photo, `IMG_2097.HEIC.heif`, face `f_acb2dce1aa77e7e3_004`)
6. **Suggestion #6** ($d = 0.5978$): Cluster `p033` (12 photos, rep `IMG_2105.HEIC`, face `f_017688ce4a6e7198_001`) $\\leftrightarrow$ Cluster `p073` (2 photos, rep `IMG_20260227_222103.jpg`, face `f_1b6a4cc85519b3a8_005`)
7. **Suggestion #7** ($d = 0.5837$): Cluster `p047` (7 photos, rep `IMG_2099.HEIC`, face `f_bae47e8229f3afde_002`) $\\leftrightarrow$ Cluster `p134` (1 photo, `IMG_2172.JPG`, face `f_15b9e3e80b666d62_003`)

Evidence contact sheet rendered with 250x250 px tiles: [`report_assets_v4/contact_sheet_maybe_bin_0.58_0.60.jpg`](file:///c:/Users/DELL/face-clubbing/report_assets_v4/contact_sheet_maybe_bin_0.58_0.60.jpg).

---

### 12.8 Programmatic Integrity Verification Results (`scratch/verify_final.py`)

The automated integrity check script [`scratch/verify_final.py`](file:///c:/Users/DELL/face-clubbing/scratch/verify_final.py) was executed directly against `export/people.json`, `suggestions.json`, `export/config.json`, and `REPORT.md`:

```text
PLACEHOLDER_VERIFY_OUTPUT
```
"""

    # Replace Section 12 using index
    idx_sec12 = content.find("## 12. PHASE 2 PRE-RELEASE REFINEMENT: DUPLICATE REDUCTION & DATA MODEL UPDATE")
    if idx_sec12 != -1:
        content = content[:idx_sec12] + section_12_text

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("Updated REPORT.md structure successfully!")

if __name__ == "__main__":
    update_report()
