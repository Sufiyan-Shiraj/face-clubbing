import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
from backend.engine.pipeline import run_pipeline, EngineConfig
from backend.engine.clusterer import FaceClusterer
from backend.engine.cache import EmbeddingCache

def main():
    config = EngineConfig(
        input_path="test_photos",
        output_dir="export",
        cache_dir="export/.cache",
        same_photo_merge_max=0.40,
        second_pass_merge=True,
    )
    result = run_pipeline(config)
    print(f"Pipeline finished. People: {len(result.people)}, Unrecognized: {len(result.unrecognized.photo_ids)} photos, {len(result.unrecognized.faces)} faces.")

    # Now apply merged_from and build id_map.json
    cache = EmbeddingCache("export/.cache")
    records = cache.load_all()
    cl_pre = FaceClusterer(second_pass_merge=False)
    people_pre, _ = cl_pre.cluster(records)
    print(f"Pre-merge clusters: {len(people_pre)}")
    assert len(people_pre) == 242

    face_to_pre_id = {}
    for p in people_pre:
        for f in p.faces:
            face_to_pre_id[f.face_id] = p.id

    with open("export/people.json", "r", encoding="utf-8") as f:
        exp_data = json.load(f)

    exp_people = exp_data["people"]
    print(f"Final exported clusters: {len(exp_people)}")

    pre_to_final = {}
    for p in exp_people:
        final_id = p["id"]
        pre_ids = set()
        for f in p["faces"]:
            fid = f["face_id"]
            if fid in face_to_pre_id:
                pre_ids.add(face_to_pre_id[fid])
        sorted_pre = sorted(list(pre_ids), key=lambda x: int(x[1:]))
        p["merged_from"] = sorted_pre
        p["merged_from_numbering"] = "pre-merge 242"
        for pid in sorted_pre:
            pre_to_final[pid] = final_id

    assert len(pre_to_final) == 242, f"Expected 242 pre-merge keys, got {len(pre_to_final)}"

    # Write updated export/people.json
    with open("export/people.json", "w", encoding="utf-8") as f:
        json.dump(exp_data, f, indent=2)
    print("Updated export/people.json with merged_from successfully!")

    # Also update viewer/public/people.json if it exists
    viewer_public_people = Path("viewer/public/people.json")
    if viewer_public_people.exists():
        with open(viewer_public_people, "w", encoding="utf-8") as f:
            json.dump(exp_data, f, indent=2)
        print("Updated viewer/public/people.json successfully!")

    # Write id_map.json
    sorted_pre_keys = sorted(list(pre_to_final.keys()), key=lambda x: int(x[1:]))
    ordered_map = {k: pre_to_final[k] for k in sorted_pre_keys}

    flat_id_map = {
        "_metadata": {
            "source": "pre-merge 242",
            "target": f"final {len(exp_people)}",
            "count_pre": 242,
            "count_final": len(exp_people),
            "same_photo_merge_max": 0.40,
        }
    }
    flat_id_map.update(ordered_map)

    with open("id_map.json", "w", encoding="utf-8") as f:
        json.dump(flat_id_map, f, indent=2)
    with open("export/id_map.json", "w", encoding="utf-8") as f:
        json.dump(flat_id_map, f, indent=2)
    with open("export/.cache/id_map.json", "w", encoding="utf-8") as f:
        json.dump(flat_id_map, f, indent=2)
    print(f"Wrote id_map.json mapping 242 -> {len(exp_people)} to root, export/, and export/.cache/!")

if __name__ == "__main__":
    main()
