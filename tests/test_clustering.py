"""Unit tests for the clustering module."""

import unittest
import numpy as np
from backend.engine.clustering import cluster_faces
from backend.engine.detector import DetectedFace


class TestClustering(unittest.TestCase):
    def _create_face(self, face_id: str, photo_id: str, vector: list[float]) -> DetectedFace:
        # Normalize vector
        vec = np.array(vector, dtype=float)
        vec = vec / np.linalg.norm(vec)
        return DetectedFace(
            face_id=face_id,
            photo_id=photo_id,
            bbox=[10.0, 10.0, 50.0, 50.0],
            det_score=0.9,
            kps=[],
            embedding=vec.tolist(),
            is_quality=True,
            quality_reason="",
        )

    def test_empty_faces(self):
        clusters = cluster_faces([])
        self.assertEqual(len(clusters), 0)

    def test_single_face(self):
        v = [1.0] + [0.0] * 511
        face = self._create_face("f1", "p1", v)
        clusters = cluster_faces([face])
        self.assertEqual(len(clusters), 1)
        self.assertEqual(len(clusters[0]), 1)
        self.assertEqual(clusters[0][0].face_id, "f1")

    def test_clustering_separation_and_merging(self):
        # Person A: base vector along axis 0
        v_a1 = [1.0, 0.05] + [0.0] * 510
        v_a2 = [0.98, 0.08] + [0.0] * 510

        # Person B: base vector along axis 1 (orthogonal)
        v_b1 = [0.02, 1.0] + [0.0] * 510
        v_b2 = [0.04, 0.99] + [0.0] * 510

        f_a1 = self._create_face("f_a1", "photo_1", v_a1)
        f_a2 = self._create_face("f_a2", "photo_2", v_a2)
        f_b1 = self._create_face("f_b1", "photo_1", v_b1)
        f_b2 = self._create_face("f_b2", "photo_3", v_b2)

        clusters = cluster_faces([f_a1, f_a2, f_b1, f_b2], distance_threshold=0.4)
        # Should form exactly 2 clusters
        self.assertEqual(len(clusters), 2)

        cluster_face_ids = [set(f.face_id for f in c) for c in clusters]
        self.assertIn({"f_a1", "f_a2"}, cluster_face_ids)
        self.assertIn({"f_b1", "f_b2"}, cluster_face_ids)


if __name__ == "__main__":
    unittest.main()
