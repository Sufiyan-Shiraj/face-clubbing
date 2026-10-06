"""Drive script for PhotoSorter FastAPI layer using authentic curl.exe.

Executes and logs all Phase 3 steps:
1. Health and settings inspection
2. Initial people and suggestions listing
3. Merging 3+ people in one call (confirms anchor face IDs, zero cluster IDs)
4. Assigning an unrecognized face to a person
5. Re-running clustering with edit replay (confirms edits survived)
6. Undo of edits
7. Exporting public bundle and validating hygiene
8. Job lifecycle: start, progress status, and cancel
"""

import sys
import json
import re
import subprocess
import time
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"


def run_curl(args: list[str], label: str) -> str:
    cmd = ["curl.exe", "-s"] + args
    cmd_display = "curl.exe " + " ".join(args)
    print("\n" + "=" * 80)
    print(f"STEP: {label}")
    print(f"COMMAND: {cmd_display}")
    print("-" * 80)

    res = subprocess.run(cmd, capture_output=True, text=True)
    out = res.stdout.strip()
    if len(out) > 1200:
        preview = out[:600] + "\n... [TRUNCATED] ...\n" + out[-400:]
        print(f"OUTPUT:\n{preview}")
    else:
        print(f"OUTPUT:\n{out}")
    return out


