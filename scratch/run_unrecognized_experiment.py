import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from collections import defaultdict
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from backend.engine.cache import EmbeddingCache
from backend.engine.clusterer import FaceClusterer

def run_clustering_with_cap(photos, attach_cap=0.45, same_photo_merge_max=0.40):
    cl = FaceClusterer()

    # 1. Categorize faces into seeds and non-seeds
    seeds = []
    non_seeds = []
    for pid, pdata in photos.items():
        for face in pdata.faces:
            if face.embedding is None:
                continue
            w = face.bbox[2] - face.bbox[0]
            h = face.bbox[3] - face.bbox[1]
            face_dim = min(w, h)
            yaw = abs(face.pose[1]) if face.pose and len(face.pose) >= 2 else 0.0
            score = face.det_score

            is_seed = (
                face_dim >= 64
                and yaw <= 60.0
                and score >= 0.70
            )

            if is_seed:
                seeds.append(face)
            else:
                if face_dim < 64:
                    reason = "unattached_small"
                elif yaw > 60.0:
                    reason = "unattached_profile"
                else:
                    reason = "unattached_lowscore"
                non_seeds.append((face, reason))

    # 2. Cluster seeds using Agglomerative Clustering
    cluster_map = defaultdict(list)
    if seeds:
        X = np.stack([f.embedding for f in seeds])
        model = AgglomerativeClustering(
            metric="cosine",
            linkage="average",
            distance_threshold=0.50,
            n_clusters=None,
        )
        labels = model.fit_predict(X)
        for idx, label in enumerate(labels):
            cluster_map[int(label)].append(seeds[idx])

    # 3. Attach non-seed faces with specified attach_cap
    cluster_seed_embs = {
        cid: np.stack([f.embedding for f in members])
        for cid, members in cluster_map.items()
    }
    cluster_photo_ids = {
        cid: set(f.photo_id for f in members)
        for cid, members in cluster_map.items()
    }

    unattached_faces = []
    attached_count = 0
    unattached_by_reason = defaultdict(int)

    for face, reason in non_seeds:
        dists = []
        for cid, embs in cluster_seed_embs.items():
            dots = np.dot(embs, face.embedding)
            avg_dist = float(1.0 - np.mean(dots))
            dists.append((avg_dist, cid))

        dists.sort(key=lambda x: x[0])
        d1, c1 = dists[0] if len(dists) > 0 else (float("inf"), None)
        d2, c2 = dists[1] if len(dists) > 1 else (float("inf"), None)

        can_attach = (
            c1 is not None
            and d1 < attach_cap
            and (d2 - d1 >= 0.05)
            and (face.photo_id not in cluster_photo_ids[c1])
        )

        if can_attach and c1 is not None:
            face.is_good_quality = True
            face.rejection_reason = None
            cluster_map[c1].append(face)
            cluster_photo_ids[c1].add(face.photo_id)
            attached_count += 1
        else:
            face.is_good_quality = False
            # If distance to nearest cluster is < 0.50, reason is ambiguous
            if d1 < 0.50:
                final_reason = "ambiguous"
            else:
                final_reason = reason
            face.rejection_reason = final_reason
            unattached_faces.append(face)
            unattached_by_reason[final_reason] += 1

    # 4. Initial clusters before merge
    initial_clusters = []
    for _, faces in cluster_map.items():
        pids = list(dict.fromkeys(f.photo_id for f in faces))
        initial_clusters.append({
            "photo_ids": pids,
            "faces": faces,
        })
    initial_clusters.sort(key=lambda item: (len(item["photo_ids"]), len(item["faces"])), reverse=True)

    # 5. Second-pass merge with same_photo_merge_max rule
    n_init = len(initial_clusters)
    initial_centroids = [cl.compute_cluster_centroid(c["faces"], top_k=5) for c in initial_clusters]
    merge_adj = defaultdict(list)

    for i in range(n_init):
        c_i = initial_centroids[i]
        if c_i is None: continue
        for j in range(i+1, n_init):
            c_j = initial_centroids[j]
            if c_j is None: continue
            dist = float(1.0 - np.dot(c_i, c_j))
            if dist < 0.50:
                # check same photo collision
                pids_i = {f.photo_id: [] for f in initial_clusters[i]["faces"]}
                for f in initial_clusters[i]["faces"]: pids_i[f.photo_id].append(f)
                pids_j = {f.photo_id: [] for f in initial_clusters[j]["faces"]}
                for f in initial_clusters[j]["faces"]: pids_j[f.photo_id].append(f)

                conflict = False
                for pid in set(pids_i.keys()) & set(pids_j.keys()):
                    for fi in pids_i[pid]:
                        for fj in pids_j[pid]:
                            sp_d = float(1.0 - np.dot(fi.embedding, fj.embedding))
                            if sp_d > same_photo_merge_max:
                                conflict = True
                if not conflict:
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
            comp_faces.extend(initial_clusters[idx]["faces"])
            for pid in initial_clusters[idx]["photo_ids"]:
                if pid not in comp_photos:
                    comp_photos.append(pid)
        merged_clusters.append({
            "photo_ids": comp_photos,
            "faces": comp_faces,
        })

    merged_clusters.sort(key=lambda item: (len(item["photo_ids"]), len(item["faces"])), reverse=True)

    # Collision diagnostic
    colliding = 0
    extra_faces = 0
    for c in merged_clusters:
        pids = [f.photo_id for f in c["faces"]]
        if len(pids) > len(set(pids)):
            colliding += 1
            extra_faces += (len(pids) - len(set(pids)))

    return {
        "attach_cap": attach_cap,
        "attached_count": attached_count,
        "unattached_count": len(unattached_faces),
        "unattached_by_reason": dict(unattached_by_reason),
        "total_clusters": len(merged_clusters),
        "singletons": sum(1 for c in merged_clusters if len(c["photo_ids"]) == 1),
        "colliding_clusters": colliding,
        "extra_faces": extra_faces,
        "initial_clusters": initial_clusters,
        "merged_clusters": merged_clusters,
        "unattached_faces": unattached_faces,
    }

