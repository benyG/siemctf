
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models import IngestionJob, Scenario
from app.services.scenarios import (
    activate_scenario,
    import_scenario_directory,
    import_scenario_zip,
    list_scenario_sources,
    resolve_scenario_source,
)


def require_admin_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    # When API_KEY is unset, admin API remains open for local/dev usage.
    if not settings.api_key:
        return
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin_api_key)])


@router.get("/scenarios")
def list_scenarios(db: Session = Depends(get_db)):
    rows = db.execute(select(Scenario).order_by(Scenario.id)).scalars().all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "difficulty": s.difficulty,
            "version": s.version,
            "is_active": s.is_active,
        }
        for s in rows
    ]


@router.get("/scenarios/sources")
def list_sources():
    roots = list_scenario_sources(settings.scenario_root)
    return {
        "root": settings.scenario_root,
        "sources": [
            {
                "source_id": p.name,
                "manifest": str(p / "manifest.yaml"),
                "logs": len(list((p / "logs").glob("*"))) if (p / "logs").exists() else 0,
            }
            for p in roots
        ],
    }


@router.post("/scenarios/import-sample/{scenario_id}")
def import_sample(scenario_id: str, db: Session = Depends(get_db)):
    try:
        source_path = resolve_scenario_source(settings.scenario_root, scenario_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scenario id")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Scenario source not found")
    return {"status": "ok", **import_scenario_directory(db, str(source_path))}


@router.post("/scenarios/import-zip")
async def import_zip(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return {"status": "ok", **import_scenario_zip(db, await file.read())}


@router.post("/scenarios/{scenario_id}/activate")
def activate(scenario_id: str, db: Session = Depends(get_db)):
    if not db.get(Scenario, scenario_id):
        raise HTTPException(status_code=404, detail="Scenario not found")
    activate_scenario(db, scenario_id)
    return {"status": "ok", "active_scenario": scenario_id}


@router.get("/scenarios/{scenario_id}/validation")
def validation(scenario_id: str, db: Session = Depends(get_db)):
    job = (
        db.execute(
            select(IngestionJob)
            .where(IngestionJob.scenario_id == scenario_id)
            .order_by(IngestionJob.id.desc())
        )
        .scalars()
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="No ingestion record")
    return {
        "scenario_id": scenario_id,
        "total_records": job.total_records,
        "parsed_records": job.parsed_records,
        "partial_records": job.partial_records,
        "failed_records": job.failed_records,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
    }

