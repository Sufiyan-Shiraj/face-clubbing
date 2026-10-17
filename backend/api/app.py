import sys
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

from backend.api.state import AppState
from backend.api.jobs import JobManager
from backend.api.routes import create_router


def create_app(
    work_dir: Optional[Path] = None,
    static_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    cache_dir: Optional[Path] = None,
) -> FastAPI:
    app = FastAPI(
        title="PhotoSorter API",
        description="Local organizer API for face clustering, review, edits, and static viewer export.",
        version="1.0.0",
    )

    # Enable CORS for local organizer UI development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        repo_root = Path(sys._MEIPASS)
    else:
        repo_root = Path(__file__).resolve().parent.parent.parent
    state = AppState(work_dir=work_dir, output_dir=output_dir, cache_dir=cache_dir)
    job_manager = JobManager(state=state)

    # Attach instances to app state
    app.state.app_state = state
    app.state.job_manager = job_manager

    # Include API routes
    router = create_router(state, job_manager)
    app.include_router(router)

    # Health check
    @app.get("/api/health")
    @app.get("/health")
    def health():
        return {"status": "ok", "version": "1.0.0"}

    # Serve face crops and thumbnails dynamically from output_dir, work_dir, cache_dir, or export/
    @app.get("/faces/{file_path:path}")
    def serve_face(file_path: str):
        out_raw = state.settings.output_dir
        if not out_raw or str(out_raw).startswith("http") or "drive.google.com" in str(out_raw):
            out_raw = repo_root / "export"
        out_dir = Path(out_raw).resolve()
        candidates = [
            out_dir / "faces" / file_path,
            repo_root / "export" / "faces" / file_path,
        ]
        if state.settings.cache_dir:
            candidates.append(Path(state.settings.cache_dir).resolve() / "crops" / file_path)
            candidates.append(Path(state.settings.cache_dir).resolve() / ".cache" / "crops" / file_path)
        if state.work_dir:
            candidates.append(state.work_dir / "crops" / file_path)
            candidates.append(state.work_dir / ".cache" / "crops" / file_path)
        candidates.append(repo_root / "export.work" / "crops" / file_path)

        for p in candidates:
            if p.exists() and p.is_file():
                return FileResponse(str(p))

        # Check if file_path is a cluster ID (e.g. p001.jpg) and resolve to its representative face
        cluster = state.get_cluster_by_id(Path(file_path).stem)
        if cluster:
            if cluster.rep_face is None and cluster.faces:
                from backend.engine.thumbnails import select_representative_face
                cache_crops_dir = None
                if state.work_dir:
                    cache_crops_dir = state.work_dir / "crops"
                elif state.settings.cache_dir:
                    cache_crops_dir = Path(state.settings.cache_dir).resolve() / "crops"
                cluster.rep_face = select_representative_face(cluster.faces, cache_crops=cache_crops_dir)

            if cluster.rep_face:
                rep_face_file = f"{cluster.rep_face.face_id}.jpg"
                rep_candidates = [
                    out_dir / "faces" / rep_face_file,
                    repo_root / "export" / "faces" / rep_face_file,
                ]
                if state.settings.cache_dir:
                    rep_candidates.append(Path(state.settings.cache_dir).resolve() / "crops" / rep_face_file)
                    rep_candidates.append(Path(state.settings.cache_dir).resolve() / ".cache" / "crops" / rep_face_file)
                if state.work_dir:
                    rep_candidates.append(state.work_dir / "crops" / rep_face_file)
                    rep_candidates.append(state.work_dir / ".cache" / "crops" / rep_face_file)
                rep_candidates.append(repo_root / "export.work" / "crops" / rep_face_file)

                for p in rep_candidates:
                    if p.exists() and p.is_file():
                        return FileResponse(str(p))

                # On-demand generation from original photo if available
                orig_photo = state.photos.get(cluster.rep_face.photo_id)
                if orig_photo and orig_photo.original_path and Path(orig_photo.original_path).exists():
                    from backend.engine.thumbnails import ThumbnailGenerator
                    thumb_gen = ThumbnailGenerator(face_crop_size=state.settings.face_crop_size)
                    target_p = out_dir / "faces" / file_path
                    thumb_gen.generate_square_face_crop(
                        image_path=orig_photo.original_path,
                        bbox=cluster.rep_face.bbox,
                        output_path=target_p,
                    )
                    if target_p.exists():
                        return FileResponse(str(target_p))

        raise HTTPException(status_code=404, detail="Face crop not found")

    @app.get("/thumbs/{file_path:path}")
    def serve_thumb(file_path: str):
        out_raw = state.settings.output_dir
        if not out_raw or str(out_raw).startswith("http") or "drive.google.com" in str(out_raw):
            out_raw = repo_root / "export"
        out_dir = Path(out_raw).resolve()
        candidates = [
            out_dir / "thumbs" / file_path,
            repo_root / "export" / "thumbs" / file_path,
        ]
        if state.settings.cache_dir:
            candidates.append(Path(state.settings.cache_dir).resolve() / "thumbs" / file_path)
            candidates.append(Path(state.settings.cache_dir).resolve() / ".cache" / "thumbs" / file_path)
        if state.work_dir:
            candidates.append(state.work_dir / "thumbs" / file_path)
            candidates.append(state.work_dir / ".cache" / "thumbs" / file_path)
        candidates.append(repo_root / "export.work" / "thumbs" / file_path)

        for p in candidates:
            if p.exists() and p.is_file():
                return FileResponse(str(p))
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    # Serve static UI at / (BUILD_PLAN Phase 3 / Phase 4)
    repo_root = Path(__file__).resolve().parent.parent.parent
    frontend_dist = repo_root / "frontend" / "dist"
    viewer_dist = repo_root / "viewer" / "dist"

    if static_dir:
        dist_path = static_dir
    elif frontend_dist.exists() and (frontend_dist / "index.html").exists():
        dist_path = frontend_dist
    else:
        dist_path = viewer_dist

    if dist_path.exists() and (dist_path / "index.html").exists():
        app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="static_ui")
    else:
        # Fallback placeholder if dist/ has not been built yet
        @app.get("/", response_class=HTMLResponse)
        def index_placeholder():
            return """<!DOCTYPE html>
<html>
<head><title>PhotoSorter API</title></head>
<body style="font-family:sans-serif;background:#0a0a0a;color:#fff;padding:40px;text-align:center;">
  <h1>PhotoSorter Local API Server</h1>
  <p>API endpoints running at <a href="/docs" style="color:#3b82f6;">/docs</a></p>
  <p>Static UI directory not found at frontend/dist or viewer/dist. Run <code>npm run build</code> in frontend/.</p>
</body>
</html>"""

    return app


app = create_app()
