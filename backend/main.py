import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .api.chat import router as chat_router
from .api.sessions import router as sessions_router
from .api.config import router as config_router
from .core.database import create_tables
from .core.settings import settings

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
WORKSPACE_DIR = BASE_DIR / "backend" / "workspace"

app = FastAPI(
    title="AgentForge",
    description="Multi-agent AI platform powered by Microsoft AutoGen",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    create_tables()


app.include_router(chat_router)
app.include_router(sessions_router)
app.include_router(config_router)

if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/{path:path}", include_in_schema=False)
    async def serve_spa(path: str):
        static_path = FRONTEND_DIR / path
        if static_path.exists() and static_path.is_file():
            return FileResponse(str(static_path))
        return FileResponse(str(FRONTEND_DIR / "index.html"))
