"""Verification script comparing live organizer export state against pinned baseline.

Reports differences (people count, number of edits, merged anchors) without failing.
"""

from __future__ import annotations
import sys
import json
import argparse
from pathlib import Path


def report_live_vs_baseline(
    live_export_dir: str | Path = "export",
    live_work_dir: str | Path = "export.work",
    baseline_dir: str | Path = "eval/baseline",
) -> None:
    live_exp = Path(live_export_dir)
    live_wrk = Path(live_work_dir)
    base = Path(baseline_dir)

    print("=" * 80)
    print("PHOTOSORTER LIVE STATE VS BASELINE REPORT (eval/verify_live.py)")
    print("=" * 80)

    # 1. Load baseline people.json
    base_people_file = base / "people.json"
    if not base_people_file.exists():
        print(f"[WARN] Baseline people file not found: {base_people_file}")
        return

    with open(base_people_file, "r", encoding="utf-8") as f:
        base_people_data = json.load(f)

    # 2. Load live people.json
    live_people_file = live_exp / "people.json"
    if not live_people_file.exists():
        print(f"[WARN] Live export people file not found: {live_people_file}")
        return

    with open(live_people_file, "r", encoding="utf-8") as f:
        live_people_data = json.load(f)

    # 3. Load live edits.json
    live_edits_file = live_wrk / "edits.json"
    live_edits_data = {"version": 1, "edits": []}
    if live_edits_file.exists():
        with open(live_edits_file, "r", encoding="utf-8") as f:
            live_edits_data = json.load(f)

    base_people = base_people_data.get("people", [])
    live_people = live_people_data.get("people", [])
    live_edits = live_edits_data.get("edits", [])

    base_people_count = len(base_people)
    live_people_count = len(live_people)
    people_diff = live_people_count - base_people_count

    print(f"People Count Comparison:")
    print(f"  - Baseline people count: {base_people_count}")
    print(f"  - Live export people count: {live_people_count}")
    print(f"  - Difference: {people_diff:+d} people")

    print(f"\nLive Organizer Edits:")
    print(f"  - Number of live edits: {len(live_edits)}")

    merged_anchors = []
    for idx, edit in enumerate(live_edits, 1):
        op = edit.get("op", edit.get("type", "unknown"))
        anchors = edit.get("anchors", [])
        print(f"  - Edit #{idx} [{op}]:")
        if isinstance(anchors, list):
            for g_idx, group in enumerate(anchors, 1):
                if isinstance(group, list):
                    primary_anchor = group[0] if group else "empty"
                    other_count = len(group) - 1
                    print(f"      Group {g_idx}: primary anchor={primary_anchor} ({other_count} additional anchor faces)")
                else:
                    print(f"      Group {g_idx}: anchor={group}")
            merged_anchors.append(anchors)

    base_unrec_faces = len(base_people_data.get("unrecognized", {}).get("faces", []))
    live_unrec_faces = len(live_people_data.get("unrecognized", {}).get("faces", []))
    print(f"\nUnrecognized Faces:")
    print(f"  - Baseline unrecognized faces: {base_unrec_faces}")
    print(f"  - Live unrecognized faces: {live_unrec_faces}")
    print(f"  - Difference: {live_unrec_faces - base_unrec_faces:+d} faces")

    base_photos = len(base_people_data.get("photos", {}))
    live_photos = len(live_people_data.get("photos", {}))
    print(f"\nPhotos:")
    print(f"  - Baseline photo count: {base_photos}")
    print(f"  - Live photo count: {live_photos}")

    print("=" * 80)
    print("STATUS: Informational comparison complete (exit code 0, no failure asserted)")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Report live organizer export delta against pinned baseline")
    parser.add_argument("--live-export", default="export", help="Path to live export directory")
    parser.add_argument("--live-work", default="export.work", help="Path to live work directory")
    parser.add_argument("--baseline", default="eval/baseline", help="Path to pinned baseline directory")
    args = parser.parse_args()

    report_live_vs_baseline(
        live_export_dir=args.live_export,
        live_work_dir=args.live_work,
        baseline_dir=args.baseline,
    )
    sys.exit(0)
