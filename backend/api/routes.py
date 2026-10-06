"""FastAPI route definitions for PhotoSorter API layer (BUILD_PLAN Phase 3)."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from backend.api.models import (
    SettingsModel,
    JobStartRequest,
    JobStatusResponse,
    PersonClusterResponse,
    UnrecognizedResponse,
    SuggestionsResponse,
    EditRequest,
    EditResponse,
    RerunRequest,
    RerunResponse,
    ExportRequest,
    ExportResponse,
)
from backend.api.state import AppState
from backend.api.jobs import JobManager


def create_router(state: AppState, job_manager: JobManager) -> APIRouter:
    router = APIRouter(prefix="/api")

    # 1. Job Management Endpoints
    @router.post("/jobs/start", response_model=JobStatusResponse)
    def start_job(req: JobStartRequest = JobStartRequest()):
        try:
            return job_manager.start_job(req)
        except RuntimeError as e:
            raise HTTPException(status_code=409, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/jobs/status", response_model=JobStatusResponse)
    def get_job_status():
        return job_manager.get_status()

    @router.post("/jobs/cancel", response_model=JobStatusResponse)
    def cancel_job():
        return job_manager.cancel_job()

    @router.get("/jobs/progress")
    async def get_jobs_progress():
        return StreamingResponse(
            job_manager.subscribe_progress_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # 2. People & Unrecognized Endpoints
    @router.get("/people", response_model=List[PersonClusterResponse])
    def get_people():
        return state.get_people_response()

    @router.get("/unrecognized", response_model=UnrecognizedResponse)
    def get_unrecognized():
        return state.get_unrecognized_response()

    @router.get("/photos")
    def get_photos():
        return state.get_photos_response()

    # 3. Suggestions Endpoints
    @router.get("/suggestions", response_model=SuggestionsResponse)
    def get_suggestions():
        return state.get_suggestions_response()

    # 4. Edits Endpoint (Merge, Remove, Assign, Hide, Name, Undo)
    @router.post("/edits", response_model=EditResponse)
    def apply_edit(req: EditRequest):
        try:
            success, message, unapplied = state.apply_edit_operation(req.model_dump())
            if not success:
                raise HTTPException(status_code=400, detail=message)

            return EditResponse(
                success=True,
                op=req.op,
                message=message,
                applied_count=len(state.edits_list),
                unapplied_edits=unapplied,
                people_count=len(state.people),
                unrecognized_photos_count=len(state.unrecognized.photo_ids),
                unrecognized_faces_count=len(state.unrecognized.faces),
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # 5. Re-run Pipeline with Edit Replay
    @router.post("/rerun", response_model=RerunResponse)
    def rerun_pipeline(req: RerunRequest = RerunRequest()):
        try:
            success, unapplied, stats = state.rerun_pipeline_with_edits(req.settings)
            return RerunResponse(
                success=success,
                applied_count=stats.get("applied", 0),
                unapplied_edits=unapplied,
                people_count=len(state.people),
                unrecognized_photos_count=len(state.unrecognized.photo_ids),
                unrecognized_faces_count=len(state.unrecognized.faces),
                stats=stats,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # 6. Export Public Bundle Only
    @router.post("/export", response_model=ExportResponse)
    def export_bundle(req: ExportRequest = ExportRequest()):
        try:
            if req.title:
                state.settings.event_title = req.title
            if req.subtitle:
                state.settings.event_subtitle = req.subtitle
            if req.include_maybe is not None:
                state.settings.include_maybe = req.include_maybe

            out_dir = req.output_dir or state.settings.output_dir
            exported_files = state.export_public_bundle(output_dir=out_dir)

            return ExportResponse(
                success=True,
                output_dir=str(out_dir),
                files_exported=exported_files,
                people_count=len(state.people),
                photos_count=len(state.photos),
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # 7. Settings Endpoints
    @router.get("/settings", response_model=SettingsModel)
    def get_settings():
        return state.settings

    @router.post("/settings", response_model=SettingsModel)
    def update_settings(settings: SettingsModel):
        for k, v in settings.model_dump(exclude_unset=True).items():
            if hasattr(state.settings, k) and v is not None:
                setattr(state.settings, k, v)
                if k == "work_dir":
                    state.set_work_dir(v)
        return state.settings

    return router
