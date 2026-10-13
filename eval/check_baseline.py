#!/usr/bin/env python3
"""Validation script for the pinned baseline fixture in eval/baseline/

Asserts that the pinned baseline exactly reproduces the canonical report metrics:
- 192 people clusters
- 1,256 clustered faces
- 445 unrecognized faces
- 1,701 total detected faces
- 168 unrecognized photos
- 4 photos with zero detected faces
- 81 single-photo people
- 1 collage collision cluster (4a9b927f5789cd69)
- 242 pre-merge clusters mapped to 192 final in id_map.json
- 28 connected maybe groups in suggestions.json
- 0 edits in edits.json
"""

from __future__ import annotations
import json
import sys
from pathlib import Path


def check_baseline(baseline_dir: Path | str = "eval/baseline") -> bool:
    bdir = Path(baseline_dir)
    print("=" * 80)
    print(f"VERIFYING PINNED BASELINE FIXTURE ({bdir})")
    print("=" * 80)

    people_path = bdir / "people.json"
    config_path = bdir / "config.json"
    id_map_path = bdir / "id_map.json"
    sug_path = bdir / "suggestions.json"
    edits_path = bdir / "edits.json"

    required_files = [people_path, config_path, id_map_path, sug_path, edits_path]
    for rf in required_files:
        if not rf.exists():
            print(f"[FAIL] Missing baseline file: {rf}")
            return False

    with open(people_path, "r", encoding="utf-8") as f:
        pdata = json.load(f)
    with open(config_path, "r", encoding="utf-8") as f:
        cdata = json.load(f)
    with open(id_map_path, "r", encoding="utf-8") as f:
        id_map = json.load(f)
    with open(sug_path, "r", encoding="utf-8") as f:
        sug = json.load(f)
    with open(edits_path, "r", encoding="utf-8") as f:
        edits = json.load(f)

    failures = []

    # 1. People count
    people = pdata.get("people", [])
    if len(people) != 192:
        failures.append(f"People count: {len(people)} (expected 192)")
    else:
        print(f"[PASS] People clusters: {len(people)} == 192")

    # 2. Face accounting
    clustered_faces = sum(len(p.get("faces", [])) for p in people)
    unrec_faces = len(pdata.get("unrecognized", {}).get("faces", []))
    total_faces = clustered_faces + unrec_faces
    if clustered_faces != 1256:
        failures.append(f"Clustered faces: {clustered_faces} (expected 1256)")
    else:
        print(f"[PASS] Clustered faces: {clustered_faces} == 1256")

    if unrec_faces != 445:
        failures.append(f"Unrecognized faces: {unrec_faces} (expected 445)")
    else:
        print(f"[PASS] Unrecognized faces: {unrec_faces} == 445")

    if total_faces != 1701:
        failures.append(f"Total faces: {total_faces} (expected 1701)")
    else:
        print(f"[PASS] Total detected faces: {total_faces} == 1701")

    # 3. Unrecognized photos
    unrec_photos = set(pdata.get("unrecognized", {}).get("photo_ids", []))
    if len(unrec_photos) != 168:
        failures.append(f"Unrecognized photos: {len(unrec_photos)} (expected 168)")
    else:
        print(f"[PASS] Unrecognized photos: {len(unrec_photos)} == 168")

    # 4. Photos coverage and zero-face photos
    all_photos = pdata.get("photos", {})
    if len(all_photos) != 259:
        failures.append(f"Total photo records: {len(all_photos)} (expected 259)")
    else:
        print(f"[PASS] Total unique photos: {len(all_photos)} == 259")

    # Zero-face photos: photos that have no face in any person cluster and no face in unrecognized
    photos_with_faces = set()
    for p in people:
        for f in p.get("faces", []):
            photos_with_faces.add(f.get("photo_id"))
    for f in pdata.get("unrecognized", {}).get("faces", []):
        photos_with_faces.add(f.get("photo_id"))

    no_face_photos = set(all_photos.keys()) - photos_with_faces
    expected_no_face = {"3a6ecb102a1bcf95", "ac41dd5a9fde7b36", "cbc787ccd8664c53", "fd6bc6fe47a406ab"}
    if no_face_photos != expected_no_face:
        failures.append(f"No-face photos: {sorted(list(no_face_photos))} (expected {sorted(list(expected_no_face))})")
    else:
        print(f"[PASS] No-face photos: {len(no_face_photos)} == 4 ({sorted(list(no_face_photos))})")

    # 5. Singletons count
    singletons = sum(1 for p in people if len(p.get("photos", p.get("photo_ids", []))) == 1)
    if singletons != 81:
        failures.append(f"Singletons: {singletons} (expected 81)")
    else:
        print(f"[PASS] Singletons: {singletons} == 81")

    # 6. Same-photo collision cluster
    collision_clusters = []
    for p in people:
        p_ids = [f.get("photo_id") for f in p.get("faces", [])]
        if len(p_ids) != len(set(p_ids)):
            collision_clusters.append(p)
    if len(collision_clusters) != 1:
        failures.append(f"Collision clusters count: {len(collision_clusters)} (expected 1)")
    else:
        coll_photo = "4a9b927f5789cd69"
        coll_faces = collision_clusters[0].get("faces", [])
        coll_pids = [f.get("photo_id") for f in coll_faces]
        if coll_pids.count(coll_photo) != 3:
            failures.append(f"Collage collision photo faces: {coll_pids.count(coll_photo)} (expected 3)")
        else:
            print(f"[PASS] Collision clusters: exactly 1 collage cluster verified ({coll_photo})")

    # 7. id_map.json pre-merge to final
    mapping_items = {k: v for k, v in id_map.items() if not k.startswith("_")}
    pre_merge_count = len(mapping_items)
    unique_final = len(set(mapping_items.values()))
    if pre_merge_count != 242:
        failures.append(f"Pre-merge count in id_map: {pre_merge_count} (expected 242)")
    else:
        print(f"[PASS] Pre-merge cluster count: {pre_merge_count} == 242")
    if unique_final != 192:
        failures.append(f"Unique final clusters in id_map: {unique_final} (expected 192)")
    else:
        print(f"[PASS] Final clusters mapped in id_map: {unique_final} == 192")

    # 8. suggestions.json maybe groups
    maybe_groups = sug.get("maybe_groups", [])
    if len(maybe_groups) != 28:
        failures.append(f"Maybe groups count: {len(maybe_groups)} (expected 28)")
    else:
        print(f"[PASS] Connected maybe groups: {len(maybe_groups)} == 28")

    # 9. Empty edits.json
    edits_list = edits.get("edits", [])
    if len(edits_list) != 0:
        failures.append(f"Edits count in baseline edits.json: {len(edits_list)} (expected 0)")
    else:
        print(f"[PASS] Baseline edits.json is empty: {len(edits_list)} == 0")

    print("=" * 80)
    if failures:
        print(f"BASELINE DRIFT DETECTED ({len(failures)} failures):")
        for f in failures:
            print(f"  - {f}")
        return False
    else:
        print("ALL CANONICAL BASELINE METRICS VERIFIED (100% OK)")
        return True


if __name__ == "__main__":
    baseline_path = sys.argv[1] if len(sys.argv) > 1 else "eval/baseline"
    ok = check_baseline(baseline_path)
    sys.exit(0 if ok else 1)
