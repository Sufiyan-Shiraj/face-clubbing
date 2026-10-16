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
    DirectoryItem,
    ShortcutItem,
    BrowseFolderResponse,
    MkdirRequest,
    SelectDialogRequest,
    SelectDialogResponse,
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

            # 4. Check if there are images in the folder (including subfolders, ignoring videos)
            from backend.drive import DriveClient
            client = DriveClient(api_key=api_key)
            list_res = client.list_folder_images(folder_id=folder_id, recursive=True, stop_after_images=10)
            has_images = list_res.image_count > 0

            if not has_images:
                details = []
                if list_res.skipped_folders_count > 0:
                    details.append(f"searched {list_res.skipped_folders_count} subfolders")
                if list_res.skipped_videos_count > 0:
                    details.append(f"ignored {list_res.skipped_videos_count} video files")
                if list_res.skipped_non_images_count > 0:
                    details.append(f"found non-image files like {', '.join(repr(n) for n in list_res.non_image_sample_names[:3])}")
                extra_msg = f" ({'; '.join(details)})" if details else ""
                return DriveVerifyResponse(
                    valid=False,
                    folder_id=folder_id,
                    folder_name=folder_name,
                    has_images=False,
                    image_count_preview=0,
                    error_type="no_images",
                    message=f"Folder '{folder_name}' was found, but it contains no image files{extra_msg}.",
                )

            return DriveVerifyResponse(
                valid=True,
                folder_id=folder_id,
                folder_name=folder_name,
                has_images=True,
                image_count_preview=list_res.image_count,
                message=f"Verified: '{folder_name}' ({list_res.image_count}+ images found)",
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

            out_dir = req.output_dir or state.settings.output_dir or "export"
            if str(out_dir).startswith("http") or "drive.google.com" in str(out_dir):
                out_dir = "export"
                state.settings.output_dir = "export"
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

    # 8. Filesystem Browser & Folder Picker Endpoints
    @router.get("/fs/browse", response_model=BrowseFolderResponse)
    def browse_filesystem(path: Optional[str] = None):
        try:
            import datetime
            from pathlib import Path
            repo_root = state.repo_root
            if not path or not path.strip():
                target = (repo_root / "export").resolve()
            else:
                p = Path(path.strip())
                if not p.is_absolute():
                    target = (repo_root / p).resolve()
                else:
                    target = p.resolve()

            exists = target.exists()
            is_dir = target.is_dir() if exists else True
            parent_path = str(target.parent) if target.parent != target else None

            subdirs: List[DirectoryItem] = []
            if exists and is_dir:
                try:
                    for child in sorted(target.iterdir(), key=lambda c: c.name.lower()):
                        if child.is_dir() and not child.name.startswith("."):
                            try:
                                mtime = child.stat().st_mtime
                                dt_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                            except Exception:
                                dt_str = None
                            subdirs.append(
                                DirectoryItem(
                                    name=child.name,
                                    path=str(child.resolve()),
                                    modified_time=dt_str,
                                )
                            )
                except PermissionError:
                    pass

            # Common system shortcuts
            home = Path.home()
            shortcuts = [
                ShortcutItem(label="Project Export", path=str((repo_root / "export").resolve())),
                ShortcutItem(label="Project Root", path=str(repo_root.resolve())),
                ShortcutItem(label="Desktop", path=str((home / "Desktop").resolve())),
                ShortcutItem(label="Documents", path=str((home / "Documents").resolve())),
                ShortcutItem(label="Downloads", path=str((home / "Downloads").resolve())),
            ]

            return BrowseFolderResponse(
                current_path=str(target),
                parent_path=parent_path,
                name=target.name or str(target),
                exists=exists,
                is_directory=is_dir,
                directories=subdirs,
                shortcuts=shortcuts,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/fs/mkdir", response_model=BrowseFolderResponse)
    def create_filesystem_folder(req: MkdirRequest):
        try:
            from pathlib import Path
            parent = Path(req.parent_path).resolve()
            new_folder = parent / req.folder_name.strip()
            new_folder.mkdir(parents=True, exist_ok=True)
            return browse_filesystem(str(new_folder))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/fs/select-dialog", response_model=SelectDialogResponse)
    def open_select_folder_dialog(req: Optional[SelectDialogRequest] = None):
        try:
            from pathlib import Path
            from backend.api.dialog import open_folder_dialog
            initial_dir = ""
            if req and req.initial_dir and Path(req.initial_dir).exists():
                initial_dir = str(Path(req.initial_dir).resolve())
            else:
                initial_dir = str((state.repo_root / "export").resolve())

            title = (req and req.title) or "Select Public Export Directory"
            selected = open_folder_dialog(initial_dir=initial_dir, title=title)
            if selected:
                return SelectDialogResponse(selected=str(Path(selected).resolve()), cancelled=False)
            return SelectDialogResponse(selected=None, cancelled=True)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return SelectDialogResponse(selected=None, cancelled=True)

    return router
