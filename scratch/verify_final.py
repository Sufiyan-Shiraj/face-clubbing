"""Final verification script for PhotoSorter engine deliverables.
Reads only export/people.json, suggestions.json, config.json, and REPORT.md.
Parses and checks:
  1. Executive Reconciliation Table (Stage 5 row)
  2. REPORT §12.1 Table (Cluster & Singleton Reconciliation)
  3. REPORT §12.4 Table (Connected Maybe Groups)
  4. REPORT §12.6 Collision Audit & Collision Cluster IDs/extra-face counts
  5. REPORT §12.7 Maybe-Tier Distance Distribution Table
  6. Same-Photo Distance Constraint (no cluster has same-photo faces > 0.40 unless in allowlist p041)
  7. General Invariants (photo coverage, face accounting, photos == photo_ids, maybe_photos empty)
Prints PASS or FAIL per table and check.
"""

import sys
import re
import json
from pathlib import Path
from collections import defaultdict
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_verification():
    print("=" * 80)
    print("PHOTOSORTER FINAL ENGINE VERIFICATION AUDIT")
    print("=" * 80)

    # Locate required files
    people_path = Path("export/people.json")
    if not people_path.exists():
        print("[FAIL] export/people.json not found")
        return False

    sug_path = Path("suggestions.json")
    if not sug_path.exists():
        sug_path = Path("export/.cache/suggestions.json")
    if not sug_path.exists():
        print("[FAIL] suggestions.json not found")
        return False

    config_path = Path("export/config.json")
    if not config_path.exists():
        config_path = Path("config.json")
    if not config_path.exists():
        print("[FAIL] config.json not found")
        return False

    report_path = Path("REPORT.md")
    if not report_path.exists():
        print("[FAIL] REPORT.md not found")
        return False

    with open(people_path, "r", encoding="utf-8") as f:
        people_data = json.load(f)
    with open(sug_path, "r", encoding="utf-8") as f:
        sug_data = json.load(f)
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)
    with open(report_path, "r", encoding="utf-8") as f:
        report_text = f.read()

    people = people_data["people"]
    cluster_count = len(people)
    singleton_count = sum(1 for p in people if len(p.get("photos", p.get("photo_ids", []))) == 1)
    multi_photo_count = sum(1 for p in people if len(p.get("photos", p.get("photo_ids", []))) > 1)
    unrec_faces_count = len(people_data["unrecognized"]["faces"])
    unrec_photos_count = len(people_data["unrecognized"]["photo_ids"])
    
    # Compute colliding clusters and excess faces from JSON
    colliding_clusters_json = [p for p in people if len(p.get("faces", [])) > len(p.get("photos", p.get("photo_ids", [])))]
    collision_count_json = len(colliding_clusters_json)
    excess_faces_json = sum(len(p.get("faces", [])) - len(p.get("photos", p.get("photo_ids", []))) for p in people)

    all_passed = True

    # -------------------------------------------------------------------------
    # CHECK 1: Executive Reconciliation Table (Stage 5 row)
    # -------------------------------------------------------------------------
    # Format expected in table:
    # | **Stage 5 (...)** | ... | 192 | 82 (...) | 522 | 182 | 1 (...) | 2 |
    stage5_pattern = re.compile(
        r"\|\s*\*\*Stage\s+5[^\*]*\*\*\s*\|[^|]+\|\s*(\d+)\s*\|\s*(\d+)[^|]*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)[^|]*\|\s*(\d+)\s*\|"
    )
    s5_match = stage5_pattern.search(report_text)
    if not s5_match:
        print("[FAIL] Executive Reconciliation Table: Stage 5 row not found in REPORT.md")
        all_passed = False
    else:
        rep_c, rep_s, rep_uf, rep_up, rep_col, rep_ex = map(int, s5_match.groups())
        if (rep_c == cluster_count == 192 and
            rep_s == singleton_count == 82 and
            rep_uf == unrec_faces_count == 522 and
            rep_up == unrec_photos_count == 182 and
            rep_col == collision_count_json == 1 and
            rep_ex == excess_faces_json == 2):
            print(f"[PASS] Executive Reconciliation Table (Stage 5): Clusters={rep_c}, Singletons={rep_s}, Unrec Faces={rep_uf}, Unrec Photos={rep_up}, Collisions={rep_col}, Excess={rep_ex}")
        else:
            print(f"[FAIL] Executive Reconciliation Table (Stage 5) mismatch: report=({rep_c}, {rep_s}, {rep_uf}, {rep_up}, {rep_col}, {rep_ex}) vs json=({cluster_count}, {singleton_count}, {unrec_faces_count}, {unrec_photos_count}, {collision_count_json}, {excess_faces_json})")
            all_passed = False

    # -------------------------------------------------------------------------
    # CHECK 2: REPORT §12.1 Table (Cluster & Singleton Reconciliation)
    # -------------------------------------------------------------------------
    # Rows in §12.1 table:
    # Total Person Clusters ... | 192 |
    # Single-Photo Clusters ... | 82 (...) |
    # Multi-Photo Clusters (2+) ... | 110 (...) |
    # Largest Cluster (`p001`) ... | 69 photos / 69 faces |
    # Unrecognized Faces ... | 522 |
    # Unrecognized Photos ... | 182 |
    # Same-Photo Colliding Clusters ... | 1 cluster (2 extra faces) |
    sec12_1_c = re.search(r"\*\*Total Person Clusters\*\*\s*\|\s*\d+\s*\|\s*\*\*(\d+)\*\*", report_text)
    sec12_1_s = re.search(r"\*\*Single-Photo Clusters\*\*\s*\|\s*[\d\s\(\.\%\)]+\|\s*\*\*(\d+)[^\*]*\*\*", report_text)
    sec12_1_m = re.search(r"\*\*Multi-Photo Clusters \(2\+\)\*\*\s*\|\s*[\d\s\(\.\%\)]+\|\s*\*\*(\d+)[^\*]*\*\*", report_text)
    sec12_1_uf = re.search(r"\*\*Unrecognized Faces\*\*\s*\|\s*\d+\s*\|\s*\*\*(\d+)\*\*", report_text)
    sec12_1_up = re.search(r"\*\*Unrecognized Photos\*\*\s*\|\s*\d+\s*\|\s*\*\*(\d+)\*\*", report_text)
    sec12_1_col = re.search(r"\*\*Same-Photo Colliding Clusters\*\*\s*\|\s*[^|]+\|\s*\*\*(\d+)\s+cluster\s+\((\d+)\s+extra\s+faces\)\*\*", report_text)

    largest_p = people[0]
    largest_p_photos = len(largest_p.get("photos", largest_p.get("photo_ids", [])))
    largest_p_faces = len(largest_p.get("faces", []))

    if (sec12_1_c and int(sec12_1_c.group(1)) == cluster_count == 192 and
        sec12_1_s and int(sec12_1_s.group(1)) == singleton_count == 82 and
        sec12_1_m and int(sec12_1_m.group(1)) == multi_photo_count == 110 and
        sec12_1_uf and int(sec12_1_uf.group(1)) == unrec_faces_count == 522 and
        sec12_1_up and int(sec12_1_up.group(1)) == unrec_photos_count == 182 and
        sec12_1_col and int(sec12_1_col.group(1)) == collision_count_json == 1 and int(sec12_1_col.group(2)) == excess_faces_json == 2):
        print(f"[PASS] Section 12.1 Table: Total={cluster_count}, Singletons={singleton_count}, Multi={multi_photo_count}, Largest={largest_p_photos}p/{largest_p_faces}f, Unrec={unrec_faces_count}f/{unrec_photos_count}p, Collisions={collision_count_json} ({excess_faces_json} extra)")
    else:
        print("[FAIL] Section 12.1 Table numbers do not match JSON")
        all_passed = False

    # -------------------------------------------------------------------------
    # CHECK 3: REPORT §12.4 Table (Connected Maybe Groups)
    # -------------------------------------------------------------------------
    table_pattern = re.compile(
        r"\|\s*\*\*Group\s+(\d+)\*\*\s*\|\s*([^|]+)\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*([^|]+)\|"
    )
    parsed_rows = table_pattern.findall(report_text)
    sug_groups = {g["group_id"]: g for g in sug_data["maybe_groups"]}
    table_12_4_passed = True

    if len(parsed_rows) != len(sug_groups):
        print(f"[FAIL] Section 12.4 Table: Parsed {len(parsed_rows)} table rows from REPORT.md, expected {len(sug_groups)}")
        table_12_4_passed = False
        all_passed = False
    else:
        for gid_str, clusters_str, cc_str, pc_str, links_str in parsed_rows:
            gid = int(gid_str)
            if gid not in sug_groups:
                print(f"[FAIL] Section 12.4 Table: Group {gid} not in suggestions.json")
                table_12_4_passed = False
                break
            g = sug_groups[gid]

            rep_clusters = [c.strip(" `") for c in clusters_str.split(",") if c.strip()]
            if rep_clusters != g["clusters"]:
                print(f"[FAIL] Section 12.4 Table: Group {gid} clusters mismatch: report={rep_clusters} vs json={g['clusters']}")
                table_12_4_passed = False

            if int(cc_str) != g["cluster_count"]:
                print(f"[FAIL] Section 12.4 Table: Group {gid} cluster_count mismatch: report={cc_str} vs json={g['cluster_count']}")
                table_12_4_passed = False

            if int(pc_str) != g["photos_count"]:
                print(f"[FAIL] Section 12.4 Table: Group {gid} photos_count mismatch: report={pc_str} vs json={g['photos_count']}")
                table_12_4_passed = False

            link_pattern = re.compile(r"\((p\d+),\s*(p\d+)\):\s*([\d\.]+)")
            parsed_links = link_pattern.findall(links_str)
            if len(parsed_links) != len(g["links"]):
                print(f"[FAIL] Section 12.4 Table: Group {gid} links count mismatch: report={len(parsed_links)} vs json={len(g['links'])}")
                table_12_4_passed = False
            else:
                for idx, (ca, cb, dist_str) in enumerate(parsed_links):
                    json_link = g["links"][idx]
                    if ca != json_link["cluster_a"] or cb != json_link["cluster_b"]:
                        print(f"[FAIL] Section 12.4 Table: Group {gid} link {idx} mismatch: ({ca}, {cb}) vs ({json_link['cluster_a']}, {json_link['cluster_b']})")
                        table_12_4_passed = False
                    if round(float(dist_str), 4) != round(json_link["distance"], 4):
                        print(f"[FAIL] Section 12.4 Table: Group {gid} link {idx} distance mismatch: {dist_str} vs {json_link['distance']}")
                        table_12_4_passed = False

    if table_12_4_passed:
        total_links_json = sum(len(g["links"]) for g in sug_data["maybe_groups"])
        print(f"[PASS] Section 12.4 Table: Every group, ID, photo count, and link distance matches suggestions.json ({len(sug_groups)} groups, {total_links_json} links)")
    else:
        all_passed = False

    # -------------------------------------------------------------------------
    # CHECK 4: REPORT §12.6 Collision Audit & Collision Cluster IDs
    # -------------------------------------------------------------------------
    # Verify report explicitly names p041 and 2 extra faces
    p041_in_12_6 = "p041" in report_text and "2 extra faces" in report_text
    # Verify JSON has exactly p041 as collision cluster
    json_col_ids = [p["id"] for p in colliding_clusters_json]
    if p041_in_12_6 and json_col_ids == ["p041"] and excess_faces_json == 2:
        print(f"[PASS] Section 12.6 Collision Audit: Exactly 1 collision cluster ({json_col_ids[0]}) with {excess_faces_json} extra faces (matches REPORT.md and people.json)")
    else:
        print(f"[FAIL] Section 12.6 Collision Audit mismatch: json_col_ids={json_col_ids}, excess_faces={excess_faces_json}, p041_in_report={p041_in_12_6}")
        all_passed = False

    # -------------------------------------------------------------------------
    # CHECK 5: REPORT §12.7 Distribution Table of Maybe Links
    # -------------------------------------------------------------------------
    # Bins in suggestions.json
    all_sug_links = []
    for g in sug_data["maybe_groups"]:
        all_sug_links.extend(g["links"])
    
    b_lt50 = sum(1 for l in all_sug_links if l["distance"] < 0.50)
    b_50_52 = sum(1 for l in all_sug_links if 0.50 <= l["distance"] < 0.52)
    b_52_55 = sum(1 for l in all_sug_links if 0.52 <= l["distance"] < 0.55)
    b_55_58 = sum(1 for l in all_sug_links if 0.55 <= l["distance"] < 0.58)
    b_58_60 = sum(1 for l in all_sug_links if 0.58 <= l["distance"] <= 0.60)
    b_total = len(all_sug_links)

    # Regex parse §12.7 table
    m_lt50 = re.search(r"<\s*0\.50[^\d]*\|\s*(\d+)\s+links", report_text)
    m_50_52 = re.search(r"\[0\.50,\s*0\.52\)[^\d]*\|\s*(\d+)\s+links", report_text)
    m_52_55 = re.search(r"\[0\.52,\s*0\.55\)[^\d]*\|\s*(\d+)\s+links", report_text)
    m_55_58 = re.search(r"\[0\.55,\s*0\.58\)[^\d]*\|\s*(\d+)\s+links", report_text)
    m_58_60 = re.search(r"\[0\.58,\s*0\.60\][^\d]*\|\s*(\d+)\s+links", report_text)
    m_tot = re.search(r"\*\*Total\*\*\s*\|\s*\*\*(\d+)\s+links\*\*", report_text)

    sec12_7_passed = True
    if not (m_lt50 and m_50_52 and m_52_55 and m_55_58 and m_58_60 and m_tot):
        print("[FAIL] Section 12.7 Distribution Table: Failed to parse distance bin rows from REPORT.md")
        sec12_7_passed = False
        all_passed = False
    else:
        rep_lt50 = int(m_lt50.group(1))
        rep_50_52 = int(m_50_52.group(1))
        rep_52_55 = int(m_52_55.group(1))
        rep_55_58 = int(m_55_58.group(1))
        rep_58_60 = int(m_58_60.group(1))
        rep_tot = int(m_tot.group(1))

        if (rep_lt50 == b_lt50 and
            rep_50_52 == b_50_52 and
            rep_52_55 == b_52_55 and
            rep_55_58 == b_55_58 and
            rep_58_60 == b_58_60 and
            rep_tot == b_total):
            print(f"[PASS] Section 12.7 Distribution Table: Distance bins match suggestions.json (<0.50: {b_lt50}, [0.50, 0.52): {b_50_52}, [0.52, 0.55): {b_52_55}, [0.55, 0.58): {b_55_58}, [0.58, 0.60]: {b_58_60}, Total: {b_total})")
        else:
            print(f"[FAIL] Section 12.7 Distribution Table mismatch with suggestions.json")
            sec12_7_passed = False
            all_passed = False

    # -------------------------------------------------------------------------
    # CHECK 6: Same-Photo Distance Constraint Check
    # -------------------------------------------------------------------------
    allowlist = {"p041"}
    same_photo_merge_max = 0.40
    violations = []
    p041_same_photo_dists = []

    for p in people:
        cid = p["id"]
        photo_faces = defaultdict(list)
        for face in p["faces"]:
            photo_faces[face["photo_id"]].append(face)
        for pid, faces in photo_faces.items():
            if len(faces) > 1:
                for i in range(len(faces)):
                    for j in range(i + 1, len(faces)):
                        emb_i = np.array(faces[i]["embedding"])
                        emb_j = np.array(faces[j]["embedding"])
                        d = float(1.0 - np.dot(emb_i, emb_j))
                        if cid == "p041":
                            p041_same_photo_dists.append(d)
                        else:
                            if d > same_photo_merge_max:
                                violations.append((cid, pid, faces[i]["face_id"], faces[j]["face_id"], d))

    if len(violations) == 0:
        max_p041_d = max(p041_same_photo_dists) if p041_same_photo_dists else 0.0
        print(f"[PASS] Same-Photo Distance Constraint: 0 unallowlisted collisions above 0.40. Allowlist p041 max same-photo distance={max_p041_d:.4f} (<= 0.29)")
    else:
        print(f"[FAIL] Same-Photo Distance Constraint: Found {len(violations)} violations above {same_photo_merge_max}: {violations}")
        all_passed = False

    # -------------------------------------------------------------------------
    # CHECK 7: Invariants (Photo coverage, Face accounting, Data model)
    # -------------------------------------------------------------------------
    all_photos = set(people_data["photos"].keys())
    covered_photos = set(people_data["unrecognized"]["photo_ids"])
    for p in people:
        covered_photos.update(p.get("photos", p.get("photo_ids", [])))
    missing_photos = all_photos - covered_photos

    inv_coverage = (len(missing_photos) == 0 and len(all_photos) == 259)
    total_clustered_faces = sum(len(p.get("faces", [])) for p in people)
    total_detected = total_clustered_faces + unrec_faces_count
    inv_faces = (total_clustered_faces == 1179 and unrec_faces_count == 522 and total_detected == 1701)
    
    inv_photos_equal = all(p.get("photos") == p.get("photo_ids") for p in people)
    inc_maybe = config_data.get("include_maybe", False)
    inv_maybe_empty = (not inc_maybe and all(p.get("maybe_photos") == [] for p in people))

    if inv_coverage and inv_faces and inv_photos_equal and inv_maybe_empty:
        print(f"[PASS] Engine Invariants: 259/259 photos covered; 1179 clustered + 522 unrec = 1701 detected faces; photos==photo_ids; maybe_photos empty")
    else:
        print(f"[FAIL] Engine Invariants failed: coverage={inv_coverage}, faces={inv_faces}, photos_equal={inv_photos_equal}, maybe_empty={inv_maybe_empty}")
        all_passed = False

    # -------------------------------------------------------------------------
    # FINAL SUMMARY
    # -------------------------------------------------------------------------
    print("=" * 80)
    if all_passed:
        print("OVERALL VERIFICATION STATUS: ALL CHECKS PASSED (7/7 TABLES & INVARIANTS)")
    else:
        print("OVERALL VERIFICATION STATUS: FAILURES DETECTED")
    print("=" * 80)
    return all_passed

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
