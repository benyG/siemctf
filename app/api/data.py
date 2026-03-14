from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.db import get_db
from app.models import Event, Alert, Asset
from app.services.scenarios import get_active_scenario
from app.services.search import build_condition, parse_query_string

router = APIRouter(prefix="/api/v1", tags=["data"])

@router.get("/dashboard")
def dashboard_summary(q: str = "", db: Session = Depends(get_db)):
    from app.services.dashboard import build_dashboard
    scenario = get_active_scenario(db)
    if not scenario:
        return {"message": "No active scenario"}
    return build_dashboard(db, scenario.id, q=q)

@router.get("/search")
def search(q: str = "", db: Session = Depends(get_db)):
    scenario = get_active_scenario(db)
    if not scenario:
        return {"results": []}
    query_meta = parse_query_string(q)
    stmt = select(Event).where(Event.scenario_id == scenario.id)
    condition = build_condition(Event, q)
    if condition is not None:
        stmt = stmt.where(condition)
    rows = db.execute(stmt.order_by(Event.id.desc()).limit(200)).scalars().all()
    return {
        "query": query_meta,
        "results": [
            {
                "id": e.id, "timestamp": e.timestamp, "source": e.source, "event_type": e.event_type,
                "hostname": e.hostname, "username": e.username, "src_ip": e.src_ip, "dst_ip": e.dst_ip,
                "process_name": e.process_name, "message": e.message, "ioc_match": e.ioc_match
            } for e in rows
        ]
    }

@router.get("/alerts")
def alerts(db: Session = Depends(get_db)):
    scenario = get_active_scenario(db)
    if not scenario:
        return []
    rows = db.execute(select(Alert).where(Alert.scenario_id == scenario.id).order_by(Alert.id.desc())).scalars().all()
    return [{"id": a.id, "rule_id": a.rule_id, "title": a.title, "severity": a.severity, "status": a.status, "event_id": a.event_id} for a in rows]

@router.get("/assets")
def assets(db: Session = Depends(get_db)):
    scenario = get_active_scenario(db)
    if not scenario:
        return []
    rows = db.execute(select(Asset).where(Asset.scenario_id == scenario.id)).scalars().all()
    return [{"hostname": a.hostname, "ip": a.ip, "os": a.os, "owner": a.owner, "criticality": a.criticality, "department": a.department} for a in rows]
