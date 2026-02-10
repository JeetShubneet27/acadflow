from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    annotations,
    audit,
    auth,
    conferences,
    drafts,
    maintenance,
    news,
    plagiarism,
    projects,
    reviews,
    users,
    workspace,
)
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.utils.files import ensure_directory


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(projects.router)
    app.include_router(drafts.router)
    app.include_router(reviews.router)
    app.include_router(plagiarism.router)
    app.include_router(news.router)
    app.include_router(conferences.router)
    app.include_router(workspace.router)
    app.include_router(annotations.router)
    app.include_router(audit.router)
    app.include_router(maintenance.router)

    return app


app = create_app()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_directory(settings.storage_dir)
