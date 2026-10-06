"""Reachability verification script for PhotoSorter viewer (Requirement 11).

Loads people.json and computes photo reachability using the exact data paths
navigated by the viewer components:
- Person gallery: person.photos || person.photo_ids
- Unrecognized gallery: unrecognized.photo_ids and unrecognized.faces[].photo_id

Asserts that every photo in data["photos"] is reachable from at least one screen.
"""

from pathlib import Path
import json
import sys


def verify_reachability(people_json_path: Path) -> dict:
    if not people_json_path.exists():
        raise FileNotFoundError(f"File not found: {people_json_path}")

    with open(people_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    declared_photos = set(data.get("photos", {}).keys())
    total_declared = len(declared_photos)

    # 1. Photos reachable through People galleries (PhotoGallery.tsx)
    reachable_via_people = set()
    for person in data.get("people", []):
        p_photos = person.get("photos") or person.get("photo_ids", [])
        reachable_via_people.update(p_photos)

    # 2. Photos reachable through Unrecognized gallery (UnrecognizedGallery.tsx)
    unrec = data.get("unrecognized", {})
    unrec_photo_ids = set(unrec.get("photo_ids", []))
    unrec_face_photo_ids = {f["photo_id"] for f in unrec.get("faces", []) if "photo_id" in f}
    reachable_via_unrecognized = unrec_photo_ids | unrec_face_photo_ids

    # Combined reachable photos across all screens
    all_reachable = reachable_via_people | reachable_via_unrecognized

    unreachable = declared_photos - all_reachable
    orphan_reachable = all_reachable - declared_photos

    results = {
        "file": str(people_json_path),
        "total_declared": total_declared,
        "reachable_via_people": len(reachable_via_people),
        "reachable_via_unrecognized": len(reachable_via_unrecognized),
        "total_reachable": len(all_reachable),
        "unreachable_count": len(unreachable),
        "unreachable_ids": sorted(list(unreachable)),
        "orphan_reachable_count": len(orphan_reachable),
        "is_complete": len(unreachable) == 0 and len(all_reachable) == total_declared,
    }
    return results


def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    default_path = repo_root / "export" / "people.json"

    target_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_path

    print(f"=== PhotoSorter Viewer Reachability Verification ===")
    print(f"Target: {target_path}")

    res = verify_reachability(target_path)

    print(f"Total photos declared in photos dict: {res['total_declared']}")
    print(f"Reachable via confirmed person galleries: {res['reachable_via_people']}")
    print(f"Reachable via unrecognized screen:       {res['reachable_via_unrecognized']}")
    print(f"Total unique reachable photos:           {res['total_reachable']}")
    print(f"Unreachable photos:                     {res['unreachable_count']}")

    if res["is_complete"]:
        print(f"RESULT: PASS ({res['total_reachable']}/{res['total_declared']} photos reachable)")
        sys.exit(0)
    else:
        print(f"RESULT: FAIL ({res['unreachable_count']} unreachable photos)")
        if res["unreachable_ids"]:
            print(f"Sample unreachable: {res['unreachable_ids'][:5]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
