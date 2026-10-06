"""TASK 5 Verification Script: Real job execution with SSE progress streaming and cancellation test.

Steps:
1. Start SSE listener on /api/jobs/progress.
2. POST /api/jobs/start with real test_photos input_path.
3. Stream and display SSE events (capturing >= 5 events with current, total, percent, stage, eta).
4. Wait for completion, then verify GET /api/people matches CLI export (192 people, 445 unrecognized faces).
5. Start a second job, wait until current > 0, then POST /api/jobs/cancel.
6. Verify final status shows status == "cancelled" and current > 0.
"""

import json
import threading
import time
import urllib.request
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"


def http_post(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_get(url: str) -> dict:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def listen_sse(events_list: list, stop_event: threading.Event):
    req = urllib.request.Request(f"{BASE_URL}/api/jobs/progress", headers={"Accept": "text/event-stream"})
    try:
        with urllib.request.urlopen(req, timeout=60) as stream:
            for raw_line in stream:
                if stop_event.is_set():
                    break
                line = raw_line.decode("utf-8").strip()
                if line.startswith("data:"):
                    raw_data = line[5:].strip()
                    try:
                        event = json.loads(raw_data)
                        events_list.append(event)
                    except Exception:
                        pass
    except Exception as e:
        pass


def main():
    print("================================================================================")
    print("TASK 5: Real Job Execution with SSE Progress and Cancellation")
    print("================================================================================\n")

    # --- PART 1: Real Job Execution to Completion ---
    print("--- PART 1: Starting Real Job on Full Dataset ('test_photos') ---")
    sse_events = []
    stop_listener = threading.Event()
    listener_thread = threading.Thread(target=listen_sse, args=(sse_events, stop_listener), daemon=True)
    listener_thread.start()
    time.sleep(0.5)

    start_payload = {
        "input_path": "test_photos",
        "output_dir": "export",
        "cache_dir": "export.work",
    }
    start_resp = http_post(f"{BASE_URL}/api/jobs/start", start_payload)
    print(f"POST /api/jobs/start response:")
    print(json.dumps(start_resp, indent=2))
    job_id = start_resp.get("job_id")

    # Monitor until completion
    print("\nStreaming SSE events from /api/jobs/progress...")
    captured_progress_events = []
    last_printed_idx = 0
    max_wait = 120
    start_t = time.time()

    while time.time() - start_t < max_wait:
        # Check newly arrived events
        while last_printed_idx < len(sse_events):
            evt = sse_events[last_printed_idx]
            last_printed_idx += 1
            if evt.get("current", 0) > 0:
                captured_progress_events.append(evt)
                if len(captured_progress_events) <= 10 or evt.get("current") % 50 == 0:
                    print(
                        f"  [SSE Event {len(captured_progress_events)}] stage={evt.get('stage')}, "
                        f"current={evt.get('current')}/{evt.get('total')}, "
                        f"percent={evt.get('percent')}%, "
                        f"eta={evt.get('eta_seconds')}s, "
                        f"file={evt.get('current_file')}"
                    )

        status = http_get(f"{BASE_URL}/api/jobs/status")
        if status.get("status") in ["completed", "failed", "cancelled"]:
            print(f"\nJob reached terminal state: {status.get('status')} ({status.get('message')})")
            break
        time.sleep(0.5)

    stop_listener.set()

    print(f"\nTotal SSE events captured: {len(sse_events)}")
    print(f"Total detecting progress events captured: {len(captured_progress_events)}")
    assert len(captured_progress_events) >= 5, f"Expected at least 5 progress events, got {len(captured_progress_events)}"

    # Sample of at least 5 progress events to paste into the report
    print("\n--- Paste Sample of 5 SSE Events (as required by TASK 5) ---")
    sample_indices = [
        0,
        len(captured_progress_events) // 4,
        len(captured_progress_events) // 2,
        (3 * len(captured_progress_events)) // 4,
        len(captured_progress_events) - 1,
    ]
    for i in sample_indices:
        e = captured_progress_events[i]
        print(f"Event: current={e.get('current')}, total={e.get('total')}, percent={e.get('percent')}%, stage={e.get('stage')}, eta={e.get('eta_seconds')}s, file={e.get('current_file')}")

    # Confirm GET /api/people matches CLI export (192 people, 445 unrecognized faces)
    people_data = http_get(f"{BASE_URL}/api/people")
    unrec_data = http_get(f"{BASE_URL}/api/unrecognized")
    people_count = len(people_data)
    unrec_faces_count = len(unrec_data.get("faces", []))
    unrec_photos_count = unrec_data.get("total_unrecognized_photos", 0)

    print(f"\nGET /api/people count:       {people_count} (expected 192)")
    print(f"GET /api/unrecognized faces:  {unrec_faces_count} (expected 445)")
    print(f"GET /api/unrecognized photos: {unrec_photos_count} (expected 168)")

    assert people_count == 192, f"Expected 192 people, got {people_count}"
    assert unrec_faces_count == 445, f"Expected 445 unrecognized faces, got {unrec_faces_count}"
    assert unrec_photos_count == 168, f"Expected 168 unrecognized photos, got {unrec_photos_count}"
    print("[PASS] Full set finished and matches canonical CLI export exactly!")

    # --- PART 2: Mid-way Cancellation Test ---
    print("\n--- PART 2: Starting Second Job to Cancel Mid-Way ---")
    start_resp2 = http_post(f"{BASE_URL}/api/jobs/start", start_payload)
    print(f"POST /api/jobs/start response:")
    print(json.dumps(start_resp2, indent=2))

    # Wait until current > 0
    poll_start = time.time()
    cancelled_status = None
    while time.time() - poll_start < 30:
        st = http_get(f"{BASE_URL}/api/jobs/status")
        if st.get("current", 0) > 0 and st.get("status") == "running":
            print(f"Job in progress: current={st.get('current')}/{st.get('total')}. Issuing cancel...")
            cancel_resp = http_post(f"{BASE_URL}/api/jobs/cancel", {})
            print("POST /api/jobs/cancel response:")
            print(json.dumps(cancel_resp, indent=2))
            break
        time.sleep(0.05)

    # Wait for cancellation to settle
    time.sleep(0.5)
    final_cancel_status = http_get(f"{BASE_URL}/api/jobs/status")
    print("\nGET /api/jobs/status after cancellation:")
    print(json.dumps(final_cancel_status, indent=2))

    print(f"\nAsserting: status == 'cancelled' and current > 0...")
    print(f"  status:  '{final_cancel_status.get('status')}'")
    print(f"  current: {final_cancel_status.get('current')}")
    assert final_cancel_status.get("status") == "cancelled"
    assert final_cancel_status.get("current", 0) > 0

    # Restore server state back to pristine canonical export baseline
    try:
        http_post(f"{BASE_URL}/api/settings", {"work_dir": "export.work"})
    except Exception:
        pass

    print("\n[PASS] Mid-way cancellation verified: current > 0 and status is 'cancelled'.")
    print("================================================================================")
    print("TASK 5 VERIFICATION RESULT: PASS")
    print("================================================================================")


if __name__ == "__main__":
    main()
