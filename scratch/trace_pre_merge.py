import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.engine.cache import EmbeddingCache
from backend.engine.clusterer import FaceClusterer
import numpy as np
from collections import defaultdict
import json

cache = EmbeddingCache("export/.cache")
records = cache.load_all()

# Run clusterer with second_pass_merge=False to get the exact 242 pre-merge clusters
cl_pre = FaceClusterer(second_pass_merge=False)
people_pre, unrec_pre = cl_pre.cluster(records)
print(f"Pre-merge clusters: {len(people_pre)}")

# Let's inspect p001, p080, p121, p129 in people_pre
pre_dict = {p.id: p for p in people_pre}
print(f"p001 photos: {len(pre_dict['p001'].photo_ids)}, faces: {len(pre_dict['p001'].faces)}")
print(f"p080 photos: {len(pre_dict['p080'].photo_ids)}, faces: {len(pre_dict['p080'].faces)}")
print(f"p121 photos: {len(pre_dict['p121'].photo_ids)}, faces: {len(pre_dict['p121'].faces)}")
print(f"p129 photos: {len(pre_dict['p129'].photo_ids)}, faces: {len(pre_dict['p129'].faces)}")

# Now run with second_pass_merge=True
cl_post = FaceClusterer(second_pass_merge=True)
people_post, unrec_post = cl_post.cluster(records)
print(f"Post-merge clusters: {len(people_post)}")

# Let's see how pre-merge clusters map to post-merge clusters
# Let's trace centroids of pre-merge clusters
pre_centroids = [
    FaceClusterer.compute_cluster_centroid(p.faces, top_k=5)
    for p in people_pre
]

n_pre = len(people_pre)
merge_adj = defaultdict(list)
for i in range(n_pre):
    c_i = pre_centroids[i]
    if c_i is None: continue
    for j in range(i + 1, n_pre):
        c_j = pre_centroids[j]
        if c_j is None: continue
        d = float(1.0 - np.dot(c_i, c_j))
        if d < 0.50:
            merge_adj[i].append(j)
            merge_adj[j].append(i)

visited = set()
components = []
for i in range(n_pre):
    if i not in visited:
        comp = []
        q = [i]
        visited.add(i)
        while q:
            curr = q.pop(0)
            comp.append(curr)
            for nbr in merge_adj[curr]:
                if nbr not in visited:
                    visited.add(nbr)
                    q.append(nbr)
        components.append(comp)

# Build merged clusters data
merged_data = []
for comp in components:
    comp_faces = []
    comp_photos = []
    for idx in comp:
        comp_faces.extend(people_pre[idx].faces)
        for pid in people_pre[idx].photo_ids:
            if pid not in comp_photos:
                comp_photos.append(pid)
    merged_data.append({
        "comp_pre_ids": [people_pre[idx].id for idx in comp],
        "photos": comp_photos,
        "faces": comp_faces,
    })

# Sort same way: len(photos) desc, len(faces) desc
merged_data.sort(key=lambda item: (len(item["photos"]), len(item["faces"])), reverse=True)

# Build id_map: pre_id -> post_id
id_map = {}
post_to_pre = {}
for final_idx, item in enumerate(merged_data):
    final_id = f"p{final_idx+1:03d}"
    item["final_id"] = final_id
    post_to_pre[final_id] = item["comp_pre_ids"]
    for pre_id in item["comp_pre_ids"]:
        id_map[pre_id] = final_id

print("\nMerged into p001:")
print(f"p001 was merged from: {post_to_pre['p001']}")

for pre_id in post_to_pre['p001']:
    p = pre_dict[pre_id]
    filenames = [records[pid].file_name for pid in p.photo_ids]
    face_ids = [f.face_id for f in p.faces]
    print(f"  {pre_id}: {len(p.photo_ids)} photos: {p.photo_ids} ({filenames})")
    print(f"       faces ({len(face_ids)}): {face_ids}")
