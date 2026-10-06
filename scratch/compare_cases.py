import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scratch.test_same_photo_rule import merged_clusters, final_centroids, blocked_pairs, init_to_final, same_photo_merge_max
import numpy as np
from collections import defaultdict

m = len(merged_clusters)
# Case B: strictly 0.50 <= d <= 0.60
links_b = []
for i in range(m):
    for j in range(i+1, m):
        d = float(1.0 - np.dot(final_centroids[i], final_centroids[j]))
        if 0.50 <= d <= 0.60:
            pids_i = {f.photo_id: [] for f in merged_clusters[i]['faces']}
            for f in merged_clusters[i]['faces']: pids_i[f.photo_id].append(f)
            pids_j = {f.photo_id: [] for f in merged_clusters[j]['faces']}
            for f in merged_clusters[j]['faces']: pids_j[f.photo_id].append(f)
            conflict = False
            for pid in set(pids_i.keys()) & set(pids_j.keys()):
                for fi in pids_i[pid]:
                    for fj in pids_j[pid]:
                        if (1.0 - np.dot(fi.embedding, fj.embedding)) > same_photo_merge_max:
                            conflict = True
            reason = 'same_photo_conflict' if conflict else 'centroid_band'
            links_b.append((i, j, d, reason))

print('Case B (0.50 <= d <= 0.60) links count:', len(links_b))
for u, v, d, r in links_b:
    if r == 'same_photo_conflict':
        print(f"  {merged_clusters[u]['new_id']} - {merged_clusters[v]['new_id']}: d={d:.4f}, reason={r}")

# Check connected components for Case B
adj_b = defaultdict(list)
for u, v, d, r in links_b:
    adj_b[u].append(v)
    adj_b[v].append(u)

visited = set()
groups_b = []
for i in range(m):
    if i not in visited and len(adj_b[i]) > 0:
        comp = []
        queue = [i]
        visited.add(i)
        while queue:
            curr = queue.pop(0)
            comp.append(curr)
            for neighbor in adj_b[curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        if len(comp) >= 2:
            groups_b.append(comp)

print(f"Case B groups count: {len(groups_b)}")

# Now check Case A: includes blocked pairs under 0.50
links_a = []
for i, j, init_d in blocked_pairs:
    fi = init_to_final[i]
    fj = init_to_final[j]
    if fi != fj:
        final_d = float(1.0 - np.dot(final_centroids[fi], final_centroids[fj]))
        links_a.append((min(fi, fj), max(fi, fj), final_d, "same_photo_conflict"))

for u, v, d, r in links_b:
    links_a.append((u, v, d, r))

unique_a = {}
for u, v, d, r in links_a:
    key = (min(u, v), max(u, v))
    if key not in unique_a:
        unique_a[key] = (d, r)

print(f"Case A unique links count: {len(unique_a)}")
adj_a = defaultdict(list)
for (u, v), (d, r) in unique_a.items():
    adj_a[u].append(v)
    adj_a[v].append(u)

visited = set()
groups_a = []
for i in range(m):
    if i not in visited and len(adj_a[i]) > 0:
        comp = []
        queue = [i]
        visited.add(i)
        while queue:
            curr = queue.pop(0)
            comp.append(curr)
            for neighbor in adj_a[curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        if len(comp) >= 2:
            groups_a.append(comp)

print(f"Case A groups count: {len(groups_a)}")
