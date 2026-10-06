import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.engine.cache import EmbeddingCache
from backend.engine.clusterer import FaceClusterer
import json
from collections import defaultdict

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

print(f"Total faces mapped to pre-merge clusters: {len(face_to_pre_id)}")

exp_data = json.load(open("export/people.json"))
exp_people = exp_data["people"]

final_to_pre = {}
pre_to_final = {}
inconsistencies = 0

for p in exp_people:
    final_id = p["id"]
    pre_ids = set()
    for f in p["faces"]:
        fid = f["face_id"]
        pre_id = face_to_pre_id.get(fid)
        assert pre_id is not None, f"Face {fid} not found in pre-merge clusters!"
        pre_ids.add(pre_id)
    # Sort pre_ids naturally
    sorted_pre = sorted(list(pre_ids), key=lambda x: int(x[1:]))
    final_to_pre[final_id] = sorted_pre
    for pid in sorted_pre:
        if pid in pre_to_final:
            print(f"ERROR: pre_id {pid} mapped to multiple final IDs: {pre_to_final[pid]} and {final_id}")
            inconsistencies += 1
        pre_to_final[pid] = final_id

print(f"Total pre-merge IDs mapped: {len(pre_to_final)} / 242")
print(f"Inconsistencies: {inconsistencies}")
assert len(pre_to_final) == 242, "Not all 242 pre-merge IDs were mapped!"
assert inconsistencies == 0, "Some pre-merge IDs mapped to multiple final IDs!"

# Print clusters that merged more than 1 pre-merge cluster
multi_merged = {k: v for k, v in final_to_pre.items() if len(v) > 1}
print(f"\nFinal clusters formed by merging >= 2 pre-merge clusters ({len(multi_merged)} clusters):")
for k, v in multi_merged.items():
    print(f"  {k}: merged from {len(v)} pre-clusters: {v}")

print(f"\nFinal p001 merged from: {final_to_pre['p001']}")