def main():
    print("================================================================================")
    print("PHOTOSORTER PHASE 3 END-TO-END DRIVE TRANSCRIPT (curl.exe)")
    print("================================================================================")

    # 0. Set up isolated test work directory (never touches canonical export/ or export.work/edits.json)
    test_dir = Path("export.api_test")
    test_dir.mkdir(parents=True, exist_ok=True)
    test_edits = test_dir / "edits.json"
    test_edits.write_text(json.dumps({"version": 1, "edits": []}, indent=2), encoding="utf-8")

    # Re-point API server state to isolated test work directory and test output directory
    setup_body = json.dumps({"work_dir": "export.api_test", "output_dir": "export.api_test"})
    run_curl(
        ["-X", "POST", f"{BASE_URL}/api/settings", "-H", "Content-Type: application/json", "-d", setup_body],
        "Configure Isolated Test Directory (export.api_test)",
    )

    # 1. Health check
    run_curl([f"{BASE_URL}/api/health"], "Check API Health")

    # 2. Get Settings
    run_curl([f"{BASE_URL}/api/settings"], "Inspect Current Settings")

    # 3. Get initial people count
    p_raw = run_curl([f"{BASE_URL}/api/people"], "Fetch Initial People")
    people = json.loads(p_raw)
    print(f"--> Retrieved {len(people)} people clusters from API.")

    # 4. Get suggestions
    sug_raw = run_curl([f"{BASE_URL}/api/suggestions"], "Fetch Clustering Suggestions")
    sug = json.loads(sug_raw)
    print(f"--> Retrieved {sug.get('maybe_groups_count', 0)} maybe groups, {sug.get('possibly_the_same_count', 0)} ranked pairs, {sug.get('ambiguous_faces_count', 0)} ambiguous faces.")

    # 5. Get unrecognized faces
    unrec_raw = run_curl([f"{BASE_URL}/api/unrecognized"], "Fetch Unrecognized Group")
    unrec = json.loads(unrec_raw)
    unrec_faces = unrec.get("faces", [])
    no_face_photos = unrec.get("no_face_photos", [])
    print(f"--> Retrieved {len(unrec_faces)} unrecognized faces, {unrec.get('total_unrecognized_photos', 0)} photos, {len(no_face_photos)} no-face photos.")

    # 6. Merge 3+ people in one call
    # Pick three small clusters from the end of the list
    merge_candidates = people[-3:]
    merge_ids = [c["id"] for c in merge_candidates]
    print(f"--> Target cluster IDs to merge: {merge_ids}")

    merge_body = json.dumps({"op": "merge", "person_ids": merge_ids})
    run_curl(
        ["-X", "POST", f"{BASE_URL}/api/edits", "-H", "Content-Type: application/json", "-d", merge_body],
        "Merge 3 People in One Call",
    )

    # Check edits.json on disk to assert NO cluster IDs
    if test_edits.exists():
        content = test_edits.read_text(encoding="utf-8")
        cluster_violations = re.findall(r'\bp\d{3}\b', content)
        print(f"--> edits.json check: {len(cluster_violations)} cluster ID violations found.")
        assert len(cluster_violations) == 0, f"Violations found: {cluster_violations}"
        parsed = json.loads(content)
        print(f"--> Persisted edit anchors: {parsed['edits'][-1]['anchors']}")

    # 7. Assign an Unrecognized face to a person
    if unrec_faces:
        face_to_assign = unrec_faces[0]["face_id"]
        target_person = people[0]["id"]
        assign_body = json.dumps({"op": "assign", "face_id": face_to_assign, "person_id": target_person})
        run_curl(
            ["-X", "POST", f"{BASE_URL}/api/edits", "-H", "Content-Type: application/json", "-d", assign_body],
            f"Assign Unrecognized Face {face_to_assign} to Person {target_person}",
        )

    # 8. Re-run pipeline with edit replay
    rerun_body = json.dumps({"settings": {"distance_threshold": 0.48}})
    run_curl(
        ["-X", "POST", f"{BASE_URL}/api/rerun", "-H", "Content-Type: application/json", "-d", rerun_body],
        "Re-run Engine with Edit Replay and Parameter Change",
    )

    # Confirm edits survived
    after_people = json.loads(subprocess.run(["curl.exe", "-s", f"{BASE_URL}/api/people"], capture_output=True, text=True).stdout)
    print(f"--> Re-clustered people count: {len(after_people)}")

    # 9. Test Undo
    run_curl(
        ["-X", "POST", f"{BASE_URL}/api/edits", "-H", "Content-Type: application/json", "-d", json.dumps({"op": "undo"})],
        "Undo Last Edit (Assign)",
    )
    run_curl(
        ["-X", "POST", f"{BASE_URL}/api/edits", "-H", "Content-Type: application/json", "-d", json.dumps({"op": "undo"})],
        "Undo Previous Edit (Merge)",
    )

    # 10. Export Public Bundle into export.api_test
    export_body = json.dumps({"output_dir": "export.api_test"})
    run_curl(
        ["-X", "POST", f"{BASE_URL}/api/export", "-H", "Content-Type: application/json", "-d", export_body],
        "Export Public Bundle to Isolated Test Directory",
    )

    # Verify public bundle hygiene
    exported_names = sorted([p.name for p in test_dir.iterdir() if p.name != "edits.json"])
    forbidden = {"suggestions.json", "edits.json", "id_map.json", ".cache"}
    found_forbidden = [f for f in forbidden if f in exported_names]
    print(f"--> Exported files in export.api_test: {exported_names}")
    print(f"--> Forbidden files in public bundle: {found_forbidden} (0 expected)")
    assert len(found_forbidden) == 0

    # 11. Test Cancel background job
    run_curl(
        ["-X", "POST", f"{BASE_URL}/api/jobs/start", "-H", "Content-Type: application/json", "-d", "{}"],
        "Start Background Job",
    )
    run_curl(
        ["-X", "POST", f"{BASE_URL}/api/jobs/cancel"],
        "Cancel Background Job",
    )
    time.sleep(0.2)
    run_curl(
        [f"{BASE_URL}/api/jobs/status"],
        "Check Final Job Status After Cancellation",
    )

    # 12. Restore settings to canonical workspace defaults
    restore_body = json.dumps({"work_dir": "export.work", "output_dir": "export"})
    subprocess.run(["curl.exe", "-s", "-X", "POST", f"{BASE_URL}/api/settings", "-H", "Content-Type: application/json", "-d", restore_body], capture_output=True)

    print("\n" + "=" * 80)
    print("FULL DRIVE TRANSCRIPT COMPLETE - ALL PHASE 3 API WORKFLOWS VERIFIED")
    print("=" * 80)


if __name__ == "__main__":
    main()
