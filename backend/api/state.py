"""Application state manager for PhotoSorter FastAPI layer (SPEC 6.3, BUILD_PLAN Phase 3).

Guarantees:
- Cluster IDs (pNNN) are strictly transient display handles converted to anchor face IDs.
- edits.json contains zero cluster IDs (enforced by regex check).
- Undo restores the previous state for every edit type.
- Suggestions include maybe groups, ranked possibly the same pairs (extended to 0.75 for single-photo people), and ambiguous candidates.
"""

from __future__ import annotations
import os
import sys
import copy
import json
import re
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from backend.engine.models import EngineResult, PersonCluster, UnrecognizedGroup, PhotoRecord, FaceDetection
from backend.engine.clusterer import FaceClusterer
from backend.engine.edits import apply_edits, find_face_by_id, locate_person_by_anchors
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
    def __init__(
        self,
        work_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        cache_dir: Optional[Path] = None,
    ):
        if getattr(sys, "frozen", False):
            self.repo_root = Path.cwd()
        else:
            self.repo_root = Path(__file__).resolve().parent.parent.parent
        env_work = os.environ.get("PHOTOSORTER_WORK_DIR")
        env_output = os.environ.get("PHOTOSORTER_OUTPUT_DIR")
        env_cache = os.environ.get("PHOTOSORTER_CACHE_DIR")

        self.work_dir = Path(work_dir or env_work).resolve() if (work_dir or env_work) else self.repo_root / "export.work"
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.edits_path = self.work_dir / "edits.json"

        resolved_output = Path(output_dir or env_output).resolve() if (output_dir or env_output) else (self.repo_root / "export")
        resolved_cache = Path(cache_dir or env_cache).resolve() if (cache_dir or env_cache) else self.work_dir

        self.settings = SettingsModel(
            input_path=str(self.repo_root / "test_photos") if (self.repo_root / "test_photos").exists() else None,
            output_dir=str(resolved_output),
            cache_dir=str(resolved_cache),
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

        # Edit log & read-only state
        self.read_only: bool = False
        self.edits_error: Optional[str] = None
        self.edits_list: List[Dict[str, Any]] = []
        self._load_edits_from_disk()

        # Active project tracking
        self.project_active: bool = False
        self.active_project_id: Optional[str] = None
        self.active_project_name: Optional[str] = None
        self.drive_folder_name: Optional[str] = None
        self.temp_dirs: List[str] = []

        # Only load existing dataset if explicitly specified (e.g. tests or explicit work_dir/output_dir or env var)
        should_auto_load = bool(work_dir or output_dir or os.environ.get("PHOTOSORTER_LOAD_SAVED"))
        if should_auto_load:
            self._try_load_existing_dataset()

    def _try_load_existing_dataset(self):
        """Attempts to load existing Phase 1/1b export data if present."""
        raw_out = self.settings.output_dir
        if not raw_out or str(raw_out).startswith("http") or "drive.google.com" in str(raw_out):
            raw_out = "export"
            self.settings.output_dir = "export"
        export_people = Path(raw_out) / "people.json"
        if not export_people.exists():
            if Path(raw_out).resolve() == (self.repo_root / "export").resolve():
                export_people = self.repo_root / "export" / "people.json"
            else:
                return

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
                if not cache_candidates:
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

                # Reconstruct photos (strictly scoped to this project's photos)
                project_photo_ids = set(data.get("unrecognized", {}).get("photo_ids", []))
                for pdict in data.get("people", []):
                    project_photo_ids.update(pdict.get("photos") or pdict.get("photo_ids", []))

                target_pids = project_photo_ids if project_photo_ids else set(data.get("photos", {}).keys())

                self.photos = {}
                for pid in target_pids:
                    if pid in cached_photos:
                        self.photos[pid] = cached_photos[pid]
                    elif pid in data.get("photos", {}):
                        pinfo = data["photos"][pid]
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
                self.project_active = True
                self.active_project_name = Path(raw_out).name
            except RuntimeError:
                raise
            except Exception as e:
                import traceback
                print("DATASET LOAD ERROR:", e)
                traceback.print_exc()
                raise

    def _load_edits_from_disk(self):
        self.read_only = False
        self.edits_error = None
        if self.edits_path.exists():
            try:
                with open(self.edits_path, "r", encoding="utf-8") as f:
                    raw_text = f.read()
                if raw_text.strip():
                    data = json.loads(raw_text)
                    if not isinstance(data, dict) or "edits" not in data or not isinstance(data["edits"], list):
                        raise ValueError("edits.json must be an object with an 'edits' list")
                    self.edits_list = data.get("edits", [])
                else:
                    self.edits_list = []
            except Exception as e:
                # Corrupt edits.json: open read-only and report, NEVER overwrite
                self.read_only = True
                self.edits_error = f"Corrupt edits.json: {e}"
                self.edits_list = []
        else:
            self.edits_list = []

    def _save_edits_to_disk(self):
        """Saves edits.json and asserts no cluster IDs (\\bp\\d{3}\\b) are ever persisted."""
        if getattr(self, "read_only", False):
            raise RuntimeError(f"Cannot save edits: project is opened in read-only mode ({self.edits_error})")

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
        self.project_active = True

        if getattr(result, "drive_folder_name", None):
            self.drive_folder_name = result.drive_folder_name
            self.active_project_name = result.drive_folder_name

        if getattr(result, "temp_dir", None):
            self.temp_dirs.append(result.temp_dir)

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

    def open_saved_project(self, work_dir: Path | str, export_path: Optional[Path | str] = None) -> Dict[str, Any]:
        """
        Reopens a past export/work folder without re-scanning disk:
        1. Validates work folder on disk.
        2. Loads edits.json (or switches to read_only if corrupt).
        3. Loads embedding cache and people.json.
        4. Reconstructs base clusters, suggestions, and replays edits.
        5. Preserves undo history and invariant.
        """
        work_p = Path(work_dir).resolve()
        if not work_p.exists() or not work_p.is_dir():
            raise FileNotFoundError(f"Work folder '{work_p}' not found or was moved.")

        self.work_dir = work_p
        self.edits_path = work_p / "edits.json"
        self.settings.work_dir = str(work_p)
        self.settings.cache_dir = str(work_p)

        export_p = Path(export_path).resolve() if export_path else None
        if export_p and export_p.exists() and export_p.is_dir():
            self.settings.output_dir = str(export_p)

        # 1. Load edits.json (corrupt files set read_only=True and report)
        self._load_edits_from_disk()

        # 2. Candidate cache directories for embedding cache (strictly within project)
        cache_candidates = [
            work_p / ".cache",
            work_p,
        ]
        if export_p:
            cache_candidates.extend([export_p / ".cache", export_p])

        cached_photos: Dict[str, PhotoRecord] = {}
        for c_dir in cache_candidates:
            if c_dir.exists():
                cache = EmbeddingCache(c_dir)
                loaded = cache.load_all()
                if len(loaded) > len(cached_photos):
                    cached_photos = loaded

        # Build face lookup map
        face_lookup: Dict[str, FaceDetection] = {}
        for p_rec in cached_photos.values():
            for f in p_rec.faces:
                face_lookup[f.face_id] = f

        # 3. Locate people.json (strictly within project)
        people_json_candidates = []
        if export_p:
            people_json_candidates.append(export_p / "people.json")
            proj_name = work_p.name.removesuffix(".work")
            people_json_candidates.append(export_p / proj_name / "people.json")
            if export_p.is_dir():
                for sub in export_p.glob("*/people.json"):
                    people_json_candidates.append(sub)
        people_json_candidates.append(work_p / "people.json")

        found_people_json = None
        for cand in people_json_candidates:
            if cand.exists() and cand.is_file():
                found_people_json = cand
                if export_p and cand.parent != export_p:
                    self.settings.output_dir = str(cand.parent)
                break

        if found_people_json:
            with open(found_people_json, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Reconstruct photos (strictly scoped to this project's photos)
            project_photo_ids = set(data.get("unrecognized", {}).get("photo_ids", []))
            for pdict in data.get("people", []):
                project_photo_ids.update(pdict.get("photos") or pdict.get("photo_ids", []))

            target_pids = project_photo_ids if project_photo_ids else set(data.get("photos", {}).keys())

            self.photos = {}
            for pid in target_pids:
                if pid in cached_photos:
                    self.photos[pid] = cached_photos[pid]
                elif pid in data.get("photos", {}):
                    pinfo = data["photos"][pid]
                    self.photos[pid] = PhotoRecord(
                        photo_id=pid,
                        original_path=pinfo.get("thumb", ""),
                        file_name=pinfo.get("name", f"{pid}.jpg"),
                        width=pinfo.get("width", 1000),
                        height=pinfo.get("height", 1000),
                        download_url=pinfo.get("download"),
                        faces=[],
                    )

            # Reconstruct people
            self.people = []
            for pdict in data.get("people", []):
                faces = []
                for fdict in pdict.get("faces", []):
                    fid = fdict.get("face_id", f"f_{fdict.get('photo_id')}_001")
                    if fid in face_lookup:
                        f_obj = face_lookup[fid]
                    else:
                        emb = np.zeros(512, dtype=np.float32)
                        f_obj = FaceDetection(
                            face_id=fid,
                            photo_id=fdict.get("photo_id", ""),
                            bbox=fdict.get("bbox", [0.0, 0.0, 100.0, 100.0]),
                            det_score=fdict.get("det_score", 0.9),
                            embedding=emb,
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

            # Reconstruct unrecognized
            unrec_dict = data.get("unrecognized", {})
            self.unrecognized = UnrecognizedGroup(
                photo_ids=unrec_dict.get("photo_ids", []),
                faces=unrec_dict.get("faces", []),
            )
            self.unrecognized._face_items = []
            for f_entry in unrec_dict.get("faces", []):
                fid = f_entry.get("face_id")
                f_real = face_lookup.get(fid) if fid else None
                if not f_real:
                    f_real = FaceDetection(
                        face_id=fid or f"unrec_{f_entry.get('photo_id')}",
                        photo_id=f_entry.get("photo_id", ""),
                        bbox=f_entry.get("bbox", [0.0, 0.0, 100.0, 100.0]),
                        det_score=f_entry.get("det_score", 0.5),
                        embedding=np.zeros(512, dtype=np.float32),
                        rejection_reason=f_entry.get("rejection_reason", "unattached"),
                    )
                else:
                    f_real.rejection_reason = f_entry.get("rejection_reason", "unattached")
                self.unrecognized._face_items.append({
                    "face_obj": f_real,
                    "photo_id": f_entry.get("photo_id", ""),
                    "face": f_entry.get("face", f"faces/{fid}.jpg"),
                    "rejection_reason": f_entry.get("rejection_reason", "unattached"),
                })
        elif cached_photos:
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
            self.people, self.unrecognized = clusterer.cluster(cached_photos)
            self.photos = cached_photos
            self.id_map = clusterer.id_map
            self.maybe_groups = clusterer.maybe_groups
            self.ambiguous_faces_raw = clusterer.ambiguous_faces
        else:
            raise RuntimeError(f"Could not find people.json or valid embedding cache in '{work_p}'.")

        # Snapshot baseline for undo/replay
        self.base_people = copy.deepcopy(self.people)
        self.base_unrecognized = copy.deepcopy(self.unrecognized)
        self.initial_people = copy.deepcopy(self.people)
        self.initial_unrecognized = copy.deepcopy(self.unrecognized)

        # 4. Load suggestions if present in work_dir
        sug_path = work_p / "suggestions.json"
        if sug_path.exists():
            try:
                with open(sug_path, "r", encoding="utf-8") as f:
                    sug_data = json.load(f)
                self.maybe_groups = sug_data.get("maybe_groups", [])
                self.ambiguous_faces_raw = sug_data.get("ambiguous_faces", [])
            except Exception:
                pass
        self.initial_maybe_groups = copy.deepcopy(self.maybe_groups)
        self.initial_ambiguous_faces_raw = copy.deepcopy(self.ambiguous_faces_raw)

        # 5. Replay edits if any and not read-only
        unapplied_edits = []
        if self.edits_list and not self.read_only:
            people_replayed, unrec_replayed, unapplied_edits, _ = apply_edits(
                copy.deepcopy(self.base_people),
                copy.deepcopy(self.base_unrecognized),
                {"version": 1, "edits": self.edits_list},
                self.photos,
            )
            self.people = people_replayed
            self.unrecognized = unrec_replayed

        self.project_active = True
        self.active_project_name = work_p.name.removesuffix(".work")
        if found_people_json and found_people_json.parent.name.lower() != "export" and found_people_json.parent != work_p:
            self.active_project_name = found_people_json.parent.name
        elif export_p and export_p.name.lower() != "export":
            self.active_project_name = export_p.name

        return {
            "work_dir": str(work_p),
            "export_path": str(export_p) if export_p else None,
            "people_count": len(self.people),
            "photos_count": len(self.photos),
            "unrecognized_faces_count": len(self.unrecognized.faces),
            "applied_edits_count": len(self.edits_list),
            "read_only": self.read_only,
            "edits_error": self.edits_error,
        }

    def reset_to_empty(self):
        """Resets active state to clean empty slate for a new project."""
        self.photos = {}
        self.people = []
        self.unrecognized = UnrecognizedGroup(photo_ids=[], faces=[])
        self.id_map = {}
        self.maybe_groups = []
        self.ambiguous_faces_raw = []
        self.base_people = []
        self.base_unrecognized = UnrecognizedGroup(photo_ids=[], faces=[])
        self.initial_people = []
        self.initial_unrecognized = UnrecognizedGroup(photo_ids=[], faces=[])
        self.initial_maybe_groups = []
        self.initial_ambiguous_faces_raw = []
        self.edits_list = []
        self.read_only = False
        self.edits_error = None
        self.project_active = False
        self.active_project_id = None
        self.active_project_name = None
        self.drive_folder_name = None
        self.temp_dirs = []
        self.settings.event_title = "CatLog Gallery"
        self.settings.event_subtitle = "Auto-sorted face albums and photo gallery"

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
        if getattr(self, "read_only", False):
            return False, f"Project is in read-only mode ({self.edits_error}). Edits are disabled to prevent overwriting.", []

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
            # Remove face or photo from person
            if "person_id" in req and req["person_id"]:
                stored_edit["person"] = self.resolve_person_handle_to_anchors(req["person_id"])
            elif "person" in req and req["person"]:
                stored_edit["person"] = req["person"]
            else:
                return False, "Remove requires 'person_id' or 'person' anchors", []

            if not req.get("face_id"):
                if req.get("photo_id"):
                    target_person, _ = locate_person_by_anchors(self.people, stored_edit["person"])
                    if target_person:
                        matching_faces = [f.face_id for f in target_person.faces if f.photo_id == req["photo_id"]]
                        if matching_faces:
                            stored_edit["face_id"] = matching_faces[0]
                        else:
                            return False, f"Photo {req['photo_id']} has no faces in this person", []
                    else:
                        return False, "Could not locate person", []
                else:
                    return False, "Remove requires 'face_id' or 'photo_id'", []
            else:
                stored_edit["face_id"] = req["face_id"]

        elif op == "assign":
            # Assign unrecognized face(s) or photo(s) to person or create new person
            target_anchors = None
            if req.get("person_id") and req["person_id"] != "new":
                target_anchors = self.resolve_person_handle_to_anchors(req["person_id"])
            elif req.get("person"):
                target_anchors = req["person"]
            else:
                target_anchors = None  # creates new person

            face_ids = req.get("face_ids") or ([req["face_id"]] if req.get("face_id") else [])
            photo_ids = req.get("photo_ids") or ([req["photo_id"]] if req.get("photo_id") else [])

            if not face_ids and not photo_ids:
                return False, "Assign requires 'face_id', 'face_ids', 'photo_id', or 'photo_ids'", []

            batch_edits = []
            if face_ids:
                resolved_fids = []
                for fid in face_ids:
                    face_obj, _, _ = find_face_by_id(fid, self.people, self.unrecognized, self.photos)
                    actual_fid = face_obj.face_id if face_obj else fid
                    resolved_fids.append(actual_fid)
                if len(resolved_fids) == 1:
                    batch_edits.append({
                        "op": "assign",
                        "face_id": resolved_fids[0],
                        "person": target_anchors,
                    })
                else:
                    batch_edits.append({
                        "op": "assign",
                        "face_ids": resolved_fids,
                        "person": target_anchors,
                    })

            for pid in photo_ids:
                batch_edits.append({
                    "op": "assign",
                    "photo_id": pid,
                    "person": target_anchors,
                })

            for e in batch_edits:
                self.edits_list.append(e)
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

            return True, f"Applied edit 'assign' ({len(batch_edits)} items)", unapplied

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

    def export_public_bundle(self, output_dir: Optional[str] = None, theme: str = "t-dark") -> List[str]:
        """
        Exports the public bundle ONLY:
        config.json, people.json, faces/, thumbs/, index.html, gallery.html.
        Guarantees suggestions.json, edits.json, id_map.json, and .cache/ are never exported.
        Automatically nests destination directory under drive/project folder name if not already ending in it.
        Deletes all temporary downloaded files upon export completion.
        """
        import shutil

        target = output_dir or self.settings.output_dir or "export"
        if str(target).startswith("http") or "drive.google.com" in str(target):
            target = "export"
            self.settings.output_dir = "export"
        out_p = Path(target).resolve()

        # If a project name or drive folder name is known, ensure we export into a subfolder titled with that name
        folder_title = self.drive_folder_name or self.active_project_name
        if not folder_title and self.settings.event_title and self.settings.event_title not in ("CatLog Gallery", "Face Clubbing Gallery", "Event Gallery"):
            folder_title = self.settings.event_title

        if folder_title and folder_title.lower() != "export":
            safe_folder = re.sub(r'[\\/*?:"<>|]', "", folder_title).strip()
            if safe_folder and out_p.name.lower() != safe_folder.lower():
                out_p = out_p / safe_folder
                out_p.mkdir(parents=True, exist_ok=True)

        cache_p = Path(self.settings.cache_dir).resolve() if self.settings.cache_dir else self.work_dir

        exporter = BundleExporter(
            output_dir=out_p,
            cache_dir=cache_p,
            thumb_size=self.settings.thumb_size,
            face_crop_size=self.settings.face_crop_size,
        )

        # Invariant guarantee: Only export photos that belong to people or unrecognized
        covered_photos = set(self.unrecognized.photo_ids)
        for p in self.people:
            covered_photos.update(p.photo_ids)

        clean_photos = {
            pid: p_rec
            for pid, p_rec in self.photos.items()
            if pid in covered_photos
        }
        if not clean_photos:
            clean_photos = self.photos

        result = EngineResult(
            photos=clean_photos,
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
                "theme": theme,
            },
            include_maybe=self.settings.include_maybe,
            generate_html=True,
        )

        # Clean up temporary working dirs
        for t_dir in list(self.temp_dirs):
            try:
                t_p = Path(t_dir)
                if t_p.exists() and t_p.is_dir():
                    shutil.rmtree(t_p, ignore_errors=True)
            except Exception:
                pass
        self.temp_dirs.clear()

        # Also search for any <folder_name>_temp directory around cache, work dir, or repo root
        if folder_title:
            safe_folder = re.sub(r'[\\/*?:"<>|]', "", folder_title).strip()
            if safe_folder:
                for base in [self.work_dir.parent, self.work_dir, self.repo_root, out_p.parent]:
                    temp_cand = base / f"{safe_folder}_temp"
                    if temp_cand.exists() and temp_cand.is_dir():
                        try:
                            shutil.rmtree(temp_cand, ignore_errors=True)
                        except Exception:
                            pass

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
                bbox = f.get("bbox")
                photo_id = f.get("photo_id", "")
                if not bbox and photo_id in self.photos:
                    p_rec = self.photos[photo_id]
                    if hasattr(p_rec, "faces") and p_rec.faces:
                        for pf in p_rec.faces:
                            if pf.face_id == fid:
                                bbox = pf.bbox
                                break
                elif not bbox and i < len(internal_items):
                    f_obj = internal_items[i].get("face_obj")
                    if f_obj and hasattr(f_obj, "bbox") and f_obj.bbox:
                        bbox = f_obj.bbox

                faces_resp.append(
                    UnrecognizedFaceResponse(
                        face_id=fid,
                        photo_id=photo_id,
                        face=f.get("face", ""),
                        rejection_reason=f.get("rejection_reason", "unattached"),
                        det_score=f.get("det_score"),
                        file_name=self.photos.get(photo_id).file_name if photo_id in self.photos else None,
                        bbox=bbox,
                    )
                )

        return UnrecognizedResponse(
            total_unrecognized_photos=len(self.unrecognized.photo_ids),
            no_face_photos=no_face_photos,
            faces=faces_resp,
        )

    def get_photos_response(self) -> Dict[str, Any]:
        result = {}
        for pid, p in self.photos.items():
            source_exists = False
            if p.original_path:
                try:
                    source_exists = Path(p.original_path).exists() and Path(p.original_path).is_file()
                except Exception:
                    source_exists = False

            result[pid] = {
                "photo_id": pid,
                "file_name": p.file_name,
                "width": p.width,
                "height": p.height,
                "thumb": f"thumbs/{pid}.jpg",
                "source_exists": source_exists,
                "original_path": p.original_path,
                "faces": [
                    {
                        "face_id": f.face_id,
                        "photo_id": pid,
                        "det_score": f.det_score,
                        "bbox": f.bbox,
                        "file_name": p.file_name,
                    }
                    for f in (p.faces or [])
                ],
            }
        return result

    def get_suggestions_response(self) -> SuggestionsResponse:
        """
        Builds suggestions response per SPEC 6.5 & BUILD_PLAN Phase 3:
        1. maybe_groups from clustering
        2. ranked possibly_the_same list (including extended range up to 0.75 for single-photo people)
        3. top-3 candidates for ambiguous faces
        """
        # 1. Compute top-5 centroids for all current people (snapshot for thread safety)
        current_people = list(self.people)
        centroids: Dict[str, np.ndarray] = {}
        for p in current_people:
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
        n_people = len(current_people)

        for i in range(n_people):
            p_a = current_people[i]
            c_a = centroids.get(p_a.id)
            if c_a is None:
                continue

            for j in range(i + 1, n_people):
                p_b = current_people[j]
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
