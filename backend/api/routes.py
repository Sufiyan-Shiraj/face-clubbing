"""FastAPI route definitions for PhotoSorter API layer (BUILD_PLAN Phase 3)."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from backend.api.models import (
    SettingsModel,
    JobStartRequest,
    JobStatusResponse,
    DriveVerifyRequest,
    DriveVerifyResponse,
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

    # 1b. Google Drive Verification Endpoint
    @router.post("/drive/verify", response_model=DriveVerifyResponse)
    def verify_drive_folder(req: DriveVerifyRequest):
        import requests
        from backend.drive.parser import parse_drive_folder_id
        from backend.drive.config import get_drive_api_key

        # 1. Parse folder ID from link or raw ID
        try:
            folder_id = parse_drive_folder_id(req.drive_folder)
        except ValueError as e:
            return DriveVerifyResponse(
                valid=False,
                error_type="invalid_link",
                message=str(e),
            )

        # 2. Check API key presence
        api_key = (req.drive_api_key or "").strip() or get_drive_api_key()
        if not api_key:
            return DriveVerifyResponse(
                valid=False,
                folder_id=folder_id,
                error_type="api_key_missing",
                message="Google Drive API key is missing. Please provide your API key to check Google Drive.",
            )

        # 3. Check folder existence and metadata via Drive API v3
        try:
            meta_url = f"https://www.googleapis.com/drive/v3/files/{folder_id}"
            meta_resp = requests.get(
                meta_url,
                params={
                    "fields": "id,name,mimeType,trashed",
                    "key": api_key,
                    "supportsAllDrives": "true",
                },
                timeout=8,
            )

            if meta_resp.status_code == 400 or "API key not valid" in meta_resp.text:
                return DriveVerifyResponse(
                    valid=False,
                    folder_id=folder_id,
                    error_type="api_key_invalid",
                    message="Invalid Google Drive API key. Please check and re-enter your API key.",
                )
            if meta_resp.status_code == 404:
                return DriveVerifyResponse(
                    valid=False,
                    folder_id=folder_id,
                    error_type="folder_not_found",
                    message=f"Google Drive folder '{folder_id}' was not found. Please verify the link.",
                )
            if meta_resp.status_code == 403:
                return DriveVerifyResponse(
                    valid=False,
                    folder_id=folder_id,
                    error_type="folder_permission_denied",
                    message="Google Drive folder is private or inaccessible. Ensure the folder is shared with 'Anyone with the link' (Viewer access).",
                )
            if meta_resp.status_code != 200:
                return DriveVerifyResponse(
                    valid=False,
                    folder_id=folder_id,
                    error_type="other",
                    message=f"Google Drive API error (HTTP {meta_resp.status_code}).",
                )

            meta_data = meta_resp.json()
            if meta_data.get("trashed"):
                return DriveVerifyResponse(
                    valid=False,
                    folder_id=folder_id,
                    error_type="folder_not_found",
                    message="This Google Drive folder is in trash.",
                )
            if meta_data.get("mimeType") != "application/vnd.google-apps.folder":
                return DriveVerifyResponse(
                    valid=False,
                    folder_id=folder_id,
                    error_type="invalid_link",
                    message="The provided link is for a file, not a Google Drive folder.",
                )

            folder_name = meta_data.get("name", "Google Drive Folder")

            # 4. Check if there are images in the folder
            query = f"'{folder_id}' in parents and trashed = false and (mimeType contains 'image/' or name contains '.jpg' or name contains '.jpeg' or name contains '.png' or name contains '.webp' or name contains '.heic')"
            list_url = "https://www.googleapis.com/drive/v3/files"
            list_resp = requests.get(
                list_url,
                params={
                    "q": query,
                    "pageSize": 10,
                    "fields": "files(id,name,mimeType)",
                    "key": api_key,
                    "supportsAllDrives": "true",
                    "includeItemsFromAllDrives": "true",
                },
                timeout=8,
            )

            has_images = False
            image_count = 0
            if list_resp.status_code == 200:
                files = list_resp.json().get("files", [])
                image_count = len(files)
                has_images = image_count > 0

            if not has_images:
                return DriveVerifyResponse(
                    valid=False,
                    folder_id=folder_id,
                    folder_name=folder_name,
                    has_images=False,
                    image_count_preview=0,
                    error_type="no_images",
                    message=f"Folder '{folder_name}' was found, but it contains no image files.",
                )

            return DriveVerifyResponse(
                valid=True,
                folder_id=folder_id,
                folder_name=folder_name,
                has_images=True,
                image_count_preview=image_count,
                message=f"Verified: '{folder_name}' ({image_count}+ images found)",
            )
        except requests.exceptions.RequestException as e:
            return DriveVerifyResponse(
                valid=False,
                folder_id=folder_id,
                error_type="other",
                message=f"Network error connecting to Google Drive API: {e}",
            )
        except Exception as e:
            return DriveVerifyResponse(
                valid=False,
                folder_id=folder_id,
                error_type="other",
                message=f"Verification failed: {e}",
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
        from backend.drive import get_drive_api_key, mask_api_key
        current = state.settings.model_copy()
        raw_key = get_drive_api_key()
        current.drive_api_key = None  # Never expose raw key
        current.drive_api_key_masked = mask_api_key(raw_key)
        current.drive_api_key_configured = bool(raw_key)
        return current

    @router.post("/settings", response_model=SettingsModel)
    def update_settings(settings: SettingsModel):
        from backend.drive import set_drive_api_key, get_drive_api_key, mask_api_key
        dump = settings.model_dump(exclude_unset=True)
        new_key = dump.pop("drive_api_key", None)
        if new_key and isinstance(new_key, str) and "..." not in new_key and new_key.strip():
            set_drive_api_key(new_key.strip())

        for k, v in dump.items():
            if hasattr(state.settings, k) and v is not None and k not in ("drive_api_key", "drive_api_key_masked", "drive_api_key_configured"):
                setattr(state.settings, k, v)
                if k == "work_dir":
                    state.set_work_dir(v)

        current = state.settings.model_copy()
        raw_key = get_drive_api_key()
        current.drive_api_key = None
        current.drive_api_key_masked = mask_api_key(raw_key)
        current.drive_api_key_configured = bool(raw_key)
        return current

    return router
