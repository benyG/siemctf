from sqlalchemy import select, func, desc
from app.models import Event, Alert, Asset
from app.services.search import build_condition


def _apply_event_filter(stmt, scenario_id: str, q: str = ""):
    stmt = stmt.where(Event.scenario_id == scenario_id)
    condition = build_condition(Event, q)
    if condition is not None:
        stmt = stmt.where(condition)
    return stmt


def build_dashboard(db, scenario_id: str, q: str = "") -> dict:
    total_events = db.scalar(select(func.count()).select_from(_apply_event_filter(select(Event), scenario_id, q).subquery())) or 0

    filtered_events = _apply_event_filter(select(Event.id), scenario_id, q).subquery()
    total_alerts = db.scalar(select(func.count()).select_from(Alert).where(Alert.scenario_id == scenario_id)) or 0
    total_assets = db.scalar(select(func.count()).select_from(Asset).where(Asset.scenario_id == scenario_id)) or 0

    parsed = db.scalar(select(func.count()).select_from(_apply_event_filter(select(Event), scenario_id, q).where(Event.parse_status == "parsed").subquery())) or 0
    partial = db.scalar(select(func.count()).select_from(_apply_event_filter(select(Event), scenario_id, q).where(Event.parse_status == "partial").subquery())) or 0
    failed = db.scalar(select(func.count()).select_from(_apply_event_filter(select(Event), scenario_id, q).where(Event.parse_status == "failed").subquery())) or 0

    by_source = db.execute(
        _apply_event_filter(select(Event.source, func.count()), scenario_id, q)
        .group_by(Event.source)
        .order_by(desc(func.count()))
    ).all()

    top_hosts = db.execute(
        _apply_event_filter(select(Event.hostname, func.count()), scenario_id, q)
        .where(Event.hostname.is_not(None))
        .group_by(Event.hostname)
        .order_by(desc(func.count()))
        .limit(10)
    ).all()

    top_users = db.execute(
        _apply_event_filter(select(Event.username, func.count()), scenario_id, q)
        .where(Event.username.is_not(None))
        .group_by(Event.username)
        .order_by(desc(func.count()))
        .limit(10)
    ).all()

    top_iocs = db.execute(
        _apply_event_filter(select(Event.ioc_match, func.count()), scenario_id, q)
        .where(Event.ioc_match.is_not(None))
        .group_by(Event.ioc_match)
        .order_by(desc(func.count()))
        .limit(10)
    ).all()

    timeline = db.execute(
        _apply_event_filter(select(Event.timestamp, func.count()), scenario_id, q)
        .where(Event.timestamp.is_not(None))
        .group_by(Event.timestamp)
        .order_by(Event.timestamp)
        .limit(48)
    ).all()

    alert_ids = select(Event.id).where(Event.scenario_id == scenario_id)
    latest_alerts = db.execute(
        select(Alert)
        .where(Alert.scenario_id == scenario_id)
        .order_by(desc(Alert.id))
        .limit(10)
    ).scalars().all()
    by_severity = db.execute(
        select(Alert.severity, func.count())
        .where(Alert.scenario_id == scenario_id)
        .group_by(Alert.severity)
        .order_by(desc(func.count()))
    ).all()

    recent_events = db.execute(
        _apply_event_filter(select(Event), scenario_id, q)
        .order_by(desc(Event.id))
        .limit(12)
    ).scalars().all()

    return {
        "summary": {
            "total_events": total_events,
            "total_alerts": total_alerts,
            "total_assets": total_assets,
            "parse_success_rate": round((parsed / total_events) * 100, 2) if total_events else 0,
            "parsed": parsed,
            "partial": partial,
            "failed": failed,
            "query": q,
        },
        "by_source": [{"label": a or "unknown", "value": b} for a, b in by_source],
        "by_severity": [{"label": a or "unknown", "value": b} for a, b in by_severity],
        "top_hosts": [{"label": a or "unknown", "value": b} for a, b in top_hosts],
        "top_users": [{"label": a or "unknown", "value": b} for a, b in top_users],
        "top_iocs": [{"label": a or "unknown", "value": b} for a, b in top_iocs],
        "timeline": [{"label": a, "value": b} for a, b in timeline],
        "latest_alerts": latest_alerts,
        "recent_events": recent_events,
    }
