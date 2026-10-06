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

    # 1. Run clusterer to get initial 242 clusters
    cl_pre = FaceClusterer(second_pass_merge=False)
    people_pre, unrec_pre = cl_pre.cluster(records)
    assert len(people_pre) == 242, f"Expected 242 pre-merge clusters, got {len(people_pre)}"
    pre_by_id = {p.id: p for p in people_pre}

    # 2. Compute centroids for 242 clusters
    centroids_pre = [
        FaceClusterer.compute_cluster_centroid(p.faces, top_k=5)
        for p in people_pre
    ]

    # 3. Find auto-merge edges (d < 0.50)
    n_pre = len(people_pre)
    adj = defaultdict(list)
    tier1_edges = []
    for i in range(n_pre):
        c_i = centroids_pre[i]
        if c_i is None:
            continue
        for j in range(i + 1, n_pre):
            c_j = centroids_pre[j]
            if c_j is None:
                continue
            dist = float(1.0 - np.dot(c_i, c_j))
            if dist < 0.50:
                adj[i].append(j)
                adj[j].append(i)
                tier1_edges.append((people_pre[i].id, people_pre[j].id, dist))

    # 4. Connected components
    visited = set()
    components = []
    for i in range(n_pre):
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
            components.append(comp)

    assert len(components) == 189, f"Expected 189 components, got {len(components)}"

    # 5. Build merged clusters data
    merged_clusters_data = []
    for comp in components:
        all_faces = []
        all_photo_ids = []
        pre_ids = [people_pre[idx].id for idx in comp]
        for idx in comp:
            all_faces.extend(people_pre[idx].faces)
            for pid in people_pre[idx].photo_ids:
                if pid not in all_photo_ids:
                    all_photo_ids.append(pid)
        merged_clusters_data.append({
            "pre_ids": pre_ids,
            "photo_ids": all_photo_ids,
            "faces": all_faces,
        })

    # Sort same way as engine: len(photo_ids) desc, len(faces) desc
    merged_clusters_data.sort(key=lambda x: (len(x["photo_ids"]), len(x["faces"])), reverse=True)

    # 6. Verify against existing export/people.json
    with open("export/people.json", "r", encoding="utf-8") as f:
        existing_people_data = json.load(f)

    existing_people = existing_people_data["people"]
    assert len(existing_people) == 189, f"Expected 189 people in people.json, got {len(existing_people)}"

    id_map = {}
    for idx, cdata in enumerate(merged_clusters_data):
        final_id = f"p{idx+1:03d}"
        cdata["final_id"] = final_id
        
        # Verify that photo_ids match existing people.json
        exp_person = existing_people[idx]
        assert exp_person["id"] == final_id, f"ID mismatch at index {idx}: {exp_person['id']} vs {final_id}"
        assert set(exp_person["photo_ids"]) == set(cdata["photo_ids"]), (
            f"photo_ids mismatch at {final_id}"
        )
        assert len(exp_person["faces"]) == len(cdata["faces"]), (
            f"faces count mismatch at {final_id}"
        )

        for pre_id in cdata["pre_ids"]:
            id_map[pre_id] = final_id

    assert len(id_map) == 242, f"Expected 242 entries in id_map, got {len(id_map)}"

    print(f"Verified all 189 clusters and mapped all 242 pre-merge IDs successfully!")
    print(f"p001 was merged from: {merged_clusters_data[0]['pre_ids']}")

    # 7. Update existing_people_data with merged_from and merged_from_numbering
    for idx, cdata in enumerate(merged_clusters_data):
        exp_person = existing_people[idx]
        exp_person["merged_from"] = cdata["pre_ids"]
        exp_person["merged_from_numbering"] = "pre-merge 242"

    with open("export/people.json", "w", encoding="utf-8") as f:
        json.dump(existing_people_data, f, indent=2)
    print("Updated export/people.json with merged_from and merged_from_numbering!")

    # Write id_map.json to root and export/
    id_map_payload = {
        "_metadata": {
            "description": "Mapping from pre-merge 242 cluster IDs to final 189 cluster IDs",
            "source_numbering": "pre-merge 242",
            "target_numbering": "final 189",
            "total_pre_merge_clusters": 242,
            "total_final_clusters": 189
        },
        "id_map": id_map
    }
    # Also write a direct flat map version or dict with id_map
    with open("id_map.json", "w", encoding="utf-8") as f:
        json.dump(id_map_payload, f, indent=2)
    with open("export/id_map.json", "w", encoding="utf-8") as f:
        json.dump(id_map_payload, f, indent=2)
    with open("export/.cache/id_map.json", "w", encoding="utf-8") as f:
        json.dump(id_map_payload, f, indent=2)
    print("Wrote id_map.json to root, export/, and export/.cache/!")

    # Detail p001 split pairs
    print("\n--- Detailed breakdown for p001 additions ---")
    p001_comp = merged_clusters_data[0]
    base_p001 = pre_by_id["p001"]
    print(f"Pre-merge p001 photo count: {len(base_p001.photo_ids)}, face count: {len(base_p001.faces)}")
    added_pre_ids = [pid for pid in p001_comp["pre_ids"] if pid != "p001"]
    total_added_photos = 0
    total_added_faces = 0
    for pid in added_pre_ids:
        p = pre_by_id[pid]
        p_photos = p.photo_ids
        p_faces = p.faces
        total_added_photos += len(p_photos)
        total_added_faces += len(p_faces)
        print(f"\nCluster {pid} (pre-merge 242): {len(p_photos)} photos, {len(p_faces)} faces")
        for f in p_faces:
            print(f"  photo_id: {f.photo_id} | filename: {records[f.photo_id].file_name} | face_id: {f.face_id} | score: {f.det_score:.4f} | bbox: {[round(x, 1) for x in f.bbox]}")

    print(f"\nTotal photos added to p001: {total_added_photos} (62 + {total_added_photos} = {len(base_p001.photo_ids) + total_added_photos})")
    print(f"Total faces added to p001: {total_added_faces} (62 + {total_added_faces} = {len(base_p001.faces) + total_added_faces})")

if __name__ == "__main__":
    main()
