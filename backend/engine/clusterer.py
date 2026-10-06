"""Face clustering using Agglomerative Clustering and Second-Pass Centroid Merging."""

from __future__ import annotations
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import numpy as np

from backend.engine.models import (
    FaceDetection,
    PhotoRecord,
    PersonCluster,
    UnrecognizedGroup,
)


class FaceClusterer:
    """
    Clusters facial embeddings with:
    1. Seed clustering (size >= 64px, |yaw| <= 60°, det_score >= 0.70)
    2. Strict attach-only for non-seed faces (margin >= 0.05, dist < 0.45, no same-photo attachment)
    3. Second-pass cluster merge using top-5 centroids:
       - under 0.50: auto-merge (same-photo collisions tracked as diagnostic only)
       - 0.50 to 0.60: maybe link (connected groups formed, organizer-only suggestions)
       - over 0.60: nothing
    """

    def __init__(
        self,
        distance_threshold: float = 0.50,
        seed_min_face_size: int = 64,
        seed_max_yaw: float = 60.0,
        seed_min_det_score: float = 0.70,
        second_pass_merge: bool = True,
        merge_threshold: float = 0.50,
        maybe_threshold: float = 0.60,
        same_photo_merge_max: float = 0.40,
    ):
        self.distance_threshold = distance_threshold
        self.seed_min_face_size = seed_min_face_size
        self.seed_max_yaw = seed_max_yaw
        self.seed_min_det_score = seed_min_det_score
        self.second_pass_merge = second_pass_merge
        self.merge_threshold = merge_threshold
        self.maybe_threshold = maybe_threshold
        self.same_photo_merge_max = same_photo_merge_max
        self.stats: Dict[str, Any] = {}
        self.maybe_groups: List[Dict[str, Any]] = []
        self.ambiguous_faces: List[Dict[str, Any]] = []

    @staticmethod
    def compute_cluster_centroid(faces: List[FaceDetection], top_k: int = 5) -> Optional[np.ndarray]:
        """
        Computes a normalized centroid embedding from the top-k best faces only
        (ranked by highest det_score and face size).
        """
        scored_faces = []
        for f in faces:
            if f.embedding is None:
                continue
            w = f.bbox[2] - f.bbox[0]
            h = f.bbox[3] - f.bbox[1]
            dim = min(w, h)
            scored_faces.append((float(f.det_score), dim, f.embedding))

        # Sort descending by det_score, then face dimension
        scored_faces.sort(key=lambda x: (x[0], x[1]), reverse=True)
        top_faces = scored_faces[:top_k]
        if not top_faces:
            return None

        embs = np.stack([x[2] for x in top_faces])
        mean_v = np.mean(embs, axis=0)
        norm = np.linalg.norm(mean_v)
        if norm > 1e-8:
            mean_v = mean_v / norm
        return mean_v

    @staticmethod
    def get_cluster_best_face(faces: List[FaceDetection]) -> Tuple[str, float]:
        """
        Returns (best_face_id, best_det_score) for a cluster, ranked by det_score desc, min(w,h) desc.
        """
        scored = []
        for f in faces:
            w = f.bbox[2] - f.bbox[0]
            h = f.bbox[3] - f.bbox[1]
            scored.append((float(f.det_score), min(w, h), f.face_id))
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        if scored:
            return scored[0][2], scored[0][0]
        return "", 0.0

    def cluster(
        self,
        photos: Dict[str, PhotoRecord],
    ) -> Tuple[List[PersonCluster], UnrecognizedGroup]:
        """
        Runs seed + attach clustering followed by second-pass centroid merge.

        Returns:
            people: List of PersonCluster (sorted by photo count descending)
            unrecognized: UnrecognizedGroup with unattached faces and face-less photos
        """
        # 1. Partition all detected faces into seed faces and non-seed faces
        seeds: List[FaceDetection] = []
        non_seeds: List[Tuple[FaceDetection, str]] = []  # (face, fallback_reason)
        photos_with_no_faces: List[str] = []

        for photo_id, record in photos.items():
            if not record.faces:
                photos_with_no_faces.append(photo_id)
            else:
                for face in record.faces:
                    if face.embedding is None:
                        continue
                    w = face.bbox[2] - face.bbox[0]
                    h = face.bbox[3] - face.bbox[1]
                    face_dim = min(w, h)
                    yaw = abs(face.pose[1]) if face.pose and len(face.pose) >= 2 else 0.0
                    score = face.det_score

                    is_seed = (
                        face_dim >= self.seed_min_face_size
                        and yaw <= self.seed_max_yaw
                        and score >= self.seed_min_det_score
                    )

                    if is_seed:
                        seeds.append(face)
                    else:
                        if face_dim < self.seed_min_face_size:
                            reason = "unattached_small"
                        elif yaw > self.seed_max_yaw:
                            reason = "unattached_profile"
                        else:
                            reason = "unattached_lowscore"
                        non_seeds.append((face, reason))

        # 2. Cluster seed faces with AgglomerativeClustering
        cluster_map: Dict[int, List[FaceDetection]] = defaultdict(list)

        if len(seeds) == 0:
            pass
        elif len(seeds) == 1:
            cluster_map[0].append(seeds[0])
        else:
            X = np.stack([f.embedding for f in seeds])
            norms = np.linalg.norm(X, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            X = X / norms

            from sklearn.cluster import AgglomerativeClustering

            try:
                model = AgglomerativeClustering(
                    metric="cosine",
                    linkage="average",
                    distance_threshold=self.distance_threshold,
                    n_clusters=None,
                )
            except TypeError:
                model = AgglomerativeClustering(
                    affinity="cosine",
                    linkage="average",
                    distance_threshold=self.distance_threshold,
                    n_clusters=None,
                )

            labels = model.fit_predict(X)
            for idx, label in enumerate(labels):
                cluster_map[int(label)].append(seeds[idx])

        # 3. Attach non-seed faces to existing clusters (Strict Attach-Only)
        cluster_seed_embs = {
            cid: np.stack([f.embedding for f in members])
            for cid, members in cluster_map.items()
        }
        # Dynamically track photo_ids per cluster as faces attach to prevent same-photo collisions
        cluster_photo_ids = {
            cid: set(f.photo_id for f in members)
            for cid, members in cluster_map.items()
        }

        unattached_faces: List[FaceDetection] = []
        attached_count = 0
        unattached_by_reason: Dict[str, int] = defaultdict(int)

        for face, reason in non_seeds:
            dists = []
            for cid, embs in cluster_seed_embs.items():
                dots = np.dot(embs, face.embedding)
                avg_dist = float(1.0 - np.mean(dots))
                dists.append((avg_dist, cid))

            dists.sort(key=lambda x: x[0])
            d1, c1 = dists[0] if len(dists) > 0 else (float("inf"), None)
            d2, c2 = dists[1] if len(dists) > 1 else (float("inf"), None)

            # Strict Attach Rules:
            # a. Never attach to a cluster that already contains a face from the same photo.
            # b. Attach only if the best cluster distance is < 0.45 AND second-best is at least 0.05 farther.
            can_attach = (
                c1 is not None
                and d1 < 0.45
                and (d2 - d1 >= 0.05)
                and (face.photo_id not in cluster_photo_ids[c1])
            )

            if can_attach and c1 is not None:
                # Face attaches to existing cluster
                face.is_good_quality = True
                face.rejection_reason = None
                cluster_map[c1].append(face)
                cluster_photo_ids[c1].add(face.photo_id)
                attached_count += 1
            else:
                # Face cannot attach -> goes to Unrecognized
                face.is_good_quality = False
                if d1 < self.distance_threshold:
                    final_reason = "ambiguous"
                else:
                    final_reason = reason
                face.rejection_reason = final_reason
                unattached_faces.append(face)
                unattached_by_reason[final_reason] += 1

        # 4. Build initial clusters before merge
        initial_clusters = []
        for _, faces in cluster_map.items():
            photo_ids = list(dict.fromkeys(f.photo_id for f in faces))
            initial_clusters.append({
                "photo_ids": photo_ids,
                "faces": faces,
            })

        # Sort: most photos first; tiebreaker: most faces
        initial_clusters.sort(key=lambda item: (len(item["photo_ids"]), len(item["faces"])), reverse=True)

        clusters_before_count = len(initial_clusters)
        singletons_before_count = sum(1 for c in initial_clusters if len(c["photo_ids"]) == 1)

        # 5. Second-pass cluster merge (if enabled)
        if self.second_pass_merge and len(initial_clusters) > 1:
            # 5a. Compute centroids for initial clusters from top-5 faces
            initial_centroids = [
                self.compute_cluster_centroid(c["faces"], top_k=5)
                for c in initial_clusters
            ]

            # 5b. Tier 1: Auto-merge graph (cosine distance < merge_threshold, default 0.50)
            # Subject to same_photo_merge_max rule: blocked if merged cluster would contain
            # two faces from the same photo with cosine distance > same_photo_merge_max (0.40)
            n_init = len(initial_clusters)
            merge_adj = defaultdict(list)
            blocked_initial_pairs = []

            for i in range(n_init):
                c_i = initial_centroids[i]
                if c_i is None:
                    continue
                for j in range(i + 1, n_init):
                    c_j = initial_centroids[j]
                    if c_j is None:
                        continue
                    dist = float(1.0 - np.dot(c_i, c_j))
                    if dist < self.merge_threshold:
                        pids_i = {f.photo_id: [] for f in initial_clusters[i]["faces"]}
                        for f in initial_clusters[i]["faces"]:
                            pids_i[f.photo_id].append(f)
                        pids_j = {f.photo_id: [] for f in initial_clusters[j]["faces"]}
                        for f in initial_clusters[j]["faces"]:
                            pids_j[f.photo_id].append(f)

                        conflict = False
                        common_pids = set(pids_i.keys()) & set(pids_j.keys())
                        for pid in common_pids:
                            for fi in pids_i[pid]:
                                for fj in pids_j[pid]:
                                    sp_d = float(1.0 - np.dot(fi.embedding, fj.embedding))
                                    if sp_d > self.same_photo_merge_max:
                                        conflict = True
                                        break
                                if conflict:
                                    break
                            if conflict:
                                break

                        if conflict:
                            blocked_initial_pairs.append((i, j, dist))
                        else:
                            merge_adj[i].append(j)
                            merge_adj[j].append(i)

            # Connected components for auto-merge
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

            # Build merged clusters
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
                    "orig_indices": comp,
                })

            # 5c. Post-merge ambiguous faces re-attach (default pipeline step)
            if len(merged_clusters) > 0 and len(unattached_faces) > 0:
                post_centroids = [
                    self.compute_cluster_centroid(c["faces"], top_k=5)
                    for c in merged_clusters
                ]
                cluster_photo_ids = [set(c["photo_ids"]) for c in merged_clusters]

                remaining_unattached = []
                for face in unattached_faces:
                    if face.rejection_reason == "ambiguous":
                        dists = []
                        for cid, c_emb in enumerate(post_centroids):
                            if c_emb is None:
                                continue
                            d = float(1.0 - np.dot(c_emb, face.embedding))
                            dists.append((d, cid))
                        dists.sort(key=lambda x: x[0])
                        d1, c1 = dists[0] if len(dists) > 0 else (float("inf"), None)
                        d2, c2 = dists[1] if len(dists) > 1 else (float("inf"), None)

                        can_attach = (
                            c1 is not None
                            and d1 < 0.45
                            and (d2 - d1 >= 0.05)
                            and (face.photo_id not in cluster_photo_ids[c1])
                        )
                        if can_attach:
                            face.is_good_quality = True
                            face.rejection_reason = None
                            merged_clusters[c1]["faces"].append(face)
                            if face.photo_id not in merged_clusters[c1]["photo_ids"]:
                                merged_clusters[c1]["photo_ids"].append(face.photo_id)
                            cluster_photo_ids[c1].add(face.photo_id)
                            attached_count += 1
                            unattached_by_reason["ambiguous"] -= 1
                        else:
                            remaining_unattached.append(face)
                    else:
                        remaining_unattached.append(face)
                unattached_faces = remaining_unattached

            # Sort merged clusters: photo count desc, face count desc
            merged_clusters.sort(key=lambda item: (len(item["photo_ids"]), len(item["faces"])), reverse=True)
            init_to_final = {}
            for final_idx, c in enumerate(merged_clusters):
                for orig_idx in c.get("orig_indices", []):
                    init_to_final[orig_idx] = final_idx
        else:
            merged_clusters = initial_clusters
            blocked_initial_pairs = []
            init_to_final = {i: i for i in range(len(initial_clusters))}

        clusters_after_count = len(merged_clusters)
        singletons_after_count = sum(1 for c in merged_clusters if len(c["photo_ids"]) == 1)

        # 6. Build PersonCluster instances and assign IDs
        people: List[PersonCluster] = []
        for idx, cdata in enumerate(merged_clusters):
            person_id = f"p{idx+1:03d}"
            for f in cdata["faces"]:
                f.cluster_id = person_id

            person = PersonCluster(
                id=person_id,
                label=None,
                face_path=f"faces/{person_id}.jpg",
                photo_ids=cdata["photo_ids"],
                faces=cdata["faces"],
                maybe_photos=[],
            )
            people.append(person)

        # 7. Tier 2: Maybe links (0.50 to 0.60) & Connected Groups
        self.maybe_groups = []
        if len(people) > 1:
            merged_centroids = [
                self.compute_cluster_centroid(p.faces, top_k=5)
                for p in people
            ]

            m_clusters = len(people)
            candidate_links = {}

            # First, check blocked auto-merge candidate pairs
            for u_init, v_init, init_d in blocked_initial_pairs:
                fi = init_to_final.get(u_init)
                fj = init_to_final.get(v_init)
                if fi is not None and fj is not None and fi != fj:
                    c_fi = merged_centroids[fi]
                    c_fj = merged_centroids[fj]
                    if c_fi is not None and c_fj is not None:
                        d_final = float(1.0 - np.dot(c_fi, c_fj))
                    else:
                        d_final = init_d
                    if d_final <= self.maybe_threshold:
                        key = (min(fi, fj), max(fi, fj))
                        candidate_links[key] = (d_final, "same_photo_conflict")

            # Next, evaluate all pairs of post-merge clusters
            for i in range(m_clusters):
                c_i = merged_centroids[i]
                if c_i is None:
                    continue
                for j in range(i + 1, m_clusters):
                    c_j = merged_centroids[j]
                    if c_j is None:
                        continue
                    dist = float(1.0 - np.dot(c_i, c_j))
                    if self.merge_threshold <= dist <= self.maybe_threshold:
                        # Check same-photo collision between cluster i and cluster j
                        pids_i = {f.photo_id: [] for f in people[i].faces}
                        for f in people[i].faces:
                            pids_i[f.photo_id].append(f)
                        pids_j = {f.photo_id: [] for f in people[j].faces}
                        for f in people[j].faces:
                            pids_j[f.photo_id].append(f)

                        conflict = False
                        common_pids = set(pids_i.keys()) & set(pids_j.keys())
                        for pid in common_pids:
                            for fi in pids_i[pid]:
                                for fj in pids_j[pid]:
                                    sp_d = float(1.0 - np.dot(fi.embedding, fj.embedding))
                                    if sp_d > self.same_photo_merge_max:
                                        conflict = True
                                        break
                                if conflict:
                                    break
                            if conflict:
                                break

                        reason = "same_photo_conflict" if conflict else "centroid_band"
                        key = (min(i, j), max(i, j))
                        if key not in candidate_links:
                            candidate_links[key] = (dist, reason)

            # Build adjacency graph
            maybe_adj = defaultdict(dict)
            for (u, v), (dist, reason) in candidate_links.items():
                maybe_adj[u][v] = (dist, reason)
                maybe_adj[v][u] = (dist, reason)

            # Find connected components of maybe-links (groups of size >= 2)
            visited_maybe = set()
            maybe_components = []
            for i in range(m_clusters):
                if i not in visited_maybe and len(maybe_adj[i]) > 0:
                    comp = []
                    queue = [i]
                    visited_maybe.add(i)
                    while queue:
                        curr = queue.pop(0)
                        comp.append(curr)
                        for neighbor in maybe_adj[curr]:
                            if neighbor not in visited_maybe:
                                visited_maybe.add(neighbor)
                                queue.append(neighbor)
                    if len(comp) >= 2:
                        maybe_components.append(comp)

            # Sort components by largest cluster photo count
            maybe_components.sort(key=lambda comp: max(len(people[i].photo_ids) for i in comp), reverse=True)

            # Helper for best face
            best_faces = {}
            for p in people:
                best_faces[p.id] = self.get_cluster_best_face(p.faces)

            # Populate maybe_groups and person.maybe_photos
            for g_idx, comp in enumerate(maybe_components):
                group_clusters = [people[i].id for i in comp]
                union_pids = set()
                for i in comp:
                    union_pids.update(people[i].photo_ids)
                total_photos = len(union_pids)
                group_links = []
                for u in comp:
                    for v in comp:
                        if u < v and v in maybe_adj[u]:
                            d_val, reason_str = maybe_adj[u][v]
                            bf_u_id, bf_u_score = best_faces[people[u].id]
                            bf_v_id, bf_v_score = best_faces[people[v].id]
                            group_links.append({
                                "cluster_a": people[u].id,
                                "cluster_b": people[v].id,
                                "distance": round(d_val, 4),
                                "cluster_a_photos": len(people[u].photo_ids),
                                "cluster_b_photos": len(people[v].photo_ids),
                                "cluster_a_best_face": bf_u_id,
                                "cluster_a_best_det_score": round(bf_u_score, 4),
                                "cluster_b_best_face": bf_v_id,
                                "cluster_b_best_det_score": round(bf_v_score, 4),
                                "reason": reason_str,
                            })

                self.maybe_groups.append({
                    "group_id": g_idx + 1,
                    "clusters": group_clusters,
                    "cluster_count": len(group_clusters),
                    "photos_count": total_photos,
                    "links": group_links,
                })

                # Populate maybe_photos for each person in group
                for u in comp:
                    target_person = people[u]
                    existing_photo_ids = set(target_person.photo_ids)
                    maybe_entries = []
                    seen_maybe_pids = set()

                    for v in comp:
                        if u == v:
                            continue
                        source_person = people[v]
                        dist_entry = maybe_adj[u].get(v)
                        if dist_entry is not None:
                            dist_val = dist_entry[0]
                        else:
                            c_u = merged_centroids[u]
                            c_v = merged_centroids[v]
                            if c_u is not None and c_v is not None:
                                dist_val = float(1.0 - np.dot(c_u, c_v))
                            else:
                                dist_val = 0.55

                        for pid in source_person.photo_ids:
                            if pid not in existing_photo_ids and pid not in seen_maybe_pids:
                                seen_maybe_pids.add(pid)
                                maybe_entries.append({
                                    "photo_id": pid,
                                    "source_cluster": source_person.id,
                                    "distance": round(dist_val, 4),
                                })

                    maybe_entries.sort(key=lambda x: x["distance"])
                    target_person.maybe_photos = maybe_entries

        # Ambiguous faces nearest clusters
        self.ambiguous_faces = []
        if len(people) > 0 and len(unattached_faces) > 0:
            for uface in unattached_faces:
                if uface.rejection_reason == "ambiguous":
                    dists = []
                    for p_idx, p in enumerate(people):
                        c_emb = merged_centroids[p_idx]
                        if c_emb is not None:
                            d = float(1.0 - np.dot(c_emb, uface.embedding))
                            dists.append({
                                "cluster_id": p.id,
                                "distance": round(d, 4),
                            })
                    dists.sort(key=lambda x: x["distance"])
                    self.ambiguous_faces.append({
                        "face_id": uface.face_id,
                        "photo_id": uface.photo_id,
                        "top_clusters": dists[:3],
                    })

        # Diagnostic: same-photo collisions in final merged clusters
        colliding_clusters_count, total_extra_faces = self.count_same_photo_collisions(people)

        self.stats = {
            "total_faces": len(seeds) + len(non_seeds),
            "seed_faces": len(seeds),
            "non_seed_faces": len(non_seeds),
            "attached_faces": attached_count,
            "unattached_faces": len(unattached_faces),
            "unattached_breakdown": dict(unattached_by_reason),
            "clusters_before_merge": clusters_before_count,
            "singletons_before_merge": singletons_before_count,
            "clusters_after_merge": clusters_after_count,
            "singletons_after_merge": singletons_after_count,
            "colliding_clusters_diagnostic": colliding_clusters_count,
            "extra_faces_diagnostic": total_extra_faces,
            "maybe_groups_count": len(self.maybe_groups),
            "ambiguous_faces_count": len(self.ambiguous_faces),
        }

        # 8. Build Unrecognized group
        unrec_photo_ids_set = set(photos_with_no_faces)
        unrec_face_items = []

        for idx, uface in enumerate(unattached_faces):
            unrec_photo_ids_set.add(uface.photo_id)
            u_crop_rel = f"faces/u{idx+1:03d}.jpg"
            unrec_face_items.append({
                "photo_id": uface.photo_id,
                "face": u_crop_rel,
                "face_obj": uface,
            })

        unrecognized = UnrecognizedGroup(
            photo_ids=sorted(list(unrec_photo_ids_set)),
            faces=[{"photo_id": item["photo_id"], "face": item["face"]} for item in unrec_face_items],
        )
        unrecognized._face_items = unrec_face_items  # type: ignore

        # 9. Automated invariant verification:
        all_covered_photos = set(unrecognized.photo_ids)
        for person in people:
            all_covered_photos.update(person.photo_ids)

        all_input_photos = set(photos.keys())
        missing = all_input_photos - all_covered_photos
        if missing:
            raise ValueError(
                f"Engine integrity failure: {len(missing)} photos are missing from both "
                f"person clusters and Unrecognized: {missing}"
            )

        return people, unrecognized

    @staticmethod
    def count_same_photo_collisions(people: List[PersonCluster]) -> Tuple[int, int]:
        """
        Diagnostic: counts clusters containing two or more faces from the same photo.

        Returns:
            colliding_clusters_count: number of clusters with >= 2 faces from the same photo
            total_extra_faces: total excess faces from same-photo co-occurrences
        """
        colliding_clusters = 0
        total_extra = 0
        for person in people:
            pids = [f.photo_id for f in person.faces]
            unique_pids = set(pids)
            if len(pids) > len(unique_pids):
                colliding_clusters += 1
                total_extra += (len(pids) - len(unique_pids))
        return colliding_clusters, total_extra
