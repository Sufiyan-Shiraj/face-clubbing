"""Comprehensive integrity check for the 271-photo export bundle and viewer assets."""

import sys
import json
from pathlib import Path

def main():
    export_dir = Path("export").resolve()
    people_path = export_dir / "people.json"
    config_path = export_dir / "config.json"
    thumbs_dir = export_dir / "thumbs"
    faces_dir = export_dir / "faces"
    cache_dir = export_dir / ".cache"
    viewer_public = Path("viewer/public").resolve()

    print("--- Integrity Verification on 271 Photos ---")

    # 1. people.json validity
    assert people_path.exists(), "people.json missing from export/"
    with open(people_path, "r", encoding="utf-8") as f:
        people_data = json.load(f)
    print("[PASS] people.json exists and parses as valid JSON.")

    # 2. Photos coverage check
    all_photos = set(people_data["photos"].keys())
    print(f"Total unique photo records in export: {len(all_photos)}")

    clustered_photos = set()
    for p in people_data["people"]:
        clustered_photos.update(p["photo_ids"])

    unrec_photos = set(people_data["unrecognized"]["photo_ids"])
    covered_photos = clustered_photos.union(unrec_photos)

    unaccounted = all_photos - covered_photos
    assert len(unaccounted) == 0, f"Integrity Failure: {len(unaccounted)} photos unaccounted for: {unaccounted}"
    print(f"[PASS] All {len(all_photos)} photos are covered! (0 photos dropped).")

    # 3. Both person cluster and unrecognized coverage
    overlap = clustered_photos.intersection(unrec_photos)
    print(f"  - Photos in person clusters: {len(clustered_photos)}")
    print(f"  - Photos in Unrecognized:    {len(unrec_photos)}")
    print(f"  - Photos in both:            {len(overlap)} (photos with known faces + unrec/blurry faces)")

    # 4. Check asset existence on disk
    missing_thumbs = []
    for pid, pinfo in people_data["photos"].items():
        tpath = export_dir / pinfo["thumb"]
        if not tpath.exists():
            missing_thumbs.append(pinfo["thumb"])
    assert len(missing_thumbs) == 0, f"Missing thumbnails: {len(missing_thumbs)}"
    print(f"[PASS] All {len(people_data['photos'])} photo thumbnails exist on disk in export/thumbs/.")

    missing_faces = []
    for p in people_data["people"]:
        fpath = export_dir / p["face"]
        if not fpath.exists():
            missing_faces.append(p["face"])
    assert len(missing_faces) == 0, f"Missing person face crops: {len(missing_faces)}"
    print(f"[PASS] All {len(people_data['people'])} representative face crops exist on disk in export/faces/.")

    # 5. Security & Isolation Check: suggestions.json must NEVER be in public export bundle
    assert not (export_dir / "suggestions.json").exists(), "CRITICAL: suggestions.json leaked into export/ root!"
    assert not (viewer_public / "suggestions.json").exists(), "CRITICAL: suggestions.json leaked into viewer/public/!"
    assert (cache_dir / "suggestions.json").exists(), "suggestions.json missing from organizer cache!"
    print("[PASS] suggestions.json is strictly organizer-only (.cache/suggestions.json) and NOT inside public export/ or viewer/public/.")

    # 6. config.json validity
    assert config_path.exists(), "config.json missing from export/"
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)
    print(f"[PASS] config.json is valid (title: '{config_data.get('title')}', accent: '{config_data.get('accent')}').")

    print("\nALL INTEGRITY CHECKS PASSED.")

if __name__ == "__main__":
    main()
