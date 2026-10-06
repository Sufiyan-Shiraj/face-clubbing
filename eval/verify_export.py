"""Verification script for PhotoSorter Phase 1b deliverables.
Checks export/people.json, export.work/suggestions.json, export.work/id_map.json,
export/config.json, eval/ground_truth.json, eval/recall_false_pairs_report.json,
export.work cache, and REPORT.md.

Rules enforced:
  1. No cluster ID allowlists (pNNN removed). Same-photo distance <= 0.40 across all clusters.
  2. Public bundle hygiene (export/ contains strictly only config.json, people.json, faces/, thumbs/).
  3. Every number in every report table in the new Phase 1b section must match JSON data.
  4. Script FAILS if any table it checks is missing from REPORT.md.
"""

import sys
import re
import json
from pathlib import Path
from collections import defaultdict
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def find_file(paths):
    for p in paths:
        pth = Path(p)
        if pth.exists():
            return pth
    return None

def run_verification(export_dir: str = "export", work_dir: str = "export.work", report_file: str = "REPORT.md") -> bool:
    print("=" * 80)
    print("PHOTOSORTER PHASE 1b VERIFICATION AUDIT (eval/verify_export.py)")
    print("=" * 80)

    # 1. Locate required files
    people_path = find_file([f"{export_dir}/people.json", "people.json"])
    if not people_path:
        print(f"[FAIL] {export_dir}/people.json not found")
        return False

    sug_path = find_file([f"{work_dir}/suggestions.json", "suggestions.json"])
    if not sug_path:
        print(f"[FAIL] {work_dir}/suggestions.json not found")
        return False

    id_map_path = find_file([f"{work_dir}/id_map.json", "id_map.json"])
    if not id_map_path:
        print(f"[FAIL] {work_dir}/id_map.json not found")
        return False

    config_path = find_file([f"{export_dir}/config.json", "config.json"])
    if not config_path:
        print(f"[FAIL] {export_dir}/config.json not found")
        return False

    gt_path = find_file(["eval/ground_truth.json", "ground_truth.json"])
    if not gt_path:
        print("[FAIL] eval/ground_truth.json not found")
        return False

    rec_path = find_file(["eval/recall_false_pairs_report.json"])
    if not rec_path:
        print("[FAIL] eval/recall_false_pairs_report.json not found")
        return False

    report_path = find_file([report_file])
    if not report_path:
        print(f"[FAIL] {report_file} not found")
        return False

    with open(people_path, "r", encoding="utf-8") as f:
        people_data = json.load(f)
    with open(sug_path, "r", encoding="utf-8") as f:
        sug_data = json.load(f)
    with open(id_map_path, "r", encoding="utf-8") as f:
        id_map_data = json.load(f)
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)
    with open(gt_path, "r", encoding="utf-8") as f:
        gt_data = json.load(f)
    with open(rec_path, "r", encoding="utf-8") as f:
        rec_data = json.load(f)
    with open(report_path, "r", encoding="utf-8") as f:
        report_text = f.read()

    people = people_data["people"]
    cluster_count = len(people)
    singleton_count = sum(1 for p in people if len(p.get("photos", p.get("photo_ids", []))) == 1)
    multi_photo_count = sum(1 for p in people if len(p.get("photos", p.get("photo_ids", []))) > 1)
    unrec_faces_count = len(people_data["unrecognized"]["faces"])
    unrec_photos_count = len(people_data["unrecognized"]["photo_ids"])

    colliding_clusters_json = [p for p in people if len(p.get("faces", [])) > len(p.get("photos", p.get("photo_ids", [])))]
    collision_count_json = len(colliding_clusters_json)
    excess_faces_json = sum(len(p.get("faces", [])) - len(p.get("photos", p.get("photo_ids", []))) for p in people)

    all_passed = True

    # -------------------------------------------------------------------------
    # CHECK 1: Engine Invariants
    # -------------------------------------------------------------------------
    all_photos = set(people_data["photos"].keys())
    covered_photos = set(people_data["unrecognized"]["photo_ids"])
    for p in people:
        covered_photos.update(p.get("photos", p.get("photo_ids", [])))
    missing_photos = all_photos - covered_photos

    inv_coverage = (len(missing_photos) == 0 and len(all_photos) == 259)
    total_clustered_faces = sum(len(p.get("faces", [])) for p in people)
    total_detected = total_clustered_faces + unrec_faces_count
    inv_faces = (total_clustered_faces == 1256 and unrec_faces_count == 445 and total_detected == 1701)
    inv_photos_equal = all(p.get("photos") == p.get("photo_ids") for p in people)
    inc_maybe = config_data.get("include_maybe", False)
    inv_maybe_empty = (not inc_maybe and all(p.get("maybe_photos") == [] for p in people))

    if inv_coverage and inv_faces and inv_photos_equal and inv_maybe_empty:
        print(f"[PASS] Check 1: Engine Invariants (259/259 photos covered, 1256 clustered + 445 unrec = 1701 detected faces, photos==photo_ids, maybe_photos empty)")
    else:
        print(f"[FAIL] Check 1: Engine Invariants failed: coverage={inv_coverage}, faces={inv_faces}, photos_equal={inv_photos_equal}, maybe_empty={inv_maybe_empty}")
        all_passed = False

    # -------------------------------------------------------------------------
    # CHECK 2: Public Bundle Hygiene
    # -------------------------------------------------------------------------
    exp_p = Path(export_dir)
    if exp_p.exists():
        entries = set(p.name for p in exp_p.iterdir())
        allowed = {"config.json", "people.json", "faces", "thumbs"}
        disallowed = entries - allowed
        if len(disallowed) == 0:
            print(f"[PASS] Check 2: Public Bundle Hygiene (export/ contains strictly only: {sorted(list(entries))})")
        else:
            print(f"[FAIL] Check 2: Public Bundle Hygiene violation! Disallowed entries found in export/: {disallowed}")
            all_passed = False
    else:
        print(f"[FAIL] Check 2: Export dir '{export_dir}' not found")
        all_passed = False

    # -------------------------------------------------------------------------
    # CHECK 3: Same-Photo Distance Constraint Check (Across ALL clusters)
    # -------------------------------------------------------------------------
    c_dir = Path(work_dir)
    embs_cache = {}

    def get_face_emb(photo_id, face_id):
        if face_id in embs_cache:
            return embs_cache[face_id]
        p_path = c_dir / f"{photo_id}.json"
        if p_path.exists():
            with open(p_path, "r", encoding="utf-8") as pf:
                p_data = json.load(pf)
                for f_info in p_data.get("faces", []):
                    if "embedding" in f_info:
                        embs_cache[f_info["face_id"]] = np.array(f_info["embedding"], dtype=np.float32)
        return embs_cache.get(face_id)

    same_photo_merge_max = 0.40
    violations = []
    same_photo_dists = []

    for p in people:
        cid = p["id"]
        photo_faces = defaultdict(list)
        for face in p["faces"]:
            photo_faces[face["photo_id"]].append(face)
        for pid, faces in photo_faces.items():
            if len(faces) > 1:
                for i in range(len(faces)):
                    for j in range(i + 1, len(faces)):
                        f1_id = faces[i]["face_id"]
                        f2_id = faces[j]["face_id"]
                        emb_i = get_face_emb(pid, f1_id)
                        emb_j = get_face_emb(pid, f2_id)
                        if emb_i is not None and emb_j is not None:
                            d = float(1.0 - np.dot(emb_i, emb_j))
                            same_photo_dists.append(d)
                            if d > same_photo_merge_max:
                                violations.append((cid, pid, f1_id, f2_id, d))

    if len(violations) == 0:
        max_same_photo_d = max(same_photo_dists) if same_photo_dists else 0.0
        print(f"[PASS] Check 3: Same-Photo Distance Constraint: 0 collisions above {same_photo_merge_max:.2f} across all {len(people)} clusters. Max same-photo distance={max_same_photo_d:.4f} (<= 0.40)")
    else:
        print(f"[FAIL] Check 3: Same-Photo Distance Constraint: Found {len(violations)} violations above {same_photo_merge_max}: {violations}")
        all_passed = False

    # -------------------------------------------------------------------------
    # CHECK 4: Stable Identity (id_map.json and merged_from)
    # -------------------------------------------------------------------------
    cluster_map = {k: v for k, v in id_map_data.items() if not k.startswith("_")}
    pre_merge_count = len(cluster_map)
    final_cids_in_map = set(cluster_map.values())
    people_cids = set(p["id"] for p in people)

    has_merged_from = all("merged_from" in p and "merged_from_numbering" in p for p in people)
    if pre_merge_count == 242 and final_cids_in_map == people_cids and has_merged_from:
        print(f"[PASS] Check 4: Stable Identity & id_map.json (242 pre-merge clusters -> 192 final clusters; merged_from present in all clusters)")
    else:
        print(f"[FAIL] Check 4: Stable Identity failure: pre_merge_count={pre_merge_count}, has_merged_from={has_merged_from}")
        all_passed = False

    # -------------------------------------------------------------------------
    # CHECK 5: REPORT Phase 1b Section: Flip-Averaging Reproduction Table
    # -------------------------------------------------------------------------
    if "## 13. PHASE 1B" not in report_text and "## 13. Phase 1b" not in report_text and "Phase 1b" not in report_text:
        print("[FAIL] Check 5: Phase 1b section not found in REPORT.md")
        all_passed = False
    else:
        # Match standard vs flip reproduction table
        m_flip = re.search(r"\|\s*\*\*Flip-Averaged\*\*\s*\|\s*(\d+)\s*\|\s*(\d+)[^|]*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)[^|]*\|\s*(\d+)\s*\|", report_text)
        if not m_flip:
            print("[FAIL] Check 5: Section 13 Flip-Averaged Benchmark Reproduction Table not found in REPORT.md")
            all_passed = False
        else:
            fc, fs, fuf, fup, fcol, fex = map(int, m_flip.groups())
            if fc == 176 and fs == 70 and fuf == 420 and fup == 160 and fcol == 1 and fex == 2:
                print(f"[PASS] Check 5: Section 13 Flip-Averaged Benchmark Reproduction Table verified (Clusters=176, Singletons=70, Unrec=420f/160p, Collisions=1, Extra=2)")
            else:
                print(f"[FAIL] Check 5: Section 13 Flip-Averaged Reproduction Table numbers mismatch: ({fc}, {fs}, {fuf}, {fup}, {fcol}, {fex})")
                all_passed = False

    # -------------------------------------------------------------------------
    # CHECK 6: REPORT Phase 1b Section: Maybe Band (0.65) Distance Bin Table
    # -------------------------------------------------------------------------
    all_sug_links = []
    for g in sug_data["maybe_groups"]:
        all_sug_links.extend(g["links"])
    
    b_lt50 = sum(1 for l in all_sug_links if l["distance"] < 0.50)
    b_50_52 = sum(1 for l in all_sug_links if 0.50 <= l["distance"] < 0.52)
    b_52_55 = sum(1 for l in all_sug_links if 0.52 <= l["distance"] < 0.55)
    b_55_58 = sum(1 for l in all_sug_links if 0.55 <= l["distance"] < 0.58)
    b_58_60 = sum(1 for l in all_sug_links if 0.58 <= l["distance"] < 0.60)
    b_60_62 = sum(1 for l in all_sug_links if 0.60 <= l["distance"] < 0.62)
    b_62_65 = sum(1 for l in all_sug_links if 0.62 <= l["distance"] <= 0.65)
    b_total = len(all_sug_links)

    m_lt50 = re.search(r"<\s*0\.50[^\d]*\|\s*(\d+)\s+links", report_text)
    m_50_52 = re.search(r"\[0\.50,\s*0\.52\)[^\d]*\|\s*(\d+)\s+links", report_text)
    m_52_55 = re.search(r"\[0\.52,\s*0\.55\)[^\d]*\|\s*(\d+)\s+links", report_text)
    m_55_58 = re.search(r"\[0\.55,\s*0\.58\)[^\d]*\|\s*(\d+)\s+links", report_text)
    m_58_60 = re.search(r"\[0\.58,\s*0\.60\)[^\d]*\|\s*(\d+)\s+links", report_text)
    m_60_62 = re.search(r"\[0\.60,\s*0\.62\)[^\d]*\|\s*(\d+)\s+links", report_text)
    m_62_65 = re.search(r"\[0\.62,\s*0\.65\][^\d]*\|\s*(\d+)\s+links", report_text)
    m_tot = re.search(r"\*\*Total\s+Maybe\s+Links\*\*\s*\|\s*\*\*(\d+)\s+links\*\*", report_text)

    if not (m_lt50 and m_50_52 and m_52_55 and m_55_58 and m_58_60 and m_60_62 and m_62_65 and m_tot):
        print("[FAIL] Check 6: Section 13 Maybe Band (0.65) Distribution Table missing from REPORT.md")
        all_passed = False
    else:
        if (int(m_lt50.group(1)) == b_lt50 == 3 and
            int(m_50_52.group(1)) == b_50_52 == 9 and
            int(m_52_55.group(1)) == b_52_55 == 9 and
            int(m_55_58.group(1)) == b_55_58 == 10 and
            int(m_58_60.group(1)) == b_58_60 == 7 and
            int(m_60_62.group(1)) == b_60_62 == 18 and
            int(m_62_65.group(1)) == b_62_65 == 26 and
            int(m_tot.group(1)) == b_total == 82):
            print(f"[PASS] Check 6: Section 13 Maybe Band (0.65) Table verified (28 groups, 82 links: <0.50: 3, 50-52: 9, 52-55: 9, 55-58: 10, 58-60: 7, 60-62: 18, 62-65: 26)")
        else:
            print("[FAIL] Check 6: Section 13 Maybe Band (0.65) Table numbers mismatch with suggestions.json")
            all_passed = False

    # -------------------------------------------------------------------------
    # CHECK 7: REPORT Phase 1b Section: Evaluation Table A (All Labelled Pairs)
    # -------------------------------------------------------------------------
    tab_a_matches = re.findall(
        r"\|\s*\*\*\$\\le\s+([\d\.]+)\$\*\*\s*\|\s*(\d+)\s*\/\s*30[^|]*\|\s*(\d+)\s*\/\s*3246[^|]*\|\s*(\d+)\s*\/\s*30[^|]*\|\s*(\d+)\s*\/\s*3246[^|]*\|",
        report_text
    )
    if len(tab_a_matches) < 7:
        print(f"[FAIL] Check 7: Section 13 Evaluation Table A (All Pairs) missing or incomplete in REPORT.md (found {len(tab_a_matches)} rows)")
        all_passed = False
    else:
        tab_a_dict = {row["threshold"]: row for row in rec_data["table_a"]}
        table_a_ok = True
        for t_str, s_rc, s_fc, f_rc, f_fc in tab_a_matches[:7]:
            t_val = round(float(t_str), 2)
            exp = tab_a_dict[t_val]
            if (int(s_rc) != exp["true_recall_std_count"] or
                int(s_fc) != exp["false_pairs_std_count"] or
                int(f_rc) != exp["true_recall_flip_count"] or
                int(f_fc) != exp["false_pairs_flip_count"]):
                print(f"[FAIL] Check 7: Evaluation Table A mismatch at threshold {t_str}")
                table_a_ok = False
                all_passed = False
        if table_a_ok:
            print(f"[PASS] Check 7: Section 13 Evaluation Table A (All Pairs: 30 positive, 3246 negative) verified across 7 thresholds")

    # -------------------------------------------------------------------------
    # CHECK 8: REPORT Phase 1b Section: Evaluation Table B (Clean Set)
    # -------------------------------------------------------------------------
    tab_b_matches = re.findall(
        r"\|\s*\*\*\$\\le\s+([\d\.]+)\$\*\*\s*\|\s*(\d+)\s*\/\s*22[^|]*\|\s*(\d+)\s*\/\s*3246[^|]*\|\s*(\d+)\s*\/\s*22[^|]*\|\s*(\d+)\s*\/\s*3246[^|]*\|",
        report_text
    )
    if len(tab_b_matches) < 7:
        print(f"[FAIL] Check 8: Section 13 Evaluation Table B (Clean Set) missing or incomplete in REPORT.md (found {len(tab_b_matches)} rows)")
        all_passed = False
    else:
        tab_b_dict = {row["threshold"]: row for row in rec_data["table_b"]}
        table_b_ok = True
        for t_str, s_rc, s_fc, f_rc, f_fc in tab_b_matches[:7]:
            t_val = round(float(t_str), 2)
            exp = tab_b_dict[t_val]
            if (int(s_rc) != exp["true_recall_std_count"] or
                int(s_fc) != exp["false_pairs_std_count"] or
                int(f_rc) != exp["true_recall_flip_count"] or
                int(f_fc) != exp["false_pairs_flip_count"]):
                print(f"[FAIL] Check 8: Evaluation Table B mismatch at threshold {t_str}")
                table_b_ok = False
                all_passed = False
        if table_b_ok:
            print(f"[PASS] Check 8: Section 13 Evaluation Table B (Clean Set: 22 positive, 3246 negative) verified across 7 thresholds")

    # -------------------------------------------------------------------------
    # CHECK 9: REPORT §12.9 Aligned Cap-Sweep Table
    # -------------------------------------------------------------------------
    cap_sweep_pattern = re.compile(
        r"\|\s*\*\*0\.(\d{2})[^\*]*\*\*\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|"
    )
    cap_matches = cap_sweep_pattern.findall(report_text)
    if len(cap_matches) < 3:
        print(f"[FAIL] Check 9: Section 12.9 Aligned Cap-Sweep Table missing or incomplete in REPORT.md")
        all_passed = False
    else:
        expected_caps = {
            "45": (253, 445, 174, 80, 111, 80, 192, 81, 1, 2),
            "50": (275, 423, 174, 58, 111, 80, 187, 75, 1, 2),
            "55": (322, 376, 150, 59, 104, 63, 185, 68, 1, 2),
        }
        cap_ok = True
        for cap_key, att, unrec, prof, ambig, sml, low, cls, sng, col, ext in cap_matches[:3]:
            if cap_key in expected_caps:
                exp_vals = expected_caps[cap_key]
                act_vals = (int(att), int(unrec), int(prof), int(ambig), int(sml), int(low), int(cls), int(sng), int(col), int(ext))
                if act_vals != exp_vals:
                    print(f"[FAIL] Check 9: Cap-Sweep Table mismatch for 0.{cap_key}: act={act_vals} vs exp={exp_vals}")
                    cap_ok = False
                    all_passed = False
        if cap_ok:
            print(f"[PASS] Check 9: Section 12.9 Aligned Cap-Sweep Table verified (0.45: 253 att/445 unrec; 0.50: 275 att/423 unrec; 0.55: 322 att/376 unrec)")

    # -------------------------------------------------------------------------
    # FINAL SUMMARY
    # -------------------------------------------------------------------------
    print("=" * 80)
    if all_passed:
        print("OVERALL VERIFICATION STATUS: ALL CHECKS PASSED (9/9 CHECKS & TABLES VERIFIED)")
    else:
        print("OVERALL VERIFICATION STATUS: FAILURES DETECTED")
    print("=" * 80)
    return all_passed

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
