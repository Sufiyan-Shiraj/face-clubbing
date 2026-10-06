"""FastAPI main application setup and static file mounting (BUILD_PLAN Phase 3)."""

from pathlib import Path
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

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

    # Serve static UI at / (BUILD_PLAN Phase 3 requirement 5)
    repo_root = Path(__file__).resolve().parent.parent.parent
    dist_path = static_dir or (repo_root / "viewer" / "dist")

    if dist_path.exists() and (dist_path / "index.html").exists():
        app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="static_viewer")
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
  <p>Static UI directory not found at viewer/dist. Run <code>npm run build</code> in viewer/.</p>
</body>
</html>"""

    return app


app = create_app()
