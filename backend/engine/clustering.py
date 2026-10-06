"""Clustering module: groups face embeddings using Agglomerative Clustering (average linkage, cosine metric)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from .detector import DetectedFace


@dataclass
class PersonCluster:
    """Represents a clustered individual person across photos."""
    person_id: str
    face_ids: list[str] = field(default_factory=list)
    photo_ids: list[str] = field(default_factory=list)
    faces: list[DetectedFace] = field(default_factory=list)
    representative_face: DetectedFace | None = None
    crop_path: str = ""
    label: str | None = None


@dataclass
class UnrecognizedData:
    """Represents faces and photos that could not be reliably clustered."""
    photo_ids: list[str] = field(default_factory=list)
    faces: list[DetectedFace] = field(default_factory=list)
    face_crops: list[dict[str, str]] = field(default_factory=list)


def cluster_faces(
    quality_faces: list[DetectedFace],
    distance_threshold: float = 0.5,
) -> list[list[DetectedFace]]:
    """Clusters quality faces using Agglomerative Clustering with average linkage and cosine distance.
    
    Hard constraints (SPEC section 3 & 6):
    - metric='cosine', linkage='average', distance_threshold=distance_threshold.
    - No noise: every face is assigned to a cluster. A person appearing once forms a cluster of one.
    - Do NOT use DBSCAN.
    
    Args:
        quality_faces: List of DetectedFace objects with non-empty normalized embeddings.
        distance_threshold: Maximum cosine distance threshold for linking faces into the same cluster.
        
    Returns:
        List of clusters, where each cluster is a list of DetectedFace objects.
    """
    if not quality_faces:
        return []

    if len(quality_faces) == 1:
        return [[quality_faces[0]]]

    embeddings = np.array([f.embedding for f in quality_faces], dtype=np.float32)

    # Normalize embeddings to unit length (just in case)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embeddings = embeddings / norms

    # Run AgglomerativeClustering
    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=distance_threshold,
        metric="cosine",
        linkage="average",
    )
    labels = clustering.fit_predict(embeddings)

    # Group faces by cluster label
    clusters_dict: dict[int, list[DetectedFace]] = {}
    for face, label in zip(quality_faces, labels):
        clusters_dict.setdefault(label, []).append(face)

    # Sort clusters by number of photos descending, then number of faces
    sorted_clusters = list(clusters_dict.values())
    sorted_clusters.sort(
        key=lambda cluster: (len(set(f.photo_id for f in cluster)), len(cluster)),
        reverse=True,
    )

    return sorted_clusters
