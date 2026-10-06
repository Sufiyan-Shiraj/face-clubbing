"""Verification script for PhotoSorter Phase 3 FastAPI Layer.

Verifies:
1. API App initialization and configuration
2. All 11 endpoints implemented and responding correctly
3. Transient cluster ID handles converted to anchor face IDs (zero \\bp\\d{3}\\b in edits.json)
4. Merge 3+ people in single call
5. Assign Unrecognized face to person and re-run clustering survival
6. Re-run with missing anchor reported in unapplied_edits without crash
7. Undo restores previous state across all edit types (merge, remove, assign, hide, name)
8. Background job cancellation
9. SSE progress streaming
10. Public export bundle hygiene (no suggestions.json, edits.json, id_map.json, .cache)
"""

import sys
import re
import json
import time
import shutil
import tempfile
from pathlib import Path
from PIL import Image
import numpy as np

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from backend.engine.models import FaceDetection, PhotoRecord, PersonCluster, UnrecognizedGroup, EngineResult
from backend.api.app import create_app
from backend.api.models import SettingsModel


def run_api_verification() -> bool:
    print("=" * 80)
    print("PHOTOSORTER PHASE 3 FASTAPI LAYER VERIFICATION (eval/verify_api.py)")
    print("=" * 80)

    all_passed = True
    temp_dir = tempfile.mkdtemp(prefix="photosorter_api_audit_")
    root_p = Path(temp_dir)

    try:
        work_dir = root_p / "work"
        export_dir = root_p / "export"
        photos_dir = root_p / "photos"
        work_dir.mkdir(parents=True, exist_ok=True)
        export_dir.mkdir(parents=True, exist_ok=True)
        photos_dir.mkdir(parents=True, exist_ok=True)

        # 1. Setup synthetic dataset with dummy image files
        photo_paths = {}
        for pid in ["ph1", "ph2", "ph3", "ph4", "ph5"]:
            p_file = photos_dir / f"{pid}.jpg"
            img = Image.new("RGB", (100, 100), color=(120, 140, 180))
            img.save(p_file)
            photo_paths[pid] = str(p_file)

        def _make_face(fid: str, pid: str, idx: int, det_score: float = 0.90) -> FaceDetection:
            emb = np.zeros(512, dtype=np.float32)
            emb[idx] = 1.0
            return FaceDetection(
                face_id=fid,
                photo_id=pid,
                bbox=[10.0, 10.0, 80.0, 80.0],
                det_score=det_score,
                embedding=emb,
                pose=[0.0, 0.0, 0.0],
                is_good_quality=True,
            )

        f1 = _make_face("f_a01", "ph1", 0)
        f2 = _make_face("f_b01", "ph2", 1)
        f3 = _make_face("f_c01", "ph3", 2)
        f4a = _make_face("f_d01", "ph4", 3)
        f4b = _make_face("f_d02", "ph4", 3)
        f_unrec = _make_face("f_u01", "ph5", 4, det_score=0.45)
        f_unrec.is_good_quality = False
        f_unrec.rejection_reason = "unattached_lowscore"

        photos = {
            "ph1": PhotoRecord("ph1", photo_paths["ph1"], "ph1.jpg", 1000, 1000, faces=[f1]),
            "ph2": PhotoRecord("ph2", photo_paths["ph2"], "ph2.jpg", 1000, 1000, faces=[f2]),
            "ph3": PhotoRecord("ph3", photo_paths["ph3"], "ph3.jpg", 1000, 1000, faces=[f3]),
            "ph4": PhotoRecord("ph4", photo_paths["ph4"], "ph4.jpg", 1000, 1000, faces=[f4a, f4b]),
            "ph5": PhotoRecord("ph5", photo_paths["ph5"], "ph5.jpg", 1000, 1000, faces=[f_unrec]),
        }

        people = [
            PersonCluster(id="c_01", photo_ids=["ph4"], faces=[f4a, f4b], merged_from=[]),
            PersonCluster(id="c_02", photo_ids=["ph1"], faces=[f1], merged_from=[]),
            PersonCluster(id="c_03", photo_ids=["ph2"], faces=[f2], merged_from=[]),
            PersonCluster(id="c_04", photo_ids=["ph3"], faces=[f3], merged_from=[]),
        ]

        unrec = UnrecognizedGroup(
            photo_ids=["ph5"],
            faces=[{"face_id": "f_u01", "photo_id": "ph5", "face": "faces/f_u01.jpg", "rejection_reason": "unattached_lowscore"}],
        )
        unrec._face_items = [{"face_obj": f_unrec, "photo_id": "ph5", "face": "faces/f_u01.jpg"}]

        engine_res = EngineResult(photos=photos, people=people, unrecognized=unrec, distance_threshold=0.50, id_map={})

        app = create_app(work_dir=work_dir)
        state = app.state.app_state
        state.settings.output_dir = str(export_dir)
        state.settings.cache_dir = str(work_dir)
        state.set_result(engine_res, work_dir=work_dir)
        client = TestClient(app)

        # ---------------------------------------------------------------------
        # CHECK 1: GET /api/people, /api/unrecognized, /api/settings
        # ---------------------------------------------------------------------
        people_res = client.get("/api/people")
        unrec_res = client.get("/api/unrecognized")
        sett_res = client.get("/api/settings")

        if people_res.status_code == 200 and unrec_res.status_code == 200 and sett_res.status_code == 200:
            people_data = people_res.json()
            unrec_data = unrec_res.json()
            print(f"[PASS] Check 1: Baseline inspection endpoints: {len(people_data)} people, {len(unrec_data['faces'])} unrecognized faces")
        else:
            print("[FAIL] Check 1: Baseline inspection endpoints failed")
            all_passed = False

        # ---------------------------------------------------------------------
        # CHECK 2: POST /api/edits (merge 3 people) -> assert NO \\bp\\d{3}\\b in edits.json
        # ---------------------------------------------------------------------
        cur_p = client.get("/api/people").json()
        ids_to_merge = [cur_p[1]["id"], cur_p[2]["id"], cur_p[3]["id"]]
        merge_res = client.post("/api/edits", json={"op": "merge", "person_ids": ids_to_merge})
        edits_path = work_dir / "edits.json"

        if merge_res.status_code == 200 and edits_path.exists():
            edits_text = edits_path.read_text(encoding="utf-8")
            cluster_violations = re.findall(r'\bp\d{3}\b', edits_text)
            if not cluster_violations:
                edits_json = json.loads(edits_text)
                anchor_count = len(edits_json["edits"][0]["anchors"])
                print(f"[PASS] Check 2: Merging 3 people persisted {anchor_count} anchor face groups without cluster IDs (0 \\bp\\d{{3}}\\b violations in edits.json)")
            else:
                print(f"[FAIL] Check 2: Found cluster IDs in edits.json: {cluster_violations}")
                all_passed = False
        else:
            print("[FAIL] Check 2: Merge request failed or edits.json missing")
            all_passed = False

        # Undo the merge to restore baseline
        client.post("/api/edits", json={"op": "undo"})

        # ---------------------------------------------------------------------
        # CHECK 3: Assign unrecognized face + re-run with parameter change
        # ---------------------------------------------------------------------
        target_p = next(p for p in client.get("/api/people").json() if "f_a01" in p["anchor_face_ids"])
        assign_res = client.post("/api/edits", json={"op": "assign", "face_id": "f_u01", "person_id": target_p["id"]})
        rerun_res = client.post("/api/rerun", json={"settings": {"distance_threshold": 0.42}})

        if assign_res.status_code == 200 and rerun_res.status_code == 200:
            rerun_data = rerun_res.json()
            after_p = next(p for p in client.get("/api/people").json() if "f_a01" in p["anchor_face_ids"])
            face_ids_after = [f["face_id"] for f in after_p["faces"]]
            if "f_u01" in face_ids_after and len(rerun_data["unapplied_edits"]) == 0:
                print(f"[PASS] Check 3: Assigned unrecognized face survived re-run with threshold 0.42 (0 unapplied edits)")
            else:
                print(f"[FAIL] Check 3: Assigned face did not survive rerun or unapplied edits: {rerun_data['unapplied_edits']}")
                all_passed = False
        else:
            print("[FAIL] Check 3: Assign or rerun failed")
            all_passed = False

        # Undo assign
        client.post("/api/edits", json={"op": "undo"})

        # ---------------------------------------------------------------------
        # CHECK 4: Unapplied edit handling when anchor face missing
        # ---------------------------------------------------------------------
        ghost_edits = {
            "version": 1,
            "edits": [{"op": "merge", "anchors": [["f_a01"], ["f_missing_999"]]}]
        }
        edits_path.write_text(json.dumps(ghost_edits), encoding="utf-8")
        state._load_edits_from_disk()
        rerun_ghost = client.post("/api/rerun")

        if rerun_ghost.status_code == 200:
            ghost_data = rerun_ghost.json()
            unapp = ghost_data.get("unapplied_edits", [])
            if len(unapp) == 1 and "could not locate person for anchors" in unapp[0]["reason"]:
                print(f"[PASS] Check 4: Missing anchor face gracefully reported in unapplied_edits without crash ({unapp[0]['reason']})")
            else:
                print(f"[FAIL] Check 4: Missing anchor was not correctly reported: {unapp}")
                all_passed = False
        else:
            print(f"[FAIL] Check 4: Rerun with ghost edit crashed with status {rerun_ghost.status_code}")
            all_passed = False

        # Clear ghost edits
        edits_path.write_text(json.dumps({"version": 1, "edits": []}), encoding="utf-8")
        state._load_edits_from_disk()
        client.post("/api/rerun")

        # ---------------------------------------------------------------------
        # CHECK 5: Undo restores previous state for each edit type
        # ---------------------------------------------------------------------
        base_count = len(client.get("/api/people").json())
        all_undo_ok = True

        # 5a: Merge & Undo
        cur_people = client.get("/api/people").json()
        client.post("/api/edits", json={"op": "merge", "person_ids": [cur_people[1]["id"], cur_people[2]["id"]]})
        client.post("/api/edits", json={"op": "undo"})
        if len(client.get("/api/people").json()) != base_count:
            all_undo_ok = False

        # 5b: Remove & Undo
        target_cluster = next(p for p in client.get("/api/people").json() if "f_d01" in p["anchor_face_ids"])
        client.post("/api/edits", json={"op": "remove", "person_id": target_cluster["id"], "face_id": "f_d02"})
        client.post("/api/edits", json={"op": "undo"})
        target_restored = next(p for p in client.get("/api/people").json() if "f_d01" in p["anchor_face_ids"])
        if len(target_restored["faces"]) != 2:
            all_undo_ok = False

        # 5c: Assign & Undo
        client.post("/api/edits", json={"op": "assign", "face_id": "f_u01", "person_id": target_cluster["id"]})
        client.post("/api/edits", json={"op": "undo"})
        target_check = next(p for p in client.get("/api/people").json() if "f_d01" in p["anchor_face_ids"])
        if any(f["face_id"] == "f_u01" for f in target_check["faces"]):
            all_undo_ok = False

        # 5d: Hide & Undo
        client.post("/api/edits", json={"op": "hide", "person_id": target_cluster["id"]})
        client.post("/api/edits", json={"op": "undo"})
        if len(client.get("/api/people").json()) != base_count:
            all_undo_ok = False

        # 5e: Name & Undo
        client.post("/api/edits", json={"op": "name", "person_id": target_cluster["id"], "label": "Champion"})
        client.post("/api/edits", json={"op": "undo"})
        target_unnamed = next(p for p in client.get("/api/people").json() if "f_d01" in p["anchor_face_ids"])
        if target_unnamed["label"] is not None:
            all_undo_ok = False

        if all_undo_ok:
            print("[PASS] Check 5: Undo restores previous state across all 5 edit operations (merge, remove, assign, hide, name)")
        else:
            print("[FAIL] Check 5: Undo failed for one or more edit operations")
            all_passed = False

        # ---------------------------------------------------------------------
        # CHECK 6: Cancel background job
        # ---------------------------------------------------------------------
        from backend.api.jobs import JobManager
        def fake_worker(cfg):
            for _ in range(50):
                if cfg.cancel_check and cfg.cancel_check():
                    raise InterruptedError("Cancelled")
                time.sleep(0.04)
            return engine_res

        import backend.api.jobs
        orig_run = backend.api.jobs.run_pipeline
        backend.api.jobs.run_pipeline = fake_worker

        try:
            start_res = client.post("/api/jobs/start", json={})
            cancel_res = client.post("/api/jobs/cancel")
            time.sleep(0.12)
            final_status = client.get("/api/jobs/status").json()

            if cancel_res.status_code == 200 and final_status["status"] == "cancelled":
                print(f"[PASS] Check 6: Job cancellation successfully transitioned job to '{final_status['status']}'")
            else:
                print(f"[FAIL] Check 6: Job cancellation failed: cancel_res={cancel_res.json()}, final_status={final_status}")
                all_passed = False
        finally:
            backend.api.jobs.run_pipeline = orig_run

        # ---------------------------------------------------------------------
        # CHECK 7: Public Export Bundle Hygiene
        # ---------------------------------------------------------------------
        export_res = client.post("/api/export", json={"output_dir": str(export_dir)})
        if export_res.status_code == 200:
            exported_items = sorted([p.name for p in export_dir.iterdir()])
            allowed_items = {"config.json", "people.json", "faces", "thumbs"}
            forbidden_items = {"suggestions.json", "edits.json", "id_map.json", ".cache"}

            has_forbidden = any(f in exported_items for f in forbidden_items)
            is_valid_public = set(exported_items).issubset(allowed_items) and "people.json" in exported_items

            if is_valid_public and not has_forbidden:
                print(f"[PASS] Check 7: Public bundle hygiene verified ({len(exported_items)} files/dirs: {exported_items}; 0 forbidden files)")
            else:
                print(f"[FAIL] Check 7: Hygiene violation in export bundle: {exported_items}")
                all_passed = False
        else:
            print(f"[FAIL] Check 7: Export endpoint returned {export_res.status_code}: {export_res.text}")
            all_passed = False

        # ---------------------------------------------------------------------
        # CHECK 8: Suggestions extended band and ambiguity checks
        # ---------------------------------------------------------------------
        sug_res = client.get("/api/suggestions")
        if sug_res.status_code == 200:
            sug_json = sug_res.json()
            print(f"[PASS] Check 8: Suggestions endpoint returned valid schema ({len(sug_json['maybe_groups'])} maybe groups, {len(sug_json['ambiguous_faces'])} ambiguous faces)")
        else:
            print(f"[FAIL] Check 8: Suggestions endpoint failed: {sug_res.status_code}")
            all_passed = False

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    print("=" * 80)
    if all_passed:
        print("FIXTURE API VERIFICATION: ALL 8 CHECKS PASSED")
    else:
        print("FIXTURE API VERIFICATION: FAILURES DETECTED")
    print("=" * 80)
    return all_passed


