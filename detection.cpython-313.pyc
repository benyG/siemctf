from sqlalchemy import select
from app.models import IOC

def apply_ioc_match(db, scenario_id: str, event_data: dict) -> dict:
    iocs = db.execute(select(IOC).where(IOC.scenario_id == scenario_id)).scalars().all()
    for ioc in iocs:
        if ioc.type == "ip" and ioc.value in {event_data.get("src_ip"), event_data.get("dst_ip")}:
            event_data["ioc_match"] = f"{ioc.type}:{ioc.value}"
            return event_data
        if ioc.type in {"domain", "url", "hash"} and ioc.value in str(event_data.get("message", "")):
            event_data["ioc_match"] = f"{ioc.type}:{ioc.value}"
            return event_data
    return event_data
