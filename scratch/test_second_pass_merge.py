import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
from collections import defaultdict
import numpy as np
from backend.engine.cache import EmbeddingCache
from backend.engine.clusterer import FaceClusterer

def main():
    cache = EmbeddingCache("export/.cache")
    records = cache.load_all()
    print(f"Loaded {len(records)} records from cache.")

    # 1. Run first pass clustering
    clusterer = FaceClusterer(
        distance_threshold=0.50,
        seed_min_face_size=64,
        seed_max_yaw=60.0,
        seed_min_det_score=0.70,
    )
    people_before, unrecognized_before = clusterer.cluster(records)
    print(f"Before merge: {len(people_before)} clusters, {len(unrecognized_before.faces)} unrecognized faces.")
    singletons_before = sum(1 for p in people_before if len(p.photo_ids) == 1)
    print(f"Singletons before: {singletons_before}")

    # Helper: compute centroid from top 5 best faces
    def get_cluster_centroid(faces):
        # Sort by det_score desc, then min(w, h) desc
        scored_faces = []
        for f in faces:
            if f.embedding is None:
                continue
            w = f.bbox[2] - f.bbox[0]
            h = f.bbox[3] - f.bbox[1]
            dim = min(w, h)
            scored_faces.append((float(f.det_score), dim, f.embedding))
        scored_faces.sort(key=lambda x: (x[0], x[1]), reverse=True)
        top_faces = scored_faces[:5]
        if not top_faces:
            return None
        embs = np.stack([x[2] for x in top_faces])
        mean_v = np.mean(embs, axis=0)
        norm = np.linalg.norm(mean_v)
        if norm > 1e-8:
            mean_v = mean_v / norm
        return mean_v

    # Compute centroids for all clusters
    centroids = []
    for p in people_before:
        c = get_cluster_centroid(p.faces)
        centroids.append(c)

    n = len(people_before)
    # Tier 1: Auto-merge graph (distance < 0.50)
    adj = defaultdict(list)
    tier1_edges = []
    for i in range(n):
        if centroids[i] is None:
            continue
        for j in range(i + 1, n):
            if centroids[j] is None:
                continue
            dist = float(1.0 - np.dot(centroids[i], centroids[j]))
            if dist < 0.50:
                adj[i].append(j)
                adj[j].append(i)
                tier1_edges.append((i, j, dist))

    print(f"Tier 1 edges (< 0.50): {len(tier1_edges)}")

    # Connected components for auto-merge
    visited = set()
    merged_components = []
    for i in range(n):
        if i not in visited:
            comp = []
            queue = [i]
            visited.add(i)
            while queue:
                curr = queue.pop(0)
                comp.append(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            merged_components.append(comp)

    print(f"Merged components count: {len(merged_components)} (reduced from {n})")

    # Build merged clusters
    merged_clusters_data = []
    for comp in merged_components:
        all_faces = []
        all_photo_ids = []
        for idx in comp:
            all_faces.extend(people_before[idx].faces)
            for pid in people_before[idx].photo_ids:
                if pid not in all_photo_ids:
                    all_photo_ids.append(pid)
        merged_clusters_data.append({
            "comp_indices": comp,
            "orig_ids": [people_before[idx].id for idx in comp],
            "photo_ids": all_photo_ids,
            "faces": all_faces,
        })

    # Sort merged clusters: photo count desc, face count desc
    merged_clusters_data.sort(key=lambda x: (len(x["photo_ids"]), len(x["faces"])), reverse=True)

    # Re-assign IDs
    for idx, cdata in enumerate(merged_clusters_data):
        cdata["new_id"] = f"p{idx+1:03d}"

    # Check collisions in merged clusters
    collision_clusters = 0
    extra_faces = 0
    for cdata in merged_clusters_data:
        pids = [f.photo_id for f in cdata["faces"]]
        if len(pids) > len(set(pids)):
            collision_clusters += 1
            extra_faces += (len(pids) - len(set(pids)))
    print(f"Collision diagnostic after merge: {collision_clusters} clusters with collision, {extra_faces} extra faces.")

    singletons_after = sum(1 for c in merged_clusters_data if len(c["photo_ids"]) == 1)
    print(f"Singletons after merge: {singletons_after}")

    # Recompute centroids for merged clusters
    merged_centroids = []
    for cdata in merged_clusters_data:
        c = get_cluster_centroid(cdata["faces"])
        merged_centroids.append(c)

    # Tier 2: Maybe links (0.50 to 0.60)
    m = len(merged_clusters_data)
    maybe_adj = defaultdict(list)
    maybe_edges = []
    for i in range(m):
        if merged_centroids[i] is None:
            continue
        for j in range(i + 1, m):
            if merged_centroids[j] is None:
                continue
            dist = float(1.0 - np.dot(merged_centroids[i], merged_centroids[j]))
            if 0.50 <= dist <= 0.60:
                maybe_adj[i].append((j, dist))
                maybe_adj[j].append((i, dist))
                maybe_edges.append((i, j, dist))

    print(f"Maybe edges count (0.50 - 0.60): {len(maybe_edges)}")

    # Find connected components of maybe links (groups of size >= 2)
    visited_maybe = set()
    maybe_groups = []
    for i in range(m):
        if i not in visited_maybe and len(maybe_adj[i]) > 0:
            comp = []
            queue = [i]
            visited_maybe.add(i)
            while queue:
                curr = queue.pop(0)
                comp.append(curr)
                for neighbor, _ in maybe_adj[curr]:
                    if neighbor not in visited_maybe:
                        visited_maybe.add(neighbor)
                        queue.append(neighbor)
            if len(comp) >= 2:
                maybe_groups.append(comp)

    print(f"Connected maybe groups count: {len(maybe_groups)}")
    for g_idx, comp in enumerate(maybe_groups):
        cluster_ids = [merged_clusters_data[i]["new_id"] for i in comp]
        photo_counts = [len(merged_clusters_data[i]["photo_ids"]) for i in comp]
        print(f"  Group {g_idx+1}: {cluster_ids} (photo counts: {photo_counts})")

if __name__ == "__main__":
    main()