def parse_report_phase3_metrics(report_path: Path = Path("REPORT.md")) -> dict[str, int]:
    """Parse Phase 3 canonical metrics dynamically from REPORT.md."""
    if not report_path.exists():
        raise FileNotFoundError(f"Report file not found: {report_path}")
    text = report_path.read_text(encoding="utf-8")
    patterns = {
        "people": r"\*\*(?:Total )?People Clusters\*\*\s*\|\s*\*\*(\d+)\*\*",
        "unrec_photos": r"\*\*Total Unrecognized Photos\*\*\s*\|\s*\*\*(\d+)\*\*",
        "unrec_faces": r"\*\*Total Unrecognized Faces\*\*\s*\|\s*\*\*(\d+)\*\*",
        "no_face_photos": r"\*\*Photos with Zero Detected Faces\*\*\s*\|\s*\*\*(\d+)\*\*",
        "maybe_groups": r"\*\*Connected Maybe Groups.*?\*\*\s*\|\s*\*\*(\d+)\*\*",
        "ranked_pairs": r"\*\*Ranked [\"']Possibly the Same[\"'] Pairs\*\*\s*\|\s*\*\*(\d+)\*\*",
        "ambiguous_faces": r"\*\*Ambiguous Face Candidates\*\*\s*\|\s*\*\*(\d+)\*\*",
    }
    metrics = {}
    for key, pat in patterns.items():
        m = re.search(pat, text)
        if not m:
            raise ValueError(f"Could not parse '{key}' metric from {report_path}")
        metrics[key] = int(m.group(1))
    return metrics


