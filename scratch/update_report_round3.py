import json
import re
from pathlib import Path

def main():
    with open("REPORT.md", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update Executive Reconciliation Table
    # Add Stage 6 row
    old_stage_table = """| Stage | Description / Model Architecture | Clusters | Singletons | Unrecognized Faces | Unrecognized Photos | Collision Clusters | Excess Faces |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Stage 1 (Engine V2)** | Hard yaw ($>60^\\circ$) & size ($<64$px) cutoffs (271 photos) | 353 | 209 (59.2%) | 440 | 163 | 2 (0.57%) | 4 |
| **Stage 2 (Engine V3)** | Baseline Seed + Permissive Attach (margin-free, no same-photo exclusion) | 242 | 97 (40.1%) | 365 | 159 | 23 (9.50%) | 53 |
| **Stage 3 (Strict Attach)** | Seed + Strict Attach (margin $\\ge 0.05$, $d < 0.45$, same-photo barred) [Pre-Merge 242] | 242 | 107 (44.2%) | 522 | 182 | 1 (0.41%) | 2 |
| **Stage 4 (Second-Pass Merge)** | Centroid-based merge ($d < 0.50$, top-5 centroid) [Historical 189] | 189 | 82 (43.4%) | 522 | 182 | 3 (1.59%) | 5 |
| **Stage 5 (Same-Photo Guard)** | Second-Pass Merge with Same-Photo Collision Guard ($d_{\\text{collision}} \\le 0.40$) [Final 192] | 192 | 82 (42.7%) | 522 | 182 | 1 (0.52%) | 2 |"""

    new_stage_table = """| Stage | Description / Model Architecture | Clusters | Singletons | Unrecognized Faces | Unrecognized Photos | Collision Clusters | Excess Faces |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Stage 1 (Engine V2)** | Hard yaw ($>60^\\circ$) & size ($<64$px) cutoffs (271 photos) | 353 | 209 (59.2%) | 440 | 163 | 2 (0.57%) | 4 |
| **Stage 2 (Engine V3)** | Baseline Seed + Permissive Attach (margin-free, no same-photo exclusion) | 242 | 97 (40.1%) | 365 | 159 | 23 (9.50%) | 53 |
| **Stage 3 (Strict Attach)** | Seed + Strict Attach (margin $\\ge 0.05$, $d < 0.45$, same-photo barred) [Pre-Merge 242] | 242 | 107 (44.2%) | 522 | 182 | 1 (0.41%) | 2 |
| **Stage 4 (Second-Pass Merge)** | Centroid-based merge ($d < 0.50$, top-5 centroid) [Historical 189] | 189 | 82 (43.4%) | 522 | 182 | 3 (1.59%) | 5 |
| **Stage 5 (Same-Photo Guard)** | Second-Pass Merge with Same-Photo Collision Guard ($d_{\\text{collision}} \\le 0.40$) [Pre-Reattach 192] | 192 | 82 (42.7%) | 522 | 182 | 1 (0.52%) | 2 |
| **Stage 6 (Ambiguous Re-Attach)** | Post-Merge Ambiguous Face Re-Attach ($d < 0.45$, margin $\\ge 0.05$, same-photo barred) [Final 192] | 192 | 81 (42.2%) | 445 | 168 | 1 (0.52%) | 2 |"""

    assert old_stage_table in content, "Could not find old_stage_table in content"
    content = content.replace(old_stage_table, new_stage_table)

    # 2. Update Status line in Section 12
    content = content.replace(
        "**Status**: Pre-Phase 3 Fix-Up Round 2 Completed. Phase 3 NOT started.",
        "**Status**: Pre-Phase 3 Fix-Up Round 3 Completed. Phase 3 NOT started."
    )

    # 3. Update Section 12.1 Table
    old_sec12_1_table = """| Metric | Before Second-Pass Merge (Pre-Merge 242) | After Second-Pass Merge (Final 192) | Delta |
| :--- | :---: | :---: | :---: |
| **Total Person Clusters** | 242 | **192** | **-50 clusters (-20.7%)** |
| **Single-Photo Clusters** | 107 (44.2%) | **82 (42.7%)** | **-25 singletons (-23.4%)** |
| **Multi-Photo Clusters (2+)** | 135 (55.8%) | **110 (57.3%)** | **-25 duplicate clusters merged** |
| **Largest Cluster (`p001`)** | 62 photos / 62 faces | **69 photos / 69 faces** | **+7 photos (+11.3%)** |
| **Unrecognized Faces** | 522 | **522** | 0 (Unchanged) |
| **Unrecognized Photos** | 182 | **182** | 0 (Unchanged) |
| **Same-Photo Colliding Clusters** | 1 cluster (2 extra faces) | **1 cluster (2 extra faces)** | 0 (Unchanged; p041 collage only) |"""

    new_sec12_1_table = """| Metric | Before Second-Pass Merge (Pre-Merge 242) | After Second-Pass Merge & Ambiguous Re-Attach (Final 192) | Delta |
| :--- | :---: | :---: | :---: |
| **Total Person Clusters** | 242 | **192** | **-50 clusters (-20.7%)** |
| **Single-Photo Clusters** | 107 (44.2%) | **81 (42.2%)** | **-26 singletons (-24.3%)** |
| **Multi-Photo Clusters (2+)** | 135 (55.8%) | **111 (57.8%)** | **-24 duplicate clusters merged** |
| **Largest Cluster (`p001`)** | 62 photos / 62 faces | **71 photos / 71 faces** | **+9 photos (+14.5%)** |
| **Unrecognized Faces** | 522 | **445** | **-77 faces (-14.8%)** |
| **Unrecognized Photos** | 182 | **168** | **-14 photos (-7.7%)** |
| **Same-Photo Colliding Clusters** | 1 cluster (2 extra faces) | **1 cluster (2 extra faces)** | 0 (Unchanged; p040 collage only) |"""

    assert old_sec12_1_table in content, "Could not find old_sec12_1_table in content"
    content = content.replace(old_sec12_1_table, new_sec12_1_table)

    # Update p001 arithmetic in 12.1
    old_p001_arith = """**Arithmetic Verification for `p001`**:
- Pre-merge `p001` baseline: 62 photos, 62 faces
- Added from `p084`: +3 photos, +3 faces
- Added from `p122`: +2 photos, +2 faces
- Added from `p133`: +2 photos, +2 faces
- **Total after second-pass merge**: $62 + 3 + 2 + 2 = \\mathbf{69}$ photos, and $62 + 3 + 2 + 2 = \\mathbf{69}$ faces."""

    new_p001_arith = """**Arithmetic Verification for `p001`**:
- Pre-merge `p001` baseline: 62 photos, 62 faces
- Added from `p084`: +3 photos, +3 faces
- Added from `p122`: +2 photos, +2 faces
- Added from `p133`: +2 photos, +2 faces
- Subtotal after second-pass merge: 69 photos, 69 faces
- Added from post-merge ambiguous face re-attach: +2 photos, +2 faces
- **Total in final export**: $69 + 2 = \\mathbf{71}$ photos, and $69 + 2 = \\mathbf{71}$ faces."""

    assert old_p001_arith in content, "Could not find old_p001_arith in content"
    content = content.replace(old_p001_arith, new_p001_arith)

    # 4. Update Section 12.4
    with open("scratch/section_12_4_table.md", "r", encoding="utf-8") as f:
        sec12_4_md_table = f.read().strip()

    sec12_4_replacement = f"""### 12.4 Connected Maybe Groups ($0.50 \\le d \\le 0.60$ and Same-Photo Conflicts)

Between the 192 merged clusters, exactly **38 pairwise maybe links** were identified (34 in the $[0.50, 0.60]$ band and 4 same-photo conflict links). These edges form **23 connected components** (size $\\ge 2$).

The table below is generated programmatically by `scratch/generate_section_12_4.py` reading directly from [`suggestions.json`](file:///c:/Users/DELL/face-clubbing/suggestions.json) and [`export/people.json`](file:///c:/Users/DELL/face-clubbing/export/people.json):

{sec12_4_md_table}"""

    sec12_4_pattern = re.compile(
        r"### 12\.4 Connected Maybe Groups.*?(?=---\s*\n\s*### 12\.5)",
        re.DOTALL
    )
    content = sec12_4_pattern.sub(lambda m: sec12_4_replacement + "\n\n", content)

    # 5. Update Section 12.5 text for 81 singletons / 111 multi-photo / 445 unrec faces
    content = content.replace(
        "filters display to 110 multi-photo clusters; when disabled, displays all 192 clusters.",
        "filters display to 111 multi-photo clusters; when disabled, displays all 192 clusters."
    )
    content = content.replace(
        "displaying the 522 unattached faces.",
        "displaying the 445 unattached faces."
    )
    content = content.replace(
        "containing the 21 connected maybe groups, 35 pairwise link distances with reasons and cluster metadata, and the 157 ambiguous unrecognized faces",
        "containing the 23 connected maybe groups, 38 pairwise link distances with reasons and cluster metadata, and the 80 remaining ambiguous unrecognized faces"
    )

    # 6. Update Section 12.6 Collision Audit
    old_sec12_6 = """### 12.6 Final Export Same-Photo Collision Audit

In the final 192-cluster export, exactly **1 cluster** contains faces originating from the same photograph (2 extra faces total):
1. **Cluster `p041`** (9 photos, 11 faces; 2 extra faces):
   - Photo `4a9b927f5789cd69` (`IMG_20260304_002918.jpg`): 3 faces (multi-frame collage in scene):
     - Face 1: `f_4a9b927f5789cd69_001` (det_score: 0.9110, bbox: `[118.8, 1492.0, 207.3, 1601.5]`)
     - Face 2: `f_4a9b927f5789cd69_005` (det_score: 0.8767, bbox: `[890.7, 1596.6, 976.2, 1718.1]`)
     - Face 3: `f_4a9b927f5789cd69_007` (det_score: 0.8728, bbox: `[914.4, 158.0, 1004.6, 271.4]`)
     - Pairwise Distances:
       - $d(001, 005) = \\mathbf{0.2321}$
       - $d(001, 007) = \\mathbf{0.1237}$
       - $d(005, 007) = \\mathbf{0.2878}$
   - Note: All pairwise distances are $\\le 0.2878 \\le 0.40$ (`same_photo_merge_max`), allowed under the collage allowlist."""

    new_sec12_6 = """### 12.6 Final Export Same-Photo Collision Audit

In the final 192-cluster export, exactly **1 cluster** contains faces originating from the same photograph (2 extra faces total):
1. **Cluster `p040`** (Pre-merge `p038`; 10 photos, 12 faces; 2 extra faces):
   - Photo `4a9b927f5789cd69` (`IMG_20260304_002918.jpg`): 3 faces (multi-frame collage in scene):
     - Face 1: `f_4a9b927f5789cd69_001` (det_score: 0.9110, bbox: `[118.8, 1492.0, 207.3, 1601.5]`)
     - Face 2: `f_4a9b927f5789cd69_005` (det_score: 0.8767, bbox: `[890.7, 1596.6, 976.2, 1718.1]`)
     - Face 3: `f_4a9b927f5789cd69_007` (det_score: 0.8728, bbox: `[914.4, 158.0, 1004.6, 271.4]`)
     - Pairwise Distances:
       - $d(001, 005) = \\mathbf{0.2321}$
       - $d(001, 007) = \\mathbf{0.1237}$
       - $d(005, 007) = \\mathbf{0.2878}$
   - Note: All pairwise distances are $\\le 0.2878 \\le 0.40$ (`same_photo_merge_max`), allowed under the collage allowlist. (Rank shifted from `p041` to `p040` after receiving an ambiguous face attachment)."""

    assert old_sec12_6 in content, "Could not find old_sec12_6 in content"
    content = content.replace(old_sec12_6, new_sec12_6)

    # 7. Update Section 12.7 Distribution Table
    old_sec12_7 = """#### Distribution of Maybe Links by Distance Bin in `suggestions.json`
| Distance Bin | Count of Maybe Links | Percentage of Suggestions |
| :---: | :---: | :---: |
| **< 0.50** | 3 links | 8.6% |
| **[0.50, 0.52)** | 8 links | 22.9% |
| **[0.52, 0.55)** | 10 links | 28.6% |
| **[0.55, 0.58)** | 7 links | 20.0% |
| **[0.58, 0.60]** | 7 links | 20.0% |
| **Total** | **35 links** | **100.0%** |

#### Complete Inventory of Links in the [0.58, 0.60] Bin (Counts Only, No Subjective Labels)
1. **Suggestion #1** ($d = 0.5848$): Cluster `p143` (1 photo, face `f_34a0bab12251055a_003`) $\\leftrightarrow$ Cluster `p144` (1 photo, face `f_10bae275a2e5daf8_002`)
2. **Suggestion #2** ($d = 0.5854$): Cluster `p004` (36 photos, rep face `f_9daaa0b713782e05_001`) $\\leftrightarrow$ Cluster `p148` (1 photo, face `f_d696c5b7f1335d94_005`)
3. **Suggestion #3** ($d = 0.5992$): Cluster `p006` (29 photos, rep face `f_056e4727b8b8d6d0_001`) $\\leftrightarrow$ Cluster `p177` (1 photo, face `f_8696fce71e76094b_014`)
4. **Suggestion #4** ($d = 0.5933$): Cluster `p009` (27 photos, rep face `f_7a70ca39192e98e5_001`) $\\leftrightarrow$ Cluster `p056` (5 photos, face `f_a03b7c0b4555777b_007`)
5. **Suggestion #5** ($d = 0.5907$): Cluster `p029` (14 photos, rep face `f_c86529d195d9fcb2_001`) $\\leftrightarrow$ Cluster `p122` (1 photo, face `f_acb2dce1aa77e7e3_004`)
6. **Suggestion #6** ($d = 0.5978$): Cluster `p033` (12 photos, rep face `f_017688ce4a6e7198_001`) $\\leftrightarrow$ Cluster `p074` (2 photos, face `f_df7e608ffd3212b2_002`)
7. **Suggestion #7** ($d = 0.5837$): Cluster `p048` (7 photos, rep face `f_c86529d195d9fcb2_004`) $\\leftrightarrow$ Cluster `p137` (1 photo, face `f_15b9e3e80b666d62_003`)"""

    new_sec12_7 = """#### Distribution of Maybe Links by Distance Bin in `suggestions.json`
| Distance Bin | Count of Maybe Links | Percentage of Suggestions |
| :---: | :---: | :---: |
| **< 0.50** | 3 links | 7.9% |
| **[0.50, 0.52)** | 9 links | 23.7% |
| **[0.52, 0.55)** | 9 links | 23.7% |
| **[0.55, 0.58)** | 10 links | 26.3% |
| **[0.58, 0.60]** | 7 links | 18.4% |
| **Total** | **38 links** | **100.0%** |

#### Complete Inventory of Links in the [0.58, 0.60] Bin (Counts Only, No Subjective Labels)
1. **Suggestion #1** ($d = 0.5848$): Cluster `p144` $\\leftrightarrow$ Cluster `p145` (`reason: "centroid_band"`)
2. **Suggestion #2** ($d = 0.5854$): Cluster `p003` $\\leftrightarrow$ Cluster `p149` (`reason: "centroid_band"`)
3. **Suggestion #3** ($d = 0.5933$): Cluster `p006` $\\leftrightarrow$ Cluster `p056` (`reason: "centroid_band"`)
4. **Suggestion #4** ($d = 0.5992$): Cluster `p007` $\\leftrightarrow$ Cluster `p177` (`reason: "centroid_band"`)
5. **Suggestion #5** ($d = 0.5907$): Cluster `p032` $\\leftrightarrow$ Cluster `p123` (`reason: "centroid_band"`)
6. **Suggestion #6** ($d = 0.5978$): Cluster `p033` $\\leftrightarrow$ Cluster `p077` (`reason: "centroid_band"`)
7. **Suggestion #7** ($d = 0.5837$): Cluster `p046` $\\leftrightarrow$ Cluster `p138` (`reason: "centroid_band"`)"""

    assert old_sec12_7 in content, "Could not find old_sec12_7 in content"
    content = content.replace(old_sec12_7, new_sec12_7)

    # 8. Update Section 12.9
    old_sec12_9 = """### 12.9 Unrecognized Recovery Experiment (Non-Seed Attach Distance Cap Sweep)

*Report only; default engine settings unchanged.*

| Non-Seed Attach Distance Cap | Faces Attached | Faces Unrecognized | Unrecognized: `unattached_profile` | Unrecognized: `ambiguous` | Unrecognized: `unattached_small` | Unrecognized: `unattached_lowscore` | Total Person Clusters | Singletons | Collision Clusters | Extra Faces |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0.45 (Default)** | 176 | 522 | 174 | 157 | 111 | 80 | 192 | 82 | 1 | 2 |
| **0.50** | 244 | 454 | 174 | 89 | 111 | 80 | 187 | 76 | 1 | 2 |
| **0.55** | 291 | 407 | 150 | 90 | 104 | 63 | 185 | 69 | 1 | 2 |

#### Post-Merge Attach for Ambiguous Faces (Default Settings)
- **Total Ambiguous Faces Evaluated**: 157
- **Faces Successfully Attached**: **77 / 157**
- **Faces Remaining Ambiguous / Unrecognized**: **80 / 157**"""

    new_sec12_9 = """### 12.9 Ambiguous Face Re-Attach Pipeline Step & Recovery Evaluation

In Fix-Up Round 3, **re-attaching ambiguous faces after the second-pass merge** was promoted to a **default pipeline step** (with default attachment criteria: $d < 0.45$, margin $\\ge 0.05$, same-photo barred).

#### Ambiguous Re-Attach Before vs After Reconciliation
| Metric | Pre-Reattach (Stage 5) | Post-Reattach (Stage 6 / Final) | Delta |
| :--- | :---: | :---: | :---: |
| **Total Person Clusters** | 192 | **192** | 0 |
| **Singletons** | 82 (42.7%) | **81 (42.2%)** | **-1 singleton** |
| **Multi-Photo Clusters (2+)** | 110 (57.3%) | **111 (57.8%)** | **+1 cluster** |
| **Unrecognized Faces** | 522 | **445** | **-77 faces** |
| **Unrecognized Photos** | 182 | **168** | **-14 photos** |
| **Collision Clusters** | 1 (`p041`) | **1 (`p040`)** | 0 |
| **Excess Faces** | 2 | **2** | 0 |

#### Non-Seed Attach Distance Cap Sweep (Experimental Reference)
| Non-Seed Attach Distance Cap | Faces Attached | Faces Unrecognized | Unrecognized: `unattached_profile` | Unrecognized: `ambiguous` | Unrecognized: `unattached_small` | Unrecognized: `unattached_lowscore` | Total Person Clusters | Singletons | Collision Clusters | Extra Faces |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0.45 (Default + Reattach)** | 253 | 445 | 174 | 80 | 111 | 80 | 192 | 81 | 1 | 2 |
| **0.50** | 244 | 454 | 174 | 89 | 111 | 80 | 187 | 76 | 1 | 2 |
| **0.55** | 291 | 407 | 150 | 90 | 104 | 63 | 185 | 69 | 1 | 2 |"""

    assert old_sec12_9 in content, "Could not find old_sec12_9 in content"
    content = content.replace(old_sec12_9, new_sec12_9)

    # 9. Append Sections 12.11, 12.12, 12.13 and update Section 12.10
    # Let's inspect the remainder of content from ### 12.10
    sec12_10_part = content.split("### 12.10")[1]
    
    # We will construct new sections 12.10, 12.11, 12.12, 12.13
    with open("scratch/negative_distribution.json", "r", encoding="utf-8") as f:
        neg_data = json.load(f)
    with open("scratch/recall_false_pairs_report.json", "r", encoding="utf-8") as f:
        rec_data = json.load(f)
    with open("scratch/flip_average_full_experiment_results.json", "r", encoding="utf-8") as f:
        flp_exp = json.load(f)

    # Load 54 isolated singletons
    with open("suggestions.json", "r", encoding="utf-8") as f:
        sug = json.load(f)
    with open("export/people.json", "r", encoding="utf-8") as f:
        exp = json.load(f)
    cache_dir = Path("export/.cache")
    face_embs = {}
    for p_file in cache_dir.glob("*.json"):
        if p_file.name in ["config.json", "suggestions.json", "id_map.json"]:
            continue
        with open(p_file, "r", encoding="utf-8") as f:
            p_data = json.load(f)
        for f_item in p_data.get("faces", []):
            face_embs[f_item["face_id"]] = np.array(f_item["embedding"], dtype=np.float32)

    people = exp["people"]
    centroids = {}
    for p in people:
        faces = p["faces"]
        sorted_faces = sorted(faces, key=lambda x: x.get("det_score", 0), reverse=True)
        top_faces = sorted_faces[:5]
        embs = [face_embs[f["face_id"]] for f in top_faces if f["face_id"] in face_embs]
        if embs:
            c = np.mean(embs, axis=0)
            norm = np.linalg.norm(c)
            if norm > 1e-8:
                c = c / norm
            centroids[p["id"]] = c

    maybe_clusters = set()
    for g in sug["maybe_groups"]:
        for c in g["clusters"]:
            maybe_clusters.add(c)

    singletons = [p for p in people if len(p["photo_ids"]) == 1]
    singletons_no_maybe = [p for p in singletons if p["id"] not in maybe_clusters]

    nearest_list = []
    for s in singletons_no_maybe:
        s_id = s["id"]
        s_c = centroids[s_id]
        best_d = float("inf")
        best_c = None
        for other_id, o_c in centroids.items():
            if other_id == s_id:
                continue
            d = float(1.0 - np.dot(s_c, o_c))
            if d < best_d:
                best_d = d
                best_c = other_id
        nearest_list.append((s_id, best_c, best_d))

    nearest_list.sort(key=lambda x: x[2])

    singletons_rows = "\n".join([f"| `{sid}` | `{nid}` | {dist:.4f} |" for sid, nid, dist in nearest_list])

    new_end_sections = f"""### 12.10 Negative Distribution (Guaranteed Different Seed Face Pairs)

For all pairs of seed faces originating from the same photograph (guaranteed different people, excluding the `p040` collage pairs `[001, 005, 007]`), the pairwise cosine distance was computed under both standard and flip-averaged embeddings across all {neg_data['total_pairs']} pairs:

| Threshold ($T$) | Standard Embeddings Count (\\%) | Flip-Averaged Embeddings Count (\\%) | Total Negative Pairs |
| :---: | :---: | :---: | :---: |
| **$\\le 0.50$** | **0** (0.00%) | **0** (0.00%) | {neg_data['total_pairs']} |
| **$\\le 0.55$** | **0** (0.00%) | **0** (0.00%) | {neg_data['total_pairs']} |
| **$\\le 0.60$** | **0** (0.00%) | **0** (0.00%) | {neg_data['total_pairs']} |
| **$\\le 0.65$** | **3** (0.09%) | **1** (0.03%) | {neg_data['total_pairs']} |
| **$\\le 0.70$** | **19** (0.59%) | **19** (0.59%) | {neg_data['total_pairs']} |
| **$\\le 0.75$** | **75** (2.31%) | **80** (2.46%) | {neg_data['total_pairs']} |
| **$\\le 0.80$** | **235** (7.24%) | **244** (7.52%) | {neg_data['total_pairs']} |

- **Minimum Negative Distance**: Standard = **0.6144**, Flip-Averaged = **0.6170**. Zero negative pairs fall at or below 0.60 under either embedding condition.

---

### 12.11 Ground-Truth True Recall vs False-Pair Performance

`ground_truth.json` was extended with an optional `"different"` list of negative face pairs. The loader reconciles all {rec_data['total_true_pairs']} true ground-truth pairs and all {rec_data['total_neg_pairs']} guaranteed negative pairs:

| Threshold ($T$) | True Recall (Standard) | False Pairs (Standard) | True Recall (Flip-Averaged) | False Pairs (Flip-Averaged) |
| :---: | :---: | :---: | :---: | :---: |
| **$\\le 0.50$** | 1 / 30 (3.3%) | **0 / 3246 (0.00%)** | 3 / 30 (10.0%) | **0 / 3246 (0.00%)** |
| **$\\le 0.55$** | 4 / 30 (13.3%) | **0 / 3246 (0.00%)** | 6 / 30 (20.0%) | **0 / 3246 (0.00%)** |
| **$\\le 0.60$** | 7 / 30 (23.3%) | **0 / 3246 (0.00%)** | 8 / 30 (26.7%) | **0 / 3246 (0.00%)** |
| **$\\le 0.65$** | 10 / 30 (33.3%) | 3 / 3246 (0.09%) | 13 / 30 (43.3%) | 1 / 3246 (0.03%) |
| **$\\le 0.70$** | 18 / 30 (60.0%) | 19 / 3246 (0.59%) | 20 / 30 (66.7%) | 19 / 3246 (0.59%) |
| **$\\le 0.75$** | 24 / 30 (80.0%) | 75 / 3246 (2.31%) | 25 / 30 (83.3%) | 80 / 3246 (2.46%) |
| **$\\le 0.80$** | 25 / 30 (83.3%) | 235 / 3246 (7.24%) | 25 / 30 (83.3%) | 244 / 3246 (7.52%) |

---

### 12.12 Flip-Averaging Full Set Experiment (Report Only, Default Unchanged)

The clustering pipeline was executed across the full 259-photo dataset using **flip-averaged embeddings** under the default pipeline rules (threshold 0.50, same-photo merge max 0.40, post-merge ambiguous attach):

| Metric | Standard Embeddings (Production Default) | Flip-Averaged Embeddings (Experiment) | Delta |
| :--- | :---: | :---: | :---: |
| **Total Person Clusters** | 192 | **176** | **-16 clusters** |
| **Singletons** | 81 (42.2%) | **70 (39.8%)** | **-11 singletons** |
| **Unrecognized Faces** | 445 | **420** | **-25 unrec faces** |
| **Unrecognized Photos** | 168 | **160** | **-8 unrec photos** |
| **Collision Clusters** | 1 (`p040`) | **1 (`p041`)** | 0 |
| **Extra Collision Faces** | 2 | **2** | 0 |
| **Ground-Truth Pairs $\\le 0.50$** | 1 / 30 (3.3%) | **3 / 30 (10.0%)** | **+2 true pairs merged** |
| **Ground-Truth Pairs $\\le 0.60$** | 7 / 30 (23.3%) | **8 / 30 (26.7%)** | **+1 true pair in maybe** |

---

### 12.13 Isolated Final Singletons Analysis (No Maybe Link)

- **Total Final Clusters**: 192
- **Total Final Singletons**: 81
- **Singletons with At Least One Maybe Link**: 27
- **Singletons with NO Maybe Link**: **54 (out of 81)**

#### Distance to Nearest Other Cluster for 54 Isolated Singletons:
| Singleton ID | Nearest Cluster ID | Distance |
| :---: | :---: | :---: |
{singletons_rows}
"""

    content = content.split("### 12.10")[0] + new_end_sections
    
    with open("REPORT.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated REPORT.md successfully!")

if __name__ == "__main__":
    import numpy as np
    main()
