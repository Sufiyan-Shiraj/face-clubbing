"""FastAPI route definitions for PhotoSorter API layer (BUILD_PLAN Phase 3)."""

import re
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
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
    ProjectItem,
    OpenProjectRequest,
    OpenProjectResponse,
    CheckEditsResponse,
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
            source_title = state.get_source_title()
            custom_title = req.title.strip() if req.title and req.title.strip() and req.title not in ("CatLog Gallery", "Face Clubbing Gallery", "Event Gallery") else None
            effective_title = custom_title or source_title

            if effective_title:
                state.settings.event_title = effective_title

            if req.subtitle:
                state.settings.event_subtitle = req.subtitle
            if req.include_maybe is not None:
                state.settings.include_maybe = req.include_maybe

            out_dir = req.output_dir or state.settings.output_dir or "export"
            if str(out_dir).startswith("http") or "drive.google.com" in str(out_dir):
                out_dir = "export"

            # Create folder with the title of the drive/zip/folder or custom gallery title
            target_folder = effective_title or source_title
            if target_folder and target_folder.lower() not in ("export", "event gallery", "catlog gallery", "face clubbing gallery"):
                safe_folder = re.sub(r'[\\/*?:"<>|]', "", target_folder).strip()
                out_p = Path(out_dir).resolve()
                if safe_folder and out_p.name.lower() != safe_folder.lower():
                    out_p = out_p / safe_folder
                    out_p.mkdir(parents=True, exist_ok=True)
                    out_dir = str(out_p)

            exported_files = state.export_public_bundle(
                output_dir=out_dir,
                theme=req.theme or "t-dark",
            )

            # Auto-save recent project entry
            try:
                from backend.api.projects import save_recent_project
                save_recent_project(
                    work_dir=state.work_dir,
                    export_path=out_dir,
                    source_description=state.settings.input_path,
                    counts={"people": len(state.people), "photos": len(state.photos)},
                )
            except Exception:
                pass

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
        st = state.get_source_title()
        if st and (not state.settings.event_title or state.settings.event_title in ("CatLog Gallery", "Face Clubbing Gallery", "Event Gallery")):
            state.settings.event_title = st
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

    # 8b. Download Original Source Photo (Edge Case: source missing / moved check)
    @router.get("/photos/{photo_id}/download")
    def download_original_photo(photo_id: str):
        p_rec = state.photos.get(photo_id)
        if not p_rec or not p_rec.original_path:
            raise HTTPException(status_code=404, detail="Photo record not found")
        orig_p = Path(p_rec.original_path)
        if not orig_p.exists() or not orig_p.is_file():
            raise HTTPException(status_code=404, detail=f"Source photo missing or moved: {p_rec.original_path}")
        from fastapi.responses import FileResponse
        return FileResponse(str(orig_p), filename=p_rec.file_name)

    # 9. Recent Projects Endpoints (SPEC Open saved project)
    @router.get("/projects", response_model=List[ProjectItem])
    def list_projects():
        from backend.api.projects import load_recent_projects
        projects = load_recent_projects()
        return [ProjectItem(**p) for p in projects]

    @router.post("/projects/open", response_model=OpenProjectResponse)
    def open_project(req: OpenProjectRequest):
        from pathlib import Path
        import hashlib
        import datetime
        from backend.api.projects import get_project_by_id, save_recent_project

        # Edge case: Block if scan is currently running
        if job_manager.get_status().status == "running":
            raise HTTPException(
                status_code=409,
                detail="Cannot open project while a scan is currently running. Please wait for the scan to finish or cancel it first.",
            )

        proj = None
        if req.project_id:
            proj = get_project_by_id(req.project_id)
        elif req.work_dir:
            proj = get_project_by_id(req.work_dir)

        if not proj and req.work_dir:
            work_p = Path(req.work_dir).resolve()
            if not work_p.exists() or not work_p.is_dir():
                raise HTTPException(
                    status_code=404,
                    detail=f"Work folder '{work_p}' not found or was moved.",
                )

            resolved_work = work_p
            resolved_export = req.export_path
            sibling_work = work_p.parent / f"{work_p.name}.work"
            if (work_p / "people.json").exists() or (work_p / "manifest.json").exists():
                resolved_export = str(work_p)
                if sibling_work.exists() and sibling_work.is_dir():
                    resolved_work = sibling_work
            elif (work_p / ".cache").exists() and not resolved_export:
                sibling_export = work_p.parent / work_p.name.removesuffix(".work")
                if sibling_export.exists() and sibling_export.is_dir():
                    resolved_export = str(sibling_export)

            proj = {
                "id": hashlib.sha256(str(resolved_work).encode("utf-8")).hexdigest()[:12],
                "name": work_p.name.removesuffix(".work"),
                "work_dir": str(resolved_work),
                "export_path": resolved_export,
                "source_description": "Local Folder",
                "last_opened": datetime.datetime.now().astimezone().isoformat(),
                "counts": {"people": 0, "photos": 0},
                "exists": True,
            }

        if not proj:
            raise HTTPException(
                status_code=404,
                detail=f"Project '{req.project_id or req.work_dir}' not found.",
            )

        # Edge case: Work folder moved or deleted
        work_path = Path(proj["work_dir"])
        if not work_path.exists() or not work_path.is_dir():
            raise HTTPException(
                status_code=404,
                detail=f"Work folder '{work_path}' not found or was moved. Would you like to remove this entry from your recent projects?",
            )

        try:
            res = state.open_saved_project(
                work_dir=proj["work_dir"],
                export_path=proj.get("export_path"),
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to open project: {e}")

        # Update last_opened and counts in projects.json
        updated = save_recent_project(
            work_dir=proj["work_dir"],
            export_path=proj.get("export_path"),
            source_description=proj.get("source_description"),
            counts={"people": res["people_count"], "photos": res["photos_count"]},
            name=proj.get("name"),
        )

        return OpenProjectResponse(
            success=True,
            project=ProjectItem(**updated),
            people_count=res["people_count"],
            photos_count=res["photos_count"],
            unrecognized_faces_count=res["unrecognized_faces_count"],
            read_only=res["read_only"],
            edits_error=res["edits_error"],
            applied_edits_count=res["applied_edits_count"],
            unapplied_edits=res.get("unapplied_edits", []),
        )

    @router.get("/projects/check-edits", response_model=CheckEditsResponse)
    def check_edits(work_dir: Optional[str] = None, input_path: Optional[str] = None):
        target_work = Path(work_dir).resolve() if work_dir else state.work_dir
        edits_file = target_work / "edits.json"

        has_edits = False
        edit_count = 0
        if edits_file.exists():
            try:
                import json
                with open(edits_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and isinstance(data.get("edits"), list):
                    edit_count = len(data["edits"])
                    has_edits = edit_count > 0
            except Exception:
                pass

        prev_source = None
        for cand in [
            target_work / "manifest.json",
            target_work.parent / target_work.name.removesuffix(".work") / "manifest.json",
            state.repo_root / "export" / "manifest.json",
        ]:
            if cand.exists():
                try:
                    import json
                    with open(cand, "r", encoding="utf-8") as f:
                        m_data = json.load(f)
                    prev_source = m_data.get("input_folder") or m_data.get("input_path")
                    if prev_source:
                        break
                except Exception:
                    pass

        if not prev_source:
            from backend.api.projects import load_recent_projects
            for p in load_recent_projects():
                if Path(p.get("work_dir", "")).resolve() == target_work:
                    prev_source = p.get("source_description")
                    break

        is_diff = False
        if input_path and prev_source:
            p1 = str(Path(input_path).resolve()) if Path(input_path).exists() else str(input_path).strip().rstrip("/\\").lower()
            p2 = str(Path(prev_source).resolve()) if Path(prev_source).exists() else str(prev_source).strip().rstrip("/\\").lower()
            is_diff = (p1 != p2)

        default_act = "fresh" if is_diff else ("keep" if has_edits else "fresh")
        msg = f"{edit_count} saved edits found in {target_work.name}" if has_edits else "No saved edits found."

        return CheckEditsResponse(
            has_saved_edits=has_edits,
            saved_edits_count=edit_count,
            work_dir=str(target_work),
            is_different_source=is_diff,
            default_action=default_act,
            previous_source=str(prev_source) if prev_source else None,
            message=msg,
        )

    @router.post("/projects/{project_id}/open", response_model=OpenProjectResponse)
    def open_project_by_id_endpoint(project_id: str):
        return open_project(OpenProjectRequest(project_id=project_id))

    @router.delete("/projects/{project_id}")
    def delete_recent_project(project_id: str):
        from backend.api.projects import remove_recent_project
        success = remove_recent_project(project_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found in recent projects.")
        return {"success": True, "removed": project_id, "message": "Project removed from recent list. Files on disk remain intact."}

    @router.post("/projects/new")
    def create_new_project():
        state.reset_to_empty()
        return {
            "success": True,
            "message": "New project created. Active state reset.",
            "active": False,
        }

    @router.get("/projects/active")
    def get_active_project():
        return {
            "active": getattr(state, "project_active", False) or bool(state.people or state.photos),
            "name": getattr(state, "active_project_name", None),
            "people_count": len(state.people),
            "photos_count": len(state.photos),
        }

    return router
