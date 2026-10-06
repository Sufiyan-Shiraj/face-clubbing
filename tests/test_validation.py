"""Validation test for Phase 1 export bundle: schema conformity and coverage invariant."""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def validate_export(export_dir: Path | str = PROJECT_ROOT / "export") -> bool:
    export_p = Path(export_dir).resolve()
    print("=" * 60)
    print(f"VALIDATING EXPORT BUNDLE: {export_p}")
    print("=" * 60)

    people_json_p = export_p / "people.json"
    config_json_p = export_p / "config.json"

    if not people_json_p.exists():
        print(f"FAIL: people.json not found at {people_json_p}")
        return False
    if not config_json_p.exists():
        print(f"FAIL: config.json not found at {config_json_p}")
        return False

    with open(people_json_p, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Schema check
    assert data.get("version") == 1, "people.json version must be 1"
    assert "photos" in data, "people.json must contain 'photos'"
    assert "people" in data, "people.json must contain 'people'"
    assert "unrecognized" in data, "people.json must contain 'unrecognized'"

    photos = data["photos"]
    people = data["people"]
    unrecognized = data["unrecognized"]

    print(f"Found {len(photos)} photos recorded in people.json.")
    print(f"Found {len(people)} people clusters.")
    print(f"Found {len(unrecognized.get('photo_ids', []))} photos in Unrecognized.")
    print(f"Found {len(unrecognized.get('faces', []))} unrecognized face crops.")

    # 2. Invariant: Every photo must appear in at least one person or in unrecognized
    all_photo_ids = set(photos.keys())
    covered_photo_ids = set(unrecognized.get("photo_ids", []))
    for p in people:
        covered_photo_ids.update(p.get("photo_ids", []))

    missing = all_photo_ids - covered_photo_ids
    if missing:
        print(f"FAIL: {len(missing)} photos are missing from both people and unrecognized: {missing}")
        return False
    print("PASS: Invariant holds - 100% of photos appear in a person cluster or Unrecognized!")

    # 3. File existence checks
    missing_files = []
    for pid, pdata in photos.items():
        thumb_p = export_p / pdata["thumb"]
        if not thumb_p.exists():
            missing_files.append(f"Missing thumbnail: {thumb_p}")

    for p in people:
        face_p = export_p / p["face"]
        if not face_p.exists():
            missing_files.append(f"Missing face crop: {face_p}")

    for uface in unrecognized.get("faces", []):
        uface_p = export_p / uface["face"]
        if not uface_p.exists():
            missing_files.append(f"Missing unrecognized face crop: {uface_p}")

    if missing_files:
        print(f"FAIL: {len(missing_files)} referenced media files are missing on disk!")
        for mf in missing_files[:5]:
            print(f"  {mf}")
        return False
    print("PASS: All referenced thumbnail and face crop files exist on disk.")

    # 4. Cluster size distribution
    print("\nCluster Distribution Summary:")
    counts = [len(p["photo_ids"]) for p in people]
    single = sum(1 for c in counts if c == 1)
    two_to_five = sum(1 for c in counts if 2 <= c <= 5)
    six_plus = sum(1 for c in counts if c >= 6)
    print(f"  People with 1 photo:       {single}")
    print(f"  People with 2-5 photos:    {two_to_five}")
    print(f"  People with 6+ photos:     {six_plus}")

    print("\n" + "=" * 60)
    print("ALL VALIDATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = validate_export()
    sys.exit(0 if success else 1)
