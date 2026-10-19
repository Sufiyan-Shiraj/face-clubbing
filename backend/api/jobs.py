"""Job manager for running engine pipeline asynchronously with cancel and SSE progress streaming."""

from __future__ import annotations
import asyncio
import json
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, AsyncGenerator
from backend.api.models import JobStatusResponse, JobStartRequest
from backend.api.state import AppState


def run_pipeline(*args, **kwargs):
    """Lazy proxy for backend.engine.pipeline.run_pipeline to avoid early heavy imports."""
    from backend.engine.pipeline import run_pipeline as _rp
    return _rp(*args, **kwargs)


class JobManager:
    def __init__(self, state: AppState):
        self.state = state
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._cancel_event = threading.Event()

        self.job_id: Optional[str] = None
        self.status: str = "idle"  # "idle" | "running" | "completed" | "failed" | "cancelled"
        self.stage: str = "idle"
        self.current: int = 0
        self.total: int = 0
        self.percent: float = 0.0
        self.current_file: Optional[str] = None
        self.eta_seconds: Optional[float] = None
        self.start_time: Optional[float] = None
        self.elapsed_seconds: Optional[float] = None
        self.message: str = "Engine is idle."
        self.error: Optional[str] = None
        self.result_summary: Optional[Dict[str, Any]] = None
        self.recent_faces: list[str] = []

        # Subscribers for SSE
        self._subscribers: list[asyncio.Queue] = []

    def get_status(self) -> JobStatusResponse:
        with self._lock:
            cur_elapsed = self.elapsed_seconds
            if self.status == "running" and self.start_time:
                cur_elapsed = round(time.time() - self.start_time, 1)
            return JobStatusResponse(
                job_id=self.job_id,
                status=self.status,
                stage=self.stage,
                current=self.current,
                total=self.total,
                percent=self.percent,
                progress=round(self.percent / 100.0, 4),
                current_file=self.current_file,
                eta_seconds=self.eta_seconds,
                elapsed_seconds=cur_elapsed,
                start_time=self.start_time,
                message=self.message,
                error=self.error,
                result_summary=self.result_summary,
                recent_faces=list(self.recent_faces),
            )

    def _broadcast_progress(self, payload: Dict[str, Any]):
        """Broadcasts progress update to status and all SSE subscribers."""
        with self._lock:
            self.stage = payload.get("stage", self.stage)
            self.message = payload.get("message", self.message)
            if "current" in payload:
                self.current = payload["current"]
            if "total" in payload:
                self.total = payload["total"]

            if self.stage == "complete":
                self.percent = 100.0
                if self.total > 0:
                    self.current = self.total
            else:
                if "percent" in payload:
                    new_pct = float(payload["percent"])
                    if self.stage in ("processing", "flip_averaging", "clustering", "exporting"):
                        self.percent = min(99.0, max(0.0, new_pct))
                    else:
                        self.percent = min(99.0, max(self.percent, new_pct))
                elif "progress" in payload:
                    new_pct = round(float(payload["progress"]) * 100.0, 1)
                    if self.stage in ("processing", "flip_averaging", "clustering", "exporting"):
                        self.percent = min(99.0, max(0.0, new_pct))
                    else:
                        self.percent = min(99.0, max(self.percent, new_pct))
                elif self.total > 0 and self.current >= 0:
                    self.percent = min(99.0, round((self.current / self.total) * 100.0, 1))

            if "file_name" in payload:
                self.current_file = payload["file_name"]
            if "eta_seconds" in payload:
                self.eta_seconds = payload["eta_seconds"]

            if "new_faces" in payload and isinstance(payload["new_faces"], list):
                for fid in payload["new_faces"]:
                    if fid and fid not in self.recent_faces:
                        self.recent_faces.append(fid)

            cur_elapsed = self.elapsed_seconds
            if self.start_time:
                cur_elapsed = round(time.time() - self.start_time, 1)
                self.elapsed_seconds = cur_elapsed

            status_dict = {
                "job_id": self.job_id,
                "status": self.status,
                "stage": self.stage,
                "current": self.current,
                "total": self.total,
                "percent": self.percent,
                "progress": round(self.percent / 100.0, 4),
                "current_file": self.current_file,
                "eta_seconds": self.eta_seconds,
                "elapsed_seconds": cur_elapsed,
                "start_time": self.start_time,
                "message": self.message,
                "recent_faces": list(self.recent_faces),
            }

        # Dispatch to async queues safely across threads via call_soon_threadsafe
        for item in list(self._subscribers):
            try:
                q, loop = item
                loop.call_soon_threadsafe(q.put_nowait, status_dict)
            except Exception:
                pass

    def start_job(self, req: JobStartRequest) -> JobStatusResponse:
        with self._lock:
            if self.status == "running":
                raise RuntimeError("A job is already running")

            self.job_id = str(uuid.uuid4())[:8]
            self.status = "running"
            self.stage = "starting"
            self.start_time = time.time()
            self.elapsed_seconds = 0.0
            self.current = 0
            self.total = 0
            self.percent = 0.0
            self.current_file = None
            self.eta_seconds = None
            self.message = "Initializing job..."
            self.error = None
            self.result_summary = None
            self.recent_faces = []
            self._cancel_event.clear()

        # Update state settings if requested
        if req.settings:
            for k, v in req.settings.model_dump(exclude_unset=True).items():
                if hasattr(self.state.settings, k) and v is not None:
                    setattr(self.state.settings, k, v)
        chosen_input = req.drive_folder or req.input_path or req.source_path

        # Defensively sanitize drive/URL confusion in output_dir
        out_candidate = req.output_dir
        if out_candidate and (out_candidate.startswith("http://") or out_candidate.startswith("https://") or "drive.google.com" in out_candidate):
            if not chosen_input:
                chosen_input = out_candidate
            out_candidate = None

        if chosen_input:
            self.state.settings.input_path = chosen_input
            from backend.drive import is_drive_folder_input
            if not is_drive_folder_input(chosen_input):
                inp = Path(chosen_input)
                if inp.suffix.lower() == ".zip":
                    self.state.source_folder_name = inp.stem
                    self.state.active_project_name = inp.stem
                elif inp.name and inp.name.lower() not in ("export", ".", ""):
                    self.state.source_folder_name = inp.name
                    self.state.active_project_name = inp.name
                if self.state.source_folder_name and (not self.state.settings.event_title or self.state.settings.event_title in ("CatLog Gallery", "Face Clubbing Gallery", "Event Gallery")):
                    self.state.settings.event_title = self.state.source_folder_name
        env_out = os.environ.get("PHOTOSORTER_OUTPUT_DIR")
        if out_candidate and (out_candidate != "export" or not env_out):
            self.state.settings.output_dir = out_candidate
        elif env_out:
            self.state.settings.output_dir = env_out
        elif not self.state.settings.output_dir or str(self.state.settings.output_dir).startswith("http") or "drive.google.com" in str(self.state.settings.output_dir):
            self.state.settings.output_dir = "export"
        if req.cache_dir:
            self.state.settings.cache_dir = req.cache_dir

        raw_input = self.state.settings.input_path or "test_photos"
        from backend.drive import is_drive_folder_input, get_drive_api_key
        if is_drive_folder_input(raw_input):
            resolved_input = raw_input
        else:
            input_candidate = Path(raw_input)
            if not input_candidate.is_absolute():
                if (Path.cwd() / input_candidate).exists():
                    resolved_input = str((Path.cwd() / input_candidate).resolve())
                elif (self.state.repo_root / input_candidate).exists():
                    resolved_input = str((self.state.repo_root / input_candidate).resolve())
                else:
                    resolved_input = str(input_candidate.resolve())
            else:
                resolved_input = str(input_candidate)

        drive_key = (
            req.drive_api_key
            or (req.settings.drive_api_key if req.settings else None)
            or self.state.settings.drive_api_key
            or get_drive_api_key()
        )

        out_dir = self.state.settings.output_dir
        if not out_dir or str(out_dir).startswith("http") or "drive.google.com" in str(out_dir):
            out_dir = "export"
            self.state.settings.output_dir = "export"

        should_replay = bool(getattr(req, "keep_edits", False) or getattr(req, "replay_edits", False))
        if not should_replay:
            self.state.edits_list = []
            if self.state.edits_path.exists():
                try:
                    with open(self.state.edits_path, "w", encoding="utf-8") as f:
                        json.dump({"version": 1, "edits": []}, f, indent=2)
                except Exception as e:
                    print(f"[jobs] Warning: Failed to reset edits.json: {e}")

        from backend.engine.pipeline import EngineConfig

        config = EngineConfig(
            input_path=resolved_input,
            output_dir=out_dir,
            cache_dir=self.state.settings.cache_dir,
            distance_threshold=self.state.settings.distance_threshold,
            min_det_score=self.state.settings.min_det_score,
            min_face_size=self.state.settings.min_face_size,
            max_yaw=self.state.settings.max_yaw,
            seed_min_face_size=self.state.settings.seed_min_face_size,
            seed_max_yaw=self.state.settings.seed_max_yaw,
            seed_min_det_score=self.state.settings.seed_min_det_score,
            max_image_dim=self.state.settings.max_image_dim,
            thumb_size=self.state.settings.thumb_size,
            face_crop_size=self.state.settings.face_crop_size,
            second_pass_merge=self.state.settings.second_pass_merge,
            merge_threshold=self.state.settings.merge_threshold,
            maybe_threshold=self.state.settings.maybe_threshold,
            same_photo_merge_max=self.state.settings.same_photo_merge_max,
            attach_distance_cap=self.state.settings.attach_distance_cap,
            flip_average=self.state.settings.flip_average,
            include_maybe=self.state.settings.include_maybe,
            replay_edits=should_replay,
            event_title=self.state.settings.event_title,
            event_subtitle=self.state.settings.event_subtitle,
            drive_api_key=drive_key,
            progress_callback=self._broadcast_progress,
            cancel_check=lambda: self._cancel_event.is_set(),
            cleanup_temp=False,
        )

        def worker():
            try:
                res = run_pipeline(config)
                self.state.set_result(res)
                with self._lock:
                    if self.start_time:
                        self.elapsed_seconds = round(time.time() - self.start_time, 1)
                    self.status = "completed"
                    self.stage = "complete"
                    self.percent = 100.0
                    self.message = f"Job finished. Clustered {len(res.people)} people."
                    self.result_summary = {
                        "people_count": len(res.people),
                        "photos_count": len(res.photos),
                        "unrecognized_faces": len(res.unrecognized.faces),
                        "unrecognized_photos": len(res.unrecognized.photo_ids),
                        "unapplied_edits": getattr(res, "unapplied_edits", []),
                    }

                # Auto-save recent project entry
                try:
                    from backend.api.projects import save_recent_project
                    save_recent_project(
                        work_dir=self.state.work_dir,
                        export_path=self.state.settings.output_dir,
                        source_description=self.state.settings.input_path,
                        counts={"people": len(res.people), "photos": len(res.photos)},
                    )
                except Exception as e:
                    print(f"[jobs] Warning: Failed to auto-save recent project: {e}")

                self._broadcast_progress({"stage": "complete", "message": self.message})
            except InterruptedError:
                with self._lock:
                    if self.start_time:
                        self.elapsed_seconds = round(time.time() - self.start_time, 1)
                    self.status = "cancelled"
                    self.stage = "cancelled"
                    self.message = "Job was cancelled by organizer."
                self._broadcast_progress({"stage": "cancelled", "message": self.message})
            except Exception as e:
                import traceback
                tb_str = traceback.format_exc()
                traceback.print_exc()
                with self._lock:
                    if self.start_time:
                        self.elapsed_seconds = round(time.time() - self.start_time, 1)
                    self.status = "failed"
                    self.stage = "failed"
                    self.error = f"{e}\n{tb_str}"
                    self.message = f"Error: {e}"
                self._broadcast_progress({"stage": "failed", "message": self.message, "error": self.error})

        self._thread = threading.Thread(target=worker, daemon=True)
        self._thread.start()

        return self.get_status()

    def cancel_job(self) -> JobStatusResponse:
        with self._lock:
            if self.status == "running":
                self._cancel_event.set()
                self.status = "cancelled"
                self.stage = "cancelling"
                self.message = "Cancelling job..."
        self._broadcast_progress({"stage": "cancelling", "message": "Cancelling job..."})
        return self.get_status()

    async def subscribe_progress_stream(self) -> AsyncGenerator[str, None]:
        """Yields server-sent events (SSE) for progress streaming."""
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()
        sub_entry = (queue, loop)
        self._subscribers.append(sub_entry)

        try:
            # Yield initial status immediately
            init_status = self.get_status()
            yield f"data: {json.dumps(init_status.model_dump())}\n\n"

            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=2.0)
                    yield f"data: {json.dumps(payload)}\n\n"
                except asyncio.TimeoutError:
                    # Keepalive comment to prevent proxy timeouts
                    yield ": keepalive\n\n"
        finally:
            if sub_entry in self._subscribers:
                self._subscribers.remove(sub_entry)
