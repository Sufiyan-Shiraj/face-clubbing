"""FastAPI main application setup and static file mounting (BUILD_PLAN Phase 3)."""

from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

from backend.api.state import AppState
from backend.api.jobs import JobManager
from backend.api.routes import create_router


def create_app(work_dir: Optional[Path] = None, static_dir: Optional[Path] = None) -> FastAPI:
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

    repo_root = Path(__file__).resolve().parent.parent.parent
    state = AppState(work_dir=work_dir)
    job_manager = JobManager(state=state)

    # Attach instances to app state
    app.state.app_state = state
    app.state.job_manager = job_manager

    # Include API routes
    router = create_router(state, job_manager)
    app.include_router(router)

    # Health check
    @app.get("/api/health")
    def health():
        return {"status": "ok", "version": "1.0.0"}

    # Serve face crops and thumbnails dynamically from output_dir or export/
    @app.get("/faces/{file_path:path}")
    def serve_face(file_path: str):
        out_dir = Path(state.settings.output_dir).resolve() if state.settings.output_dir else repo_root / "export"
        p = out_dir / "faces" / file_path
        if not p.exists():
            p = repo_root / "export" / "faces" / file_path
        if p.exists() and p.is_file():
            return FileResponse(str(p))
        raise HTTPException(status_code=404, detail="Face crop not found")

    @app.get("/thumbs/{file_path:path}")
    def serve_thumb(file_path: str):
        out_dir = Path(state.settings.output_dir).resolve() if state.settings.output_dir else repo_root / "export"
        p = out_dir / "thumbs" / file_path
        if not p.exists():
            p = repo_root / "export" / "thumbs" / file_path
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
