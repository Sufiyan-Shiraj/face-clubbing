"""Application state manager for PhotoSorter FastAPI layer (SPEC 6.3, BUILD_PLAN Phase 3).

Guarantees:
- Cluster IDs (pNNN) are strictly transient display handles converted to anchor face IDs.
- edits.json contains zero cluster IDs (enforced by regex check).
- Undo restores the previous state for every edit type.
- Suggestions include maybe groups, ranked possibly the same pairs (extended to 0.75 for single-photo people), and ambiguous candidates.
"""

from __future__ import annotations
import copy
import json
import re
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from backend.engine.models import EngineResult, PersonCluster, UnrecognizedGroup, PhotoRecord, FaceDetection
from backend.engine.clusterer import FaceClusterer
from backend.engine.edits import apply_edits, find_face_by_id
from backend.engine.exporter import BundleExporter
from backend.engine.cache import EmbeddingCache
from backend.engine.pipeline import EngineConfig, run_pipeline
from backend.api.models import (
    SettingsModel,
    PersonClusterResponse,
    UnrecognizedResponse,
    UnrecognizedFaceResponse,
    FaceItem,
    RankedPairSuggestion,
    AmbiguousFaceSuggestion,
    AmbiguousCandidate,
    SuggestionsResponse,
)


class AppState:
    def __init__(self, work_dir: Optional[Path] = None):
        self.repo_root = Path(__file__).resolve().parent.parent.parent
        self.work_dir = Path(work_dir) if work_dir else self.repo_root / "export.work"
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.edits_path = self.work_dir / "edits.json"

        self.settings = SettingsModel(
            input_path=str(self.repo_root / "test_photos") if (self.repo_root / "test_photos").exists() else None,
            output_dir=str(self.repo_root / "export"),
            cache_dir=str(self.work_dir),
        )

        # In-memory runtime dataset
        self.photos: Dict[str, PhotoRecord] = {}
        self.people: List[PersonCluster] = []
        self.unrecognized: UnrecognizedGroup = UnrecognizedGroup(photo_ids=[], faces=[])
        self.id_map: Dict[str, str] = {}
        self.maybe_groups: List[Dict[str, Any]] = []
        self.ambiguous_faces_raw: List[Dict[str, Any]] = []

        # Baseline clustering state (before organizer edits, used for clean replay & undo)
        self.base_people: List[PersonCluster] = []
        self.base_unrecognized: UnrecognizedGroup = UnrecognizedGroup(photo_ids=[], faces=[])

        # Edit log
        self.edits_list: List[Dict[str, Any]] = []
        self._load_edits_from_disk()

        # Try to load existing dataset from export if available
        self._try_load_existing_dataset()

    def _try_load_existing_dataset(self):
        """Attempts to load existing Phase 1/1b export data if present."""
        export_people = Path(self.settings.output_dir) / "people.json"
        if not export_people.exists():
            export_people = self.repo_root / "export" / "people.json"

        if export_people.exists():
            try:
                with open(export_people, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 1. Attempt to load full photo records and real embeddings from cache.
                # Must load ONLY from export/ plus export.work/.cache for current run (no stale archives/export_old/.cache).
                cache_candidates = []
                if self.settings.cache_dir:
                    c_p = Path(self.settings.cache_dir)
                    if (c_p / ".cache").exists():
                        cache_candidates.append(c_p / ".cache")
                    if c_p.exists():
                        cache_candidates.append(c_p)
                if (self.work_dir / ".cache").exists():
                    cache_candidates.append(self.work_dir / ".cache")
                if self.work_dir.exists():
                    cache_candidates.append(self.work_dir)
                export_work = self.repo_root / "export.work"
                if (export_work / ".cache").exists():
                    cache_candidates.append(export_work / ".cache")
                if export_work.exists():
                    cache_candidates.append(export_work)

                cached_photos = {}
                for c_dir in cache_candidates:
                    if c_dir.exists():
                        cache = EmbeddingCache(c_dir)
                        loaded = cache.load_all()
                        if len(loaded) > len(cached_photos):
                            cached_photos = loaded

                # Build lookup map of all cached faces by face_id
                face_lookup: Dict[str, FaceDetection] = {}
                for p_rec in cached_photos.values():
                    for f in p_rec.faces:
                        face_lookup[f.face_id] = f

                # Reconstruct photos
                self.photos = cached_photos if cached_photos else {}
                for pid, pinfo in data.get("photos", {}).items():
                    if pid not in self.photos:
                        self.photos[pid] = PhotoRecord(
                            photo_id=pid,
                            original_path=pinfo.get("thumb", ""),
                            file_name=pinfo.get("name", f"{pid}.jpg"),
                            width=pinfo.get("width", 1000),
                            height=pinfo.get("height", 1000),
                            download_url=pinfo.get("download"),
                            faces=[],
                        )

                # Reconstruct people with real face embeddings (refuse to fabricate fake FaceDetection)
                self.people = []
                for pdict in data.get("people", []):
                    faces = []
                    for fdict in pdict.get("faces", []):
                        fid = fdict.get("face_id", f"f_{fdict.get('photo_id')}_001")
                        if fid not in face_lookup:
                            raise RuntimeError(
                                f"Missing embedding cache for face '{fid}' in photo '{fdict.get('photo_id')}'. "
                                f"State must load embeddings for every face in people.json; fabricating fake FaceDetection is forbidden."
                            )
                        f_obj = face_lookup[fid]
                        if f_obj.embedding is None:
                            raise RuntimeError(
                                f"Face '{fid}' in photo '{fdict.get('photo_id')}' has embedding None in cache."
                            )
                        f_obj.cluster_id = pdict["id"]
                        faces.append(f_obj)

                    p_cluster = PersonCluster(
                        id=pdict["id"],
                        photo_ids=pdict.get("photos") or pdict.get("photo_ids", []),
                        faces=faces,
                        label=pdict.get("label"),
                        face_path=pdict.get("face", f"faces/{pdict['id']}.jpg"),
                        merged_from=pdict.get("merged_from", []),
                        merged_from_numbering="",
                    )
                    self.people.append(p_cluster)

                # Reconstruct unrecognized with face objects (refuse to fabricate fake FaceDetection)
                unrec_dict = data.get("unrecognized", {})
                self.unrecognized = UnrecognizedGroup(
                    photo_ids=unrec_dict.get("photo_ids", []),
                    faces=unrec_dict.get("faces", []),
                )
                self.unrecognized._face_items = []
                for f_entry in unrec_dict.get("faces", []):
                    fid = f_entry.get("face_id")
                    if not fid or fid not in face_lookup:
                        raise RuntimeError(
                            f"Missing embedding cache for unrecognized face '{fid}' in photo '{f_entry.get('photo_id')}'. "
                            f"State must load embeddings for every face in people.json; fabricating fake FaceDetection is forbidden."
                        )
                    f_real = face_lookup[fid]
                    if f_real.embedding is None:
                        raise RuntimeError(
                            f"Unrecognized face '{fid}' in photo '{f_entry.get('photo_id')}' has embedding None in cache."
                        )
                    f_real.rejection_reason = f_entry.get("rejection_reason", "unattached")
                    self.unrecognized._face_items.append({
                        "face_obj": f_real,
                        "photo_id": f_entry.get("photo_id", ""),
                        "face": f_entry.get("face", f"faces/{fid}.jpg"),
                        "rejection_reason": f_entry.get("rejection_reason", "unattached"),
                    })

                # Assert invariant: no face in state has embedding None
                for p in self.people:
                    for f in p.faces:
                        if f.embedding is None:
                            raise RuntimeError(f"Invariant violation: face '{f.face_id}' in person '{p.id}' has embedding None.")
                for item in self.unrecognized._face_items:
                    f_obj = item.get("face_obj")
                    if f_obj is None or f_obj.embedding is None:
                        raise RuntimeError(f"Invariant violation: unrecognized face has None embedding.")

                self.base_people = copy.deepcopy(self.people)
                self.base_unrecognized = copy.deepcopy(self.unrecognized)
                self.initial_people = copy.deepcopy(self.people)
                self.initial_unrecognized = copy.deepcopy(self.unrecognized)

                # Load suggestions if present in work dir
                sug_path = self.work_dir / "suggestions.json"
                if sug_path.exists():
                    with open(sug_path, "r", encoding="utf-8") as f:
                        sug_data = json.load(f)
                    self.maybe_groups = sug_data.get("maybe_groups", [])
                    self.ambiguous_faces_raw = sug_data.get("ambiguous_faces", [])
                self.initial_maybe_groups = copy.deepcopy(self.maybe_groups)
                self.initial_ambiguous_faces_raw = copy.deepcopy(self.ambiguous_faces_raw)
            except RuntimeError:
                raise
            except Exception as e:
                import traceback
                print("DATASET LOAD ERROR:", e)
                traceback.print_exc()
                raise

    def _load_edits_from_disk(self):
        if self.edits_path.exists():
            try:
                with open(self.edits_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.edits_list = data.get("edits", [])
            except Exception:
                self.edits_list = []
        else:
            self.edits_list = []

    def _save_edits_to_disk(self):
        """Saves edits.json and asserts no cluster IDs (\\bp\\d{3}\\b) are ever persisted."""
        payload = {
            "version": 1,
            "updated_at": datetime.datetime.now().astimezone().isoformat(),
            "edits": self.edits_list,
        }
        json_text = json.dumps(payload, indent=2)

        # STRICT ASSERTION: Never store or key anything by cluster ID
        cluster_id_match = re.search(r'\bp\d{3}\b', json_text)
        if cluster_id_match:
            raise ValueError(
                f"Working Rule Violation: Cluster ID '{cluster_id_match.group(0)}' detected in edits.json! "
                f"Edits must be strictly keyed by face IDs and photo IDs."
            )

        with open(self.edits_path, "w", encoding="utf-8") as f:
            f.write(json_text)

    def set_result(self, result: EngineResult, work_dir: Optional[Path] = None):
        """Sets engine execution result into active state."""
        if work_dir:
            self.work_dir = Path(work_dir)
            self.edits_path = self.work_dir / "edits.json"

        self.photos = result.photos
        self.people = result.people
        self.unrecognized = result.unrecognized
        self.id_map = result.id_map

        # Snapshot base unedited state
        self.base_people = copy.deepcopy(result.people)
        self.base_unrecognized = copy.deepcopy(result.unrecognized)

        # Load suggestions if saved
        sug_path = self.work_dir / "suggestions.json"
        if sug_path.exists():
            with open(sug_path, "r", encoding="utf-8") as f:
                sug_data = json.load(f)
            self.maybe_groups = sug_data.get("maybe_groups", [])
            self.ambiguous_faces_raw = sug_data.get("ambiguous_faces", [])

    def set_work_dir(self, work_dir: Path | str):
        """Switches working directory for edits and suggestions, isolating test runs."""
        self.work_dir = Path(work_dir).resolve()
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.edits_path = self.work_dir / "edits.json"
        self._load_edits_from_disk()
        source_people = getattr(self, "initial_people", None) or self.base_people
        source_unrec = getattr(self, "initial_unrecognized", None) or self.base_unrecognized
        if source_people:
            self.people = copy.deepcopy(source_people)
            self.unrecognized = copy.deepcopy(source_unrec)
            self.base_people = copy.deepcopy(source_people)
            self.base_unrecognized = copy.deepcopy(source_unrec)
            self.settings.distance_threshold = 0.50
            if hasattr(self, "initial_maybe_groups"):
                self.maybe_groups = copy.deepcopy(self.initial_maybe_groups)
            if hasattr(self, "initial_ambiguous_faces_raw"):
                self.ambiguous_faces_raw = copy.deepcopy(self.initial_ambiguous_faces_raw)
            if self.edits_list:
                people_replayed, unrec_replayed, _, _ = apply_edits(
                    copy.deepcopy(self.base_people),
                    copy.deepcopy(self.base_unrecognized),
                    {"version": 1, "edits": self.edits_list},
                    self.photos,
                )
                self.people = people_replayed
                self.unrecognized = unrec_replayed

    def get_cluster_by_id(self, cluster_id: str) -> Optional[PersonCluster]:
        for p in self.people:
            if p.id == cluster_id:
                return p
        return None

    def get_anchor_faces_for_cluster(self, cluster: PersonCluster) -> List[str]:
        """Returns stable face ID anchors for a cluster (all detected face IDs)."""
        fids = [f.face_id for f in cluster.faces if f.face_id]
        if not fids:
            # Fallback to rep_face or cluster photo if synthetic
            fids = [f"f_{cluster.id}_anchor"]
        return fids

    def resolve_person_handle_to_anchors(self, person_handle: str) -> List[str]:
        """Resolves a UI cluster ID (e.g. p001) to anchor face IDs."""
        cluster = self.get_cluster_by_id(person_handle)
        if cluster:
            return self.get_anchor_faces_for_cluster(cluster)
        raise ValueError(f"Cluster handle '{person_handle}' not found in current dataset")

    def apply_edit_operation(self, req: Dict[str, Any]) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Processes an edit request from the UI or API:
        Converts any transient cluster ID handles to anchor face IDs,
        records in edits_list, saves to edits.json, and replays edits.
        """
        op = req.get("op")

        if op == "undo":
            if not self.edits_list:
                return False, "No edits to undo", []
            popped = self.edits_list.pop()
            self._save_edits_to_disk()
            # Replay remaining edits on base clustering result
            people_replayed, unrec_replayed, unapplied, _ = apply_edits(
                copy.deepcopy(self.base_people),
                copy.deepcopy(self.base_unrecognized),
                {"version": 1, "edits": self.edits_list},
                self.photos,
            )
            self.people = people_replayed
            self.unrecognized = unrec_replayed
            return True, f"Undid edit '{popped.get('op')}'", unapplied

        stored_edit: Dict[str, Any] = {"op": op}

        if op == "merge":
            # Can accept person_ids: ["p001", "p002", "p003"] or raw anchors
            if "person_ids" in req and req["person_ids"]:
                anchors_groups = []
                for pid in req["person_ids"]:
                    anchors_groups.append(self.resolve_person_handle_to_anchors(pid))
                stored_edit["anchors"] = anchors_groups
            elif "anchors" in req and req["anchors"]:
                stored_edit["anchors"] = req["anchors"]
            else:
                return False, "Merge requires 'person_ids' or 'anchors'", []

        elif op == "remove":
            # Remove face from person
            if "person_id" in req and req["person_id"]:
                stored_edit["person"] = self.resolve_person_handle_to_anchors(req["person_id"])
            elif "person" in req and req["person"]:
                stored_edit["person"] = req["person"]
            else:
                return False, "Remove requires 'person_id' or 'person' anchors", []

            if not req.get("face_id"):
                return False, "Remove requires 'face_id'", []
            stored_edit["face_id"] = req["face_id"]

        elif op == "assign":
            # Assign unrecognized face to person or create new person
            if not req.get("face_id"):
                return False, "Assign requires 'face_id'", []
            fid = req["face_id"]
            face_obj, _, _ = find_face_by_id(fid, self.people, self.unrecognized, self.photos)
            stored_edit["face_id"] = face_obj.face_id if face_obj else fid

            if req.get("person_id"):
                stored_edit["person"] = self.resolve_person_handle_to_anchors(req["person_id"])
            elif req.get("person"):
                stored_edit["person"] = req["person"]
            else:
                stored_edit["person"] = None  # creates new person

        elif op == "hide":
            if "person_id" in req and req["person_id"]:
                stored_edit["person"] = self.resolve_person_handle_to_anchors(req["person_id"])
            elif "person" in req and req["person"]:
                stored_edit["person"] = req["person"]
            else:
                return False, "Hide requires 'person_id' or 'person' anchors", []

        elif op == "name":
            if "person_id" in req and req["person_id"]:
                stored_edit["person"] = self.resolve_person_handle_to_anchors(req["person_id"])
            elif "person" in req and req["person"]:
                stored_edit["person"] = req["person"]
            else:
                return False, "Name requires 'person_id' or 'person' anchors", []

            if "label" not in req:
                return False, "Name requires 'label'", []
            stored_edit["label"] = req["label"]

        else:
            return False, f"Unknown operation '{op}'", []

        # Append to edits list and persist to disk (asserts no cluster IDs)
        self.edits_list.append(stored_edit)
        self._save_edits_to_disk()

        # Re-apply all edits from base clustering
        people_replayed, unrec_replayed, unapplied, _ = apply_edits(
            copy.deepcopy(self.base_people),
            copy.deepcopy(self.base_unrecognized),
            {"version": 1, "edits": self.edits_list},
            self.photos,
        )
        self.people = people_replayed
        self.unrecognized = unrec_replayed

        return True, f"Applied edit '{op}'", unapplied

    def rerun_pipeline_with_edits(self, settings_override: Optional[SettingsModel] = None) -> Tuple[bool, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Re-runs the engine pipeline with edit replay.
        Returns (success, unapplied_edits, stats).
        """
        if settings_override:
            for k, v in settings_override.model_dump(exclude_unset=True).items():
                if hasattr(self.settings, k):
                    setattr(self.settings, k, v)

        if self.photos and not (settings_override and settings_override.input_path):
            # Fast re-clustering on existing photos without re-scanning disk
            clusterer = FaceClusterer(
                distance_threshold=self.settings.distance_threshold,
                seed_min_face_size=self.settings.seed_min_face_size,
                seed_max_yaw=self.settings.seed_max_yaw,
                seed_min_det_score=self.settings.seed_min_det_score,
                second_pass_merge=self.settings.second_pass_merge,
                merge_threshold=self.settings.merge_threshold,
                maybe_threshold=self.settings.maybe_threshold,
                same_photo_merge_max=self.settings.same_photo_merge_max,
                attach_distance_cap=getattr(self.settings, "attach_distance_cap", 0.45),
            )
            base_people, base_unrec = clusterer.cluster(self.photos)
            self.base_people = copy.deepcopy(base_people)
            self.base_unrecognized = copy.deepcopy(base_unrec)
            self.maybe_groups = clusterer.maybe_groups
            self.ambiguous_faces_raw = clusterer.ambiguous_faces
            self.id_map = clusterer.id_map

            people_replayed, unrec_replayed, unapplied_edits, stats = apply_edits(
                copy.deepcopy(base_people),
                copy.deepcopy(base_unrec),
                {"version": 1, "edits": self.edits_list},
                self.photos,
            )
            self.people = people_replayed
            self.unrecognized = unrec_replayed
            return True, unapplied_edits, stats

        # Otherwise full pipeline run
        config = EngineConfig(
            input_path=self.settings.input_path or str(self.repo_root / "test_photos"),
            output_dir=self.settings.output_dir,
            cache_dir=self.settings.cache_dir,
            distance_threshold=self.settings.distance_threshold,
            min_det_score=self.settings.min_det_score,
            min_face_size=self.settings.min_face_size,
            max_yaw=self.settings.max_yaw,
            seed_min_face_size=self.settings.seed_min_face_size,
            seed_max_yaw=self.settings.seed_max_yaw,
            seed_min_det_score=self.settings.seed_min_det_score,
            max_image_dim=self.settings.max_image_dim,
            thumb_size=self.settings.thumb_size,
            face_crop_size=self.settings.face_crop_size,
            second_pass_merge=self.settings.second_pass_merge,
            merge_threshold=self.settings.merge_threshold,
            maybe_threshold=self.settings.maybe_threshold,
            same_photo_merge_max=self.settings.same_photo_merge_max,
            flip_average=self.settings.flip_average,
            include_maybe=self.settings.include_maybe,
            event_title=self.settings.event_title,
            event_subtitle=self.settings.event_subtitle,
        )

        res = run_pipeline(config)
        self.set_result(res)

        # Check unapplied edits during replay
        unapplied_edits: List[Dict[str, Any]] = []
        if self.edits_list:
            _, _, unapplied_edits, stats = apply_edits(
                copy.deepcopy(self.base_people),
                copy.deepcopy(self.base_unrecognized),
                {"version": 1, "edits": self.edits_list},
                self.photos,
            )
        else:
            stats = {"applied": 0, "failed": 0}

        return True, unapplied_edits, stats

    def export_public_bundle(self, output_dir: Optional[str] = None) -> List[str]:
        """
        Exports the public bundle ONLY:
        config.json, people.json, faces/, thumbs/.
        Guarantees suggestions.json, edits.json, id_map.json, and .cache/ are never exported.
        """
        out_p = Path(output_dir).resolve() if output_dir else Path(self.settings.output_dir).resolve()
        cache_p = Path(self.settings.cache_dir).resolve() if self.settings.cache_dir else self.work_dir

        exporter = BundleExporter(
            output_dir=out_p,
            cache_dir=cache_p,
            thumb_size=self.settings.thumb_size,
            face_crop_size=self.settings.face_crop_size,
        )

        result = EngineResult(
            photos=self.photos,
            people=self.people,
            unrecognized=self.unrecognized,
            distance_threshold=self.settings.distance_threshold,
            id_map=self.id_map,
        )

        exporter.export(
            result=result,
            title=self.settings.event_title,
            subtitle=self.settings.event_subtitle,
            config_override={
                "include_maybe": self.settings.include_maybe,
                "hide_single_photo_default": False,
            },
            include_maybe=self.settings.include_maybe,
        )

        # STRICT PUBLIC BUNDLE HYGIENE VERIFICATION
        forbidden_files = ["suggestions.json", "edits.json", "id_map.json", ".cache"]
        exported_files = []
        for child in out_p.iterdir():
            name = child.name
            if name in forbidden_files:
                child.unlink() if child.is_file() else None
            else:
                exported_files.append(name)

        return sorted(exported_files)

    def get_people_response(self) -> List[PersonClusterResponse]:
        response = []
        for p in self.people:
            fitems = [
                FaceItem(
                    face_id=f.face_id,
                    photo_id=f.photo_id,
                    det_score=f.det_score,
                    bbox=f.bbox,
                    file_name=self.photos.get(f.photo_id).file_name if f.photo_id in self.photos else None,
                )
                for f in p.faces if f.face_id
            ]
            response.append(
                PersonClusterResponse(
                    id=p.id,
                    label=p.label,
                    face=p.face_path or f"faces/{p.id}.jpg",
                    photo_ids=p.photo_ids,
                    photos=p.photo_ids,
                    photo_count=len(p.photo_ids),
                    faces=fitems,
                    anchor_face_ids=self.get_anchor_faces_for_cluster(p),
                )
            )
        return response

    def get_unrecognized_response(self) -> UnrecognizedResponse:
        face_photo_ids = {f.get("photo_id") for f in self.unrecognized.faces if isinstance(f, dict)}
        no_face_photos = [pid for pid in self.unrecognized.photo_ids if pid not in face_photo_ids]

        internal_items = getattr(self.unrecognized, "_face_items", [])
        faces_resp = []
        for i, f in enumerate(self.unrecognized.faces):
            if isinstance(f, dict):
                fid = f.get("face_id")
                if not fid and i < len(internal_items):
                    f_obj = internal_items[i].get("face_obj")
                    if f_obj and f_obj.face_id:
                        fid = f_obj.face_id
                if not fid and f.get("face"):
                    # Extract face_id from face path
                    fid = Path(f["face"]).stem
                faces_resp.append(
                    UnrecognizedFaceResponse(
                        face_id=fid,
                        photo_id=f.get("photo_id", ""),
                        face=f.get("face", ""),
                        rejection_reason=f.get("rejection_reason", "unattached"),
                        det_score=f.get("det_score"),
                        file_name=self.photos.get(f.get("photo_id")).file_name if f.get("photo_id") in self.photos else None,
                    )
                )

        return UnrecognizedResponse(
            total_unrecognized_photos=len(self.unrecognized.photo_ids),
            no_face_photos=no_face_photos,
            faces=faces_resp,
        )

    def get_suggestions_response(self) -> SuggestionsResponse:
        """
        Builds suggestions response per SPEC 6.5 & BUILD_PLAN Phase 3:
        1. maybe_groups from clustering
        2. ranked possibly_the_same list (including extended range up to 0.75 for single-photo people)
        3. top-3 candidates for ambiguous faces
        """
        # 1. Compute top-5 centroids for all current people
        centroids: Dict[str, np.ndarray] = {}
        for p in self.people:
            good_faces = [f for f in p.faces if getattr(f, "is_good_quality", True) and f.embedding is not None]
            if not good_faces:
                good_faces = [f for f in p.faces if f.embedding is not None]
            if good_faces:
                good_faces.sort(key=lambda f: (f.det_score or 0.0, (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]) if f.bbox else 0.0), reverse=True)
                top_embs = [f.embedding for f in good_faces[:5]]
                c = np.mean(top_embs, axis=0)
                norm = np.linalg.norm(c)
                if norm > 1e-6:
                    c = c / norm
                centroids[p.id] = c

        ranked_pairs: List[RankedPairSuggestion] = []
        n_people = len(self.people)

        for i in range(n_people):
            p_a = self.people[i]
            c_a = centroids.get(p_a.id)
            if c_a is None:
                continue

            for j in range(i + 1, n_people):
                p_b = self.people[j]
                c_b = centroids.get(p_b.id)
                if c_b is None:
                    continue

                dist = float(1.0 - np.dot(c_a, c_b))
                is_single_a = len(p_a.photo_ids) == 1
                is_single_b = len(p_b.photo_ids) == 1
                has_single = is_single_a or is_single_b

                # Standard high-confidence ranked pairs (0.50 <= dist <= 0.59)
                if self.settings.merge_threshold <= dist <= 0.59:
                    bf_a = FaceClusterer.get_cluster_best_face(p_a.faces)[0] if p_a.faces else None
                    bf_b = FaceClusterer.get_cluster_best_face(p_b.faces)[0] if p_b.faces else None

                    ranked_pairs.append(
                        RankedPairSuggestion(
                            person_a_id=p_a.id,
                            person_b_id=p_b.id,
                            person_a_anchors=self.get_anchor_faces_for_cluster(p_a),
                            person_b_anchors=self.get_anchor_faces_for_cluster(p_b),
                            distance=round(dist, 4),
                            confidence="medium",
                            reason="centroid_band",
                            person_a_photos=len(p_a.photo_ids),
                            person_b_photos=len(p_b.photo_ids),
                            person_a_best_face=bf_a,
                            person_b_best_face=bf_b,
                        )
                    )

        # Sort ranked pairs by distance ascending
        ranked_pairs.sort(key=lambda item: item.distance)

        # 3. Top-3 candidates for ambiguous faces
        internal_items = getattr(self.unrecognized, "_face_items", [])
        ambiguous_suggestions: List[AmbiguousFaceSuggestion] = []
        for idx, face_dict in enumerate(self.unrecognized.faces):
            reason = face_dict.get("rejection_reason")
            fid = face_dict.get("face_id")
            f_obj = None
            if idx < len(internal_items):
                f_obj = internal_items[idx].get("face_obj")
                if not fid and f_obj:
                    fid = f_obj.face_id
                if not reason and f_obj:
                    reason = getattr(f_obj, "rejection_reason", None)

            reason = reason or "unattached"
            if reason == "ambiguous":
                if not f_obj and fid:
                    for prec in self.photos.values():
                        for f in prec.faces:
                            if f.face_id == fid:
                                f_obj = f
                                break
                        if f_obj:
                            break

                candidates: List[AmbiguousCandidate] = []
                if f_obj is not None and f_obj.embedding is not None:
                    dist_list = []
                    for p in self.people:
                        c = centroids.get(p.id)
                        if c is not None:
                            d = float(1.0 - np.dot(f_obj.embedding, c))
                            dist_list.append((d, p))
                    dist_list.sort(key=lambda x: x[0])
                    for d_val, cand_p in dist_list[:3]:
                        candidates.append(
                            AmbiguousCandidate(
                                candidate_id=cand_p.id,
                                distance=round(d_val, 4),
                                anchor_face_ids=self.get_anchor_faces_for_cluster(cand_p),
                            )
                        )

                if candidates and candidates[0].distance < 0.49:
                    ambiguous_suggestions.append(
                        AmbiguousFaceSuggestion(
                            face_id=fid or "",
                            photo_id=face_dict.get("photo_id", ""),
                            rejection_reason=reason,
                            top_candidates=candidates,
                        )
                    )

        return SuggestionsResponse(
            maybe_groups_count=len(self.maybe_groups),
            maybe_groups=self.maybe_groups,
            possibly_the_same_count=len(ranked_pairs),
            possibly_the_same=ranked_pairs,
            ambiguous_faces_count=len(ambiguous_suggestions),
            ambiguous_faces=ambiguous_suggestions,
        )
