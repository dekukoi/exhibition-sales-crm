import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Annotated

from alembic import command
from alembic.config import Config
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import crm, follow_ups, handoff, opportunities, schemas
from app.config import settings
from app.db import SessionLocal, get_session
from app.importer import import_archive_if_needed
from app.models import ActivityLogEntry, Company, Contact, Opportunity

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
# Alembic's fileConfig (see migrations/env.py, run on every startup) resets the root
# logger's level to WARNING, which would otherwise silently swallow our INFO-level
# startup/import progress logged after migrations run. Giving "app" its own explicit
# level makes it independent of whatever the root logger's level is at call time.
logging.getLogger("app").setLevel(logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_ROOT = Path(__file__).resolve().parent.parent


def _run_migrations() -> None:
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Running database migrations")
    _run_migrations()
    logger.info("Migrations up to date")
    with SessionLocal() as session:
        if import_archive_if_needed(session, settings.data_dir) is None:
            logger.info("Startup import skipped; serving with existing data")
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
    session: Annotated[Session, Depends(get_session)],
    q: str = "",
    limit: int = 15,
    offset: int = 0,
) -> schemas.CompanySearchListResult:
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    matches, total = crm.search_companies(session, q, limit=limit, offset=offset)
    items = [
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
    return schemas.CompanySearchListResult(items=items, total=total)


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


@app.get("/api/opportunities/statuses")
def list_opportunity_statuses(session: Annotated[Session, Depends(get_session)]) -> list[str]:
    return opportunities.list_statuses(session)


@app.patch("/api/opportunities/{opportunity_id}")
def update_opportunity(
    opportunity_id: int,
    payload: schemas.OpportunityUpdate,
    session: Annotated[Session, Depends(get_session)],
) -> schemas.OpportunitySummary:
    opportunity = opportunities.update_opportunity(session, opportunity_id, payload)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return schemas.OpportunitySummary.model_validate(opportunity)


@app.post("/api/opportunities/{opportunity_id}/activity")
def create_opportunity_activity(
    opportunity_id: int,
    payload: schemas.ActivityCreate,
    session: Annotated[Session, Depends(get_session)],
) -> schemas.ActivityEntry:
    entry = opportunities.add_activity(session, opportunity_id, payload)
    if entry is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return schemas.ActivityEntry.model_validate(entry)


@app.post("/api/opportunities/{opportunity_id}/handoff-runs")
def trigger_handoff_run(
    opportunity_id: int, session: Annotated[Session, Depends(get_session)]
) -> schemas.HandoffRunSummary:
    run = handoff.run_handoff(session, opportunity_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return schemas.HandoffRunSummary.model_validate(run)


@app.get("/api/opportunities/{opportunity_id}/handoff-runs")
def list_handoff_runs(
    opportunity_id: int, session: Annotated[Session, Depends(get_session)]
) -> list[schemas.HandoffRunSummary]:
    runs = handoff.list_handoff_runs(session, opportunity_id)
    return [schemas.HandoffRunSummary.model_validate(run) for run in runs]


def _follow_up_item(
    entry: ActivityLogEntry, company: Company, opportunity: Opportunity | None
) -> schemas.FollowUpItem:
    assert entry.follow_up_on is not None
    return schemas.FollowUpItem(
        id=entry.id,
        follow_up_on=entry.follow_up_on,
        activity_type=entry.activity_type,
        details=entry.details,
        occurred_at=entry.occurred_at,
        legacy_author=entry.legacy_author,
        company_id=company.id,
        company_name=company.company_name,
        sales_rep=company.sales_rep,
        opportunity_id=opportunity.id if opportunity else None,
        opportunity_code=opportunity.opportunity_code if opportunity else None,
    )


@app.get("/api/follow-ups")
def list_follow_ups(
    session: Annotated[Session, Depends(get_session)],
    sales_rep: str | None = None,
    company: str | None = None,
    due_before: date | None = None,
    limit: int = 50,
    offset: int = 0,
) -> schemas.FollowUpListResult:
    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    rows = follow_ups.list_pending_follow_ups(
        session,
        sales_rep=sales_rep,
        company=company,
        due_before=due_before,
        limit=limit,
        offset=offset,
    )
    total = follow_ups.count_pending_follow_ups(
        session, sales_rep=sales_rep, company=company, due_before=due_before
    )
    items = [_follow_up_item(entry, comp, opp) for entry, comp, opp in rows]
    has_more = offset + len(items) < total
    return schemas.FollowUpListResult(items=items, has_more=has_more, total=total)


@app.get("/api/follow-ups/sales-reps")
def list_follow_up_sales_reps(session: Annotated[Session, Depends(get_session)]) -> list[str]:
    return follow_ups.list_sales_reps(session)


@app.post("/api/follow-ups/{follow_up_id}/complete")
def complete_follow_up(
    follow_up_id: int, session: Annotated[Session, Depends(get_session)]
) -> schemas.FollowUpItem:
    result = follow_ups.mark_follow_up_complete(session, follow_up_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    entry, company, opportunity = result
    return _follow_up_item(entry, company, opportunity)
