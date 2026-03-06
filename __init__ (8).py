import csv
import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
import yaml
from sqlalchemy import delete, select, update
from app.models import Scenario, IngestionJob, RawRecord, Event, Alert, Asset, IOC, Flag
from app.services.normalizer import normalize_line
from app.services.ioc import apply_ioc_match
from app.services.detection import run_detections

def read_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def clear_scenario(db, scenario_id: str):
    for model in [Alert, Event, RawRecord, Asset, IOC, Flag, IngestionJob]:
        db.execute(delete(model).where(model.scenario_id == scenario_id))
    db.execute(delete(Scenario).where(Scenario.id == scenario_id))
    db.commit()

def import_scenario_directory(db, scenario_dir: str) -> dict:
    root = Path(scenario_dir)
    manifest = read_yaml(root / "manifest.yaml")
    scenario_id = manifest.get("id", root.name)
    clear_scenario(db, scenario_id)

    db.add(Scenario(
        id=scenario_id,
        name=manifest.get("name", scenario_id),
        description=manifest.get("description", ""),
        difficulty=manifest.get("difficulty", "medium"),
        version=str(manifest.get("version", "1.0")),
        is_active=False,
    ))
    db.commit()

    job = IngestionJob(scenario_id=scenario_id)
    db.add(job)
    db.commit()

    assets_path = root / "assets" / "assets.csv"
    if assets_path.exists():
        with open(assets_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                db.add(Asset(
                    scenario_id=scenario_id,
                    hostname=row.get("hostname", "unknown"),
                    ip=row.get("ip"),
                    os=row.get("os"),
                    owner=row.get("owner"),
                    criticality=row.get("criticality"),
                    department=row.get("department"),
                ))

    ioc_data = read_yaml(root / "enrichments" / "iocs.yaml")
    for ioc in ioc_data.get("iocs", []):
        db.add(IOC(
            scenario_id=scenario_id,
            type=ioc.get("type", "ip"),
            value=ioc.get("value", ""),
            threat_name=ioc.get("threat_name"),
            confidence=ioc.get("confidence"),
        ))

    flag_data = read_yaml(root / "flags" / "flags.yaml")
    for flag in flag_data.get("flags", []):
        db.add(Flag(
            scenario_id=scenario_id,
            flag=flag.get("flag", "CTF{missing_flag}"),
            location_hint=flag.get("location_hint"),
            trigger_value=flag.get("trigger_value"),
        ))

    db.commit()

    total = parsed = partial = failed = 0
    logs_dir = root / "logs"
    for file_path in sorted(logs_dir.glob("*")):
        if not file_path.is_file():
            continue
        with open(file_path, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                text = line.strip()
                if not text:
                    continue
                total += 1
                normalized = normalize_line(text, file_path.name)
                raw = RawRecord(
                    scenario_id=scenario_id,
                    source_file=file_path.name,
                    line_number=line_number,
                    raw_text=text,
                    detected_format=normalized.get("detected_format", "unknown"),
                    parser_name=normalized.get("parser_name"),
                )
                db.add(raw)
                db.flush()

                normalized = apply_ioc_match(db, scenario_id, normalized)

                db.add(Event(
                    scenario_id=scenario_id,
                    raw_record_id=raw.id,
                    timestamp=normalized.get("timestamp"),
                    source=normalized.get("source", "unknown"),
                    event_type=normalized.get("event_type", "generic_event"),
                    hostname=normalized.get("hostname"),
                    username=normalized.get("username"),
                    src_ip=normalized.get("src_ip"),
                    dst_ip=normalized.get("dst_ip"),
                    dst_port=normalized.get("dst_port"),
                    process_name=normalized.get("process_name"),
                    command_line=normalized.get("command_line"),
                    action=normalized.get("action"),
                    severity=normalized.get("severity", "info"),
                    message=normalized.get("message", text),
                    parse_status=normalized.get("parse_status", "parsed"),
                    parse_confidence=normalized.get("parse_confidence", 0.5),
                    parser_name=normalized.get("parser_name", "unknown"),
                    ioc_match=normalized.get("ioc_match"),
                ))
                status = normalized.get("parse_status", "parsed")
                if status == "parsed":
                    parsed += 1
                elif status == "partial":
                    partial += 1
                else:
                    failed += 1

    db.commit()
    rules = read_yaml(root / "detections" / "rules.yaml").get("rules", [])
    alerts = run_detections(db, scenario_id, rules)

    job.total_records = total
    job.parsed_records = parsed
    job.partial_records = partial
    job.failed_records = failed
    job.finished_at = datetime.utcnow()
    db.commit()

    return {"scenario_id": scenario_id, "events": total, "parsed": parsed, "partial": partial, "failed": failed, "alerts": alerts}

def import_scenario_zip(db, zip_bytes: bytes) -> dict:
    temp = tempfile.mkdtemp(prefix="ctf_siem_")
    try:
        archive = os.path.join(temp, "scenario.zip")
        with open(archive, "wb") as f:
            f.write(zip_bytes)
        extract_dir = os.path.join(temp, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(archive, "r") as zf:
            zf.extractall(extract_dir)
        root = Path(extract_dir)
        children = [p for p in root.iterdir()]
        if len(children) == 1 and children[0].is_dir():
            root = children[0]
        return import_scenario_directory(db, str(root))
    finally:
        shutil.rmtree(temp, ignore_errors=True)

def activate_scenario(db, scenario_id: str):
    db.execute(update(Scenario).values(is_active=False))
    db.execute(update(Scenario).where(Scenario.id == scenario_id).values(is_active=True))
    db.commit()

def get_active_scenario(db):
    return db.execute(select(Scenario).where(Scenario.is_active == True)).scalar_one_or_none()
