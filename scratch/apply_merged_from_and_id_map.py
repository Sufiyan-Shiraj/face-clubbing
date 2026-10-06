import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.engine.cache import EmbeddingCache
from backend.engine.clusterer import FaceClusterer
import json

cache = EmbeddingCache("export/.cache")
records = cache.load_all()

# Pre-merge 242 clusters
cl_pre = FaceClusterer(second_pass_merge=False)
people_pre, _ = cl_pre.cluster(records)
assert len(people_pre) == 242

face_to_pre_id = {}
for p in people_pre:
    for f in p.faces:
        face_to_pre_id[f.face_id] = p.id

with open("export/people.json", "r", encoding="utf-8") as f:
    exp_data = json.load(f)

exp_people = exp_data["people"]
assert len(exp_people) == 189

pre_to_final = {}
for p in exp_people:
    final_id = p["id"]
    pre_ids = set()
    for f in p["faces"]:
        fid = f["face_id"]
        pre_id = face_to_pre_id[fid]
        pre_ids.add(pre_id)
    sorted_pre = sorted(list(pre_ids), key=lambda x: int(x[1:]))
    p["merged_from"] = sorted_pre
    p["merged_from_numbering"] = "pre-merge 242"
    for pid in sorted_pre:
        pre_to_final[pid] = final_id

assert len(pre_to_final) == 242

# Write updated export/people.json
with open("export/people.json", "w", encoding="utf-8") as f:
    json.dump(exp_data, f, indent=2)
print("Updated export/people.json successfully!")

# Also update viewer/public/people.json if it exists
viewer_public_people = Path("viewer/public/people.json")
if viewer_public_people.exists():
    with open(viewer_public_people, "w", encoding="utf-8") as f:
        json.dump(exp_data, f, indent=2)
    print("Updated viewer/public/people.json successfully!")

# Write id_map.json
# Sort keys naturally: p001 to p242
sorted_pre_keys = sorted(list(pre_to_final.keys()), key=lambda x: int(x[1:]))
ordered_map = {k: pre_to_final[k] for k in sorted_pre_keys}

id_map_payload = {
    "_metadata": {
        "description": "Mapping from pre-merge 242 cluster IDs to final 189 cluster IDs",
        "source_numbering": "pre-merge 242",
        "target_numbering": "final 189",
        "total_pre_merge_clusters": 242,
        "total_final_clusters": 189
    },
    "id_map": ordered_map
}

# We also provide a direct dictionary so whether someone expects { "_metadata": ..., "id_map": ... } or direct { "p001": ... } they can access it, or let's write ordered_map directly at root of id_map.json?
# Let's check: "write an `id_map.json`: pre-merge ID to final ID."
# To be completely safe for any script that does `json.load(open('id_map.json'))['p001']`, let's make id_map.json have the pre-merge keys directly, with an optional metadata key like `_source_numbering`:
flat_id_map = {
    "_metadata": {
        "source": "pre-merge 242",
        "target": "final 189",
        "count_pre": 242,
        "count_final": 189
    }
}
flat_id_map.update(ordered_map)

with open("id_map.json", "w", encoding="utf-8") as f:
    json.dump(flat_id_map, f, indent=2)
with open("export/id_map.json", "w", encoding="utf-8") as f:
    json.dump(flat_id_map, f, indent=2)
with open("export/.cache/id_map.json", "w", encoding="utf-8") as f:
    json.dump(flat_id_map, f, indent=2)

print("Wrote id_map.json with 242 keys to root, export/, and export/.cache/!")
