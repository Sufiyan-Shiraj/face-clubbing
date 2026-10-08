"""Job manager for running engine pipeline asynchronously with cancel and SSE progress streaming."""

from __future__ import annotations
import asyncio
import json
import os
import threading
import time
import uuid
from typing import Dict, Any, Optional, AsyncGenerator
from pathlib import Path

from backend.engine.pipeline import EngineConfig, run_pipeline
from backend.api.models import JobStatusResponse, JobStartRequest
from backend.api.state import AppState


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
        self.message: str = "Engine is idle."
        self.error: Optional[str] = None
        self.result_summary: Optional[Dict[str, Any]] = None

        # Subscribers for SSE
        self._subscribers: list[asyncio.Queue] = []

    def get_status(self) -> JobStatusResponse:
        with self._lock:
            return JobStatusResponse(
                job_id=self.job_id,
                status=self.status,
                stage=self.stage,
                current=self.current,
                total=self.total,
                percent=self.percent,
                current_file=self.current_file,
                eta_seconds=self.eta_seconds,
                message=self.message,
                error=self.error,
                result_summary=self.result_summary,
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
            if self.total > 0 and self.current > 0:
                self.percent = round((self.current / self.total) * 100.0, 1)
            elif self.stage == "complete":
                self.percent = 100.0
            if "file_name" in payload:
                self.current_file = payload["file_name"]
            if "eta_seconds" in payload:
                self.eta_seconds = payload["eta_seconds"]

            status_dict = {
                "job_id": self.job_id,
                "status": self.status,
                "stage": self.stage,
                "current": self.current,
                "total": self.total,
                "percent": self.percent,
                "current_file": self.current_file,
                "eta_seconds": self.eta_seconds,
                "message": self.message,
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
            self.current = 0
            self.total = 0
            self.percent = 0.0
            self.current_file = None
            self.eta_seconds = None
            self.message = "Initializing job..."
            self.error = None
            self.result_summary = None
            self._cancel_event.clear()

        # Update state settings if requested
        if req.settings:
            for k, v in req.settings.model_dump(exclude_unset=True).items():
                if hasattr(self.state.settings, k) and v is not None:
                    setattr(self.state.settings, k, v)
        if req.input_path:
            self.state.settings.input_path = req.input_path
        env_out = os.environ.get("PHOTOSORTER_OUTPUT_DIR")
        if req.output_dir and (req.output_dir != "export" or not env_out):
            self.state.settings.output_dir = req.output_dir
        elif env_out:
            self.state.settings.output_dir = env_out
        if req.cache_dir:
            self.state.settings.cache_dir = req.cache_dir

        config = EngineConfig(
            input_path=self.state.settings.input_path or str(self.state.repo_root / "test_photos"),
            output_dir=self.state.settings.output_dir,
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
            event_title=self.state.settings.event_title,
            event_subtitle=self.state.settings.event_subtitle,
            progress_callback=self._broadcast_progress,
            cancel_check=lambda: self._cancel_event.is_set(),
        )

        def worker():
            try:
                res = run_pipeline(config)
                self.state.set_result(res)
                with self._lock:
                    self.status = "completed"
                    self.stage = "complete"
                    self.percent = 100.0
                    self.message = f"Job finished. Clustered {len(res.people)} people."
                    self.result_summary = {
                        "people_count": len(res.people),
                        "photos_count": len(res.photos),
                        "unrecognized_faces": len(res.unrecognized.faces),
                        "unrecognized_photos": len(res.unrecognized.photo_ids),
                    }
                self._broadcast_progress({"stage": "complete", "message": self.message})
            except InterruptedError:
                with self._lock:
                    self.status = "cancelled"
                    self.stage = "cancelled"
                    self.message = "Job was cancelled by organizer."
                self._broadcast_progress({"stage": "cancelled", "message": self.message})
            except Exception as e:
                with self._lock:
                    self.status = "failed"
                    self.stage = "failed"
                    self.error = str(e)
                    self.message = f"Error: {e}"
                self._broadcast_progress({"stage": "failed", "message": self.message, "error": str(e)})

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
