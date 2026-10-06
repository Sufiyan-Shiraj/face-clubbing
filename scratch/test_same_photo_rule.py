import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.engine.cache import EmbeddingCache
from backend.engine.clusterer import FaceClusterer
import numpy as np
from collections import defaultdict

cache = EmbeddingCache("export/.cache")
records = cache.load_all()
cl = FaceClusterer(second_pass_merge=False)
people_pre, _ = cl.cluster(records)
n_init = len(people_pre)
initial_centroids = [cl.compute_cluster_centroid(p.faces, top_k=5) for p in people_pre]

same_photo_merge_max = 0.40

merge_adj = defaultdict(list)
blocked_pairs = []

for i in range(n_init):
    c_i = initial_centroids[i]
    if c_i is None: continue
    for j in range(i+1, n_init):
        c_j = initial_centroids[j]
        if c_j is None: continue
        d = float(1.0 - np.dot(c_i, c_j))
        if d < 0.50:
            pids_i = {f.photo_id: [] for f in people_pre[i].faces}
            for f in people_pre[i].faces: pids_i[f.photo_id].append(f)
            pids_j = {f.photo_id: [] for f in people_pre[j].faces}
            for f in people_pre[j].faces: pids_j[f.photo_id].append(f)
            
            conflict = False
            for pid in set(pids_i.keys()) & set(pids_j.keys()):
                for fi in pids_i[pid]:
                    for fj in pids_j[pid]:
                        sp_d = float(1.0 - np.dot(fi.embedding, fj.embedding))
                        if sp_d > same_photo_merge_max: conflict = True
            if conflict:
                blocked_pairs.append((i, j, d))
            else:
                merge_adj[i].append(j)
                merge_adj[j].append(i)

visited_merge = set()
merged_components = []
for i in range(n_init):
    if i not in visited_merge:
        comp = []
        queue = [i]
        visited_merge.add(i)
        while queue:
            curr = queue.pop(0)
            comp.append(curr)
            for neighbor in merge_adj[curr]:
                if neighbor not in visited_merge:
                    visited_merge.add(neighbor)
                    queue.append(neighbor)
        merged_components.append(comp)

merged_clusters = []
for comp in merged_components:
    comp_faces = []
    comp_photos = []
    for idx in comp:
        comp_faces.extend(people_pre[idx].faces)
        for pid in people_pre[idx].photo_ids:
            if pid not in comp_photos: comp_photos.append(pid)
    merged_clusters.append({
        'photo_ids': comp_photos,
        'faces': comp_faces,
        'orig_ids': [people_pre[idx].id for idx in comp],
        'orig_indices': comp,
    })

merged_clusters.sort(key=lambda item: (len(item['photo_ids']), len(item['faces'])), reverse=True)
for idx, c in enumerate(merged_clusters): c['new_id'] = f"p{idx+1:03d}"
final_centroids = [cl.compute_cluster_centroid(c['faces'], top_k=5) for c in merged_clusters]

init_to_final = {}
for final_idx, c in enumerate(merged_clusters):
    for orig_idx in c['orig_indices']:
        init_to_final[orig_idx] = final_idx

# Check maybe links
m = len(merged_clusters)
print("Evaluating Case A (include blocked pairs < 0.60):")
links_a = []
for i, j, init_d in blocked_pairs:
    fi = init_to_final[i]
    fj = init_to_final[j]
    if fi != fj:
        final_d = float(1.0 - np.dot(final_centroids[fi], final_centroids[fj]))
        links_a.append((min(fi, fj), max(fi, fj), final_d, "same_photo_conflict"))

for i in range(m):
    for j in range(i+1, m):
        d = float(1.0 - np.dot(final_centroids[i], final_centroids[j]))
        if 0.50 <= d <= 0.60:
            pids_i = {f.photo_id: f for f in merged_clusters[i]['faces']}
            pids_j = {f.photo_id: f for f in merged_clusters[j]['faces']}
            common = set(pids_i.keys()) & set(pids_j.keys())
            has_conflict = False
            for pid in common:
                sp_d = 1.0 - np.dot(pids_i[pid].embedding, pids_j[pid].embedding)
                if sp_d > same_photo_merge_max: has_conflict = True
            reason = "same_photo_conflict" if has_conflict else "centroid_band"
            links_a.append((i, j, d, reason))

unique_links_a = {}
for u, v, d, r in links_a:
    key = (min(u, v), max(u, v))
    if key not in unique_links_a:
        unique_links_a[key] = (d, r)

print(f"Total links in Case A: {len(unique_links_a)}")
for (u, v), (d, r) in sorted(unique_links_a.items(), key=lambda x: (x[1][1], x[1][0])):
    id_u = merged_clusters[u]['new_id']
    id_v = merged_clusters[v]['new_id']
    print(f"  {id_u} - {id_v}: d={d:.4f}, reason={r}")
