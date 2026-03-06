from collections import defaultdict
from sqlalchemy import delete, select
from app.models import Alert, Event

def _contains_any(text: str, values: list[str]) -> bool:
    text = (text or "").lower()
    return any(v.lower() in text for v in values)

def run_detections(db, scenario_id: str, rules: list[dict]) -> int:
    db.execute(delete(Alert).where(Alert.scenario_id == scenario_id))
    db.commit()
    events = db.execute(select(Event).where(Event.scenario_id == scenario_id)).scalars().all()
    count = 0

    simple_rules = [r for r in rules if not r.get("threshold")]
    threshold_rules = [r for r in rules if r.get("threshold")]

    for event in events:
        for rule in simple_rules:
            cond = rule.get("condition", {})
            ok = True
            for field in ["source", "event_type", "process_name", "hostname", "username", "action"]:
                expected = cond.get(field)
                if expected is not None and str(getattr(event, field) or "") != str(expected):
                    ok = False
                    break
            if not ok:
                continue
            if cond.get("command_line_contains_any") and not _contains_any((event.command_line or "") + " " + (event.message or ""), cond["command_line_contains_any"]):
                continue
            if cond.get("dst_ip_in_iocs") and not event.ioc_match:
                continue
            db.add(Alert(
                scenario_id=scenario_id,
                rule_id=rule.get("id", "rule"),
                title=rule.get("title", "Detection"),
                description=rule.get("description", ""),
                severity=rule.get("severity", "medium"),
                event_id=event.id,
            ))
            count += 1

    for rule in threshold_rules:
        cond = rule.get("condition", {})
        thr = rule.get("threshold", {})
        field = thr.get("field")
        min_count = int(thr.get("count", 0))
        buckets = defaultdict(list)

        for event in events:
            if cond.get("source") and event.source != cond["source"]:
                continue
            if cond.get("event_type") and event.event_type != cond["event_type"]:
                continue
            key = getattr(event, field, None) if field else None
            if key:
                buckets[key].append(event)

        for key, items in buckets.items():
            if len(items) >= min_count:
                db.add(Alert(
                    scenario_id=scenario_id,
                    rule_id=rule.get("id", "threshold_rule"),
                    title=rule.get("title", "Threshold rule"),
                    description=f"{len(items)} events for {field}={key}",
                    severity=rule.get("severity", "medium"),
                    event_id=items[0].id,
                ))
                count += 1

    db.commit()
    return count
