from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from alembic import command
from alembic.config import Config
from fastapi import Depends, FastAPI
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal, get_session
from app.importer import import_archive
from app.models import ActivityLogEntry, Company, Contact, Opportunity

BACKEND_ROOT = Path(__file__).resolve().parent.parent


def _run_migrations() -> None:
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    _run_migrations()
    with SessionLocal() as session:
        import_archive(session, settings.data_dir)
    yield


app = FastAPI(title="Exhibition Sales CRM", lifespan=lifespan)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/summary")
def summary(session: Annotated[Session, Depends(get_session)]) -> dict[str, int]:
    return {
        "companies": session.scalar(select(func.count()).select_from(Company)) or 0,
        "contacts": session.scalar(select(func.count()).select_from(Contact)) or 0,
        "opportunities": session.scalar(select(func.count()).select_from(Opportunity)) or 0,
        "activity_log_entries": session.scalar(select(func.count()).select_from(ActivityLogEntry))
        or 0,
    }