def test_post_merge_ambiguous_attach(photos):
    # Run default clustering
    res = run_clustering_with_cap(photos, attach_cap=0.45, same_photo_merge_max=0.40)
    ambiguous_faces = [f for f in res["unattached_faces"] if f.rejection_reason == "ambiguous"]
    merged_clusters = res["merged_clusters"]

    cl = FaceClusterer()
    # Compute centroids of post-merge clusters from top-5 faces
    post_centroids = [cl.compute_cluster_centroid(c["faces"], top_k=5) for c in merged_clusters]
    # Cluster photo sets
    cluster_photo_ids = [set(c["photo_ids"]) for c in merged_clusters]

    # Re-run attach step for ambiguous faces against post-merge clusters
    attached = 0
    for face in ambiguous_faces:
        dists = []
        for cid, c_emb in enumerate(post_centroids):
            if c_emb is None: continue
            d = float(1.0 - np.dot(c_emb, face.embedding))
            dists.append((d, cid))
        dists.sort(key=lambda x: x[0])
        d1, c1 = dists[0] if len(dists) > 0 else (float("inf"), None)
        d2, c2 = dists[1] if len(dists) > 1 else (float("inf"), None)

        # Default settings: dist < 0.45, margin >= 0.05, no same photo
        can_attach = (
            c1 is not None
            and d1 < 0.45
            and (d2 - d1 >= 0.05)
            and (face.photo_id not in cluster_photo_ids[c1])
        )
        if can_attach:
            attached += 1
            cluster_photo_ids[c1].add(face.photo_id)

    return len(ambiguous_faces), attached

def main():
    cache = EmbeddingCache("export/.cache")
    photos = cache.load_all()

    print("=== UNRECOGNIZED RECOVERY EXPERIMENT (DISTANCE CAP SWEEP) ===")
    for cap in [0.45, 0.50, 0.55]:
        r = run_clustering_with_cap(photos, attach_cap=cap, same_photo_merge_max=0.40)
        print(f"\nAttach Cap: {cap}")
        print(f"  Faces Attached: {r['attached_count']}")
        print(f"  Faces Unrecognized: {r['unattached_count']}")
        print(f"  Unrecognized Breakdown: {r['unattached_by_reason']}")
        print(f"  Total Clusters: {r['total_clusters']}")
        print(f"  Singletons: {r['singletons']}")
        print(f"  Collision Clusters: {r['colliding_clusters']}, Extra Faces: {r['extra_faces']}")

    print("\n=== POST-MERGE ATTACH FOR AMBIGUOUS FACES ===")
    total_amb, attached_amb = test_post_merge_ambiguous_attach(photos)
    print(f"Total Ambiguous Faces: {total_amb}")
    print(f"Attached after post-merge attach: {attached_amb} / {total_amb}")

if __name__ == "__main__":
    main()