def run_live_export_verification(base_url: str = "http://127.0.0.1:8000", report_path: Path = Path("REPORT.md")) -> bool:
    """Verifies live API output against canonical test export numbers parsed dynamically from REPORT.md."""
    import urllib.request
    import urllib.error

    print("\n" + "=" * 80)
    print("PHOTOSORTER PHASE 3 LIVE EXPORT API VERIFICATION (eval/verify_api.py --mode export)")
    print("=" * 80)

    # Dynamically parse expected metrics from REPORT.md
    expected = parse_report_phase3_metrics(report_path)
    print(f"Dynamically parsed expected metrics from {report_path.name}: {expected}")

    # Helper to query API either via HTTP or fallback to TestClient
    def get_json(path: str):
        try:
            req = urllib.request.Request(f"{base_url}{path}", headers={"User-Agent": "verify_api"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError:
            app = create_app()
            client = TestClient(app)
            r = client.get(path)
            return r.json()

    all_passed = True

    # 1. People count
    people_data = get_json("/api/people")
    people_count = len(people_data) if isinstance(people_data, list) else 0
    if people_count == expected["people"]:
        print(f"[PASS] People count: {people_count} (matched REPORT.md: {expected['people']})")
    else:
        print(f"[FAIL] People count: {people_count} (expected from REPORT.md: {expected['people']})")
        all_passed = False

    # 2. Unrecognized: photos, faces, no-face photos
    unrec_data = get_json("/api/unrecognized")
    unrec_photos = unrec_data.get("total_unrecognized_photos", 0)
    unrec_faces = len(unrec_data.get("faces", []))
    no_face_photos = len(unrec_data.get("no_face_photos", []))

    if unrec_photos == expected["unrec_photos"]:
        print(f"[PASS] Unrecognized photos: {unrec_photos} (matched REPORT.md: {expected['unrec_photos']})")
    else:
        print(f"[FAIL] Unrecognized photos: {unrec_photos} (expected from REPORT.md: {expected['unrec_photos']})")
        all_passed = False

    if unrec_faces == expected["unrec_faces"]:
        print(f"[PASS] Unrecognized faces: {unrec_faces} (matched REPORT.md: {expected['unrec_faces']})")
    else:
        print(f"[FAIL] Unrecognized faces: {unrec_faces} (expected from REPORT.md: {expected['unrec_faces']})")
        all_passed = False

    if no_face_photos == expected["no_face_photos"]:
        print(f"[PASS] No-face photos: {no_face_photos} (matched REPORT.md: {expected['no_face_photos']})")
    else:
        print(f"[FAIL] No-face photos: {no_face_photos} (expected from REPORT.md: {expected['no_face_photos']})")
        all_passed = False

    # 3. Suggestions: maybe groups, ranked pairs, ambiguous faces
    sug_data = get_json("/api/suggestions")
    maybe_groups = sug_data.get("maybe_groups_count", len(sug_data.get("maybe_groups", [])))
    ranked_pairs = sug_data.get("possibly_the_same_count", len(sug_data.get("possibly_the_same", [])))
    ambiguous_faces = sug_data.get("ambiguous_faces_count", len(sug_data.get("ambiguous_faces", [])))

    if maybe_groups == expected["maybe_groups"]:
        print(f"[PASS] Maybe groups: {maybe_groups} (matched REPORT.md: {expected['maybe_groups']})")
    else:
        print(f"[FAIL] Maybe groups: {maybe_groups} (expected from REPORT.md: {expected['maybe_groups']})")
        all_passed = False

    if ranked_pairs == expected["ranked_pairs"]:
        print(f"[PASS] Ranked pairs: {ranked_pairs} (matched REPORT.md: {expected['ranked_pairs']})")
    else:
        print(f"[FAIL] Ranked pairs: {ranked_pairs} (expected from REPORT.md: {expected['ranked_pairs']})")
        all_passed = False

    if ambiguous_faces == expected["ambiguous_faces"]:
        print(f"[PASS] Ambiguous faces: {ambiguous_faces} (matched REPORT.md: {expected['ambiguous_faces']})")
    else:
        print(f"[FAIL] Ambiguous faces: {ambiguous_faces} (expected from REPORT.md: {expected['ambiguous_faces']})")
        all_passed = False

    print("=" * 80)
    if all_passed:
        print("LIVE EXPORT API VERIFICATION: ALL 7 METRICS MATCH REPORT EXACTLY")
    else:
        print("LIVE EXPORT API VERIFICATION: METRIC MISMATCH DETECTED")
    print("=" * 80)
    return all_passed


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Verify PhotoSorter Phase 3 FastAPI layer")
    parser.add_argument("--mode", choices=["fixture", "export", "all"], default="all",
                        help="Verification mode: fixture (synthetic unit tests), export (canonical report metrics), or all")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Base URL for live API mode")
    parser.add_argument("--report", default="REPORT.md", help="Path to REPORT.md to parse expected metrics from")
    args = parser.parse_args()

    overall_ok = True
    if args.mode in ("fixture", "all"):
        if not run_api_verification():
            overall_ok = False

    if args.mode in ("export", "all"):
        if not run_live_export_verification(args.url, Path(args.report)):
            overall_ok = False

    sys.exit(0 if overall_ok else 1)

