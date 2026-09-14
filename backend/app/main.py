from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from alembic import command
from alembic.config import Config
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import crm, schemas
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


@app.get("/api/companies")
def search_companies(
    session: Annotated[Session, Depends(get_session)], q: str = ""
) -> list[schemas.CompanySearchResult]:
    matches = crm.search_companies(session, q)
    return [
        schemas.CompanySearchResult(
            id=company.id,
            company_code=company.company_code,
            company_name=company.company_name,
            region=company.region,
            sales_rep=company.sales_rep,
            matched_contact=(schemas.ContactSummary.model_validate(contact) if contact else None),
        )
        for company, contact in matches
    ]


@app.get("/api/companies/{company_id}")
def get_company(
    company_id: int, session: Annotated[Session, Depends(get_session)]
) -> schemas.CompanyDetail:
    company = crm.get_company_detail(session, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return schemas.CompanyDetail.model_validate(company)


@app.get("/api/companies/{company_id}/activity")
def get_company_activity(
    company_id: int, session: Annotated[Session, Depends(get_session)]
) -> list[schemas.ActivityEntry]:
    entries = crm.get_company_activity(session, company_id)
    return [schemas.ActivityEntry.model_validate(entry) for entry in entries]


@app.get("/api/opportunities/{opportunity_id}/activity")
def get_opportunity_activity(
    opportunity_id: int, session: Annotated[Session, Depends(get_session)]
) -> list[schemas.ActivityEntry]:
    entries = crm.get_opportunity_activity(session, opportunity_id)
    return [schemas.ActivityEntry.model_validate(entry) for entry in entries]
