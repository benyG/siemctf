import os
from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings
from app.core.db import Base, engine, SessionLocal, get_db
from app.models import Scenario, Event, Alert, Asset, Flag
from app.api.admin import router as admin_router
from app.api.data import router as data_router
from app.services.scenarios import import_scenario_directory, activate_scenario, get_active_scenario
from app.services.dashboard import build_dashboard
from app.services.search import build_condition, parse_query_string, query_help_examples

template_dir = Path(__file__).resolve().parent / "templates"
templates = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=select_autoescape(["html", "xml"]))

def render(name: str, **ctx):
    return HTMLResponse(templates.get_template(name).render(**ctx))

app = FastAPI(title=settings.app_title)
app.include_router(admin_router)
app.include_router(data_router)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    if settings.auto_import_scenarios:
        db = SessionLocal()
        try:
            scenario_path = Path(settings.scenario_root) / settings.default_scenario_id
            if scenario_path.exists():
                import_scenario_directory(db, str(scenario_path))
                activate_scenario(db, settings.default_scenario_id)
        finally:
            db.close()

@app.get("/")
def home():
    return RedirectResponse("/dashboard")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(db: Session = Depends(get_db)):
    scenario = get_active_scenario(db)
    if not scenario:
        return render("empty.html", title=settings.app_title, message="No active scenario loaded.")
    return render("dashboard.html", title=settings.app_title, scenario=scenario, dashboard=build_dashboard(db, scenario.id))

@app.get("/events", response_class=HTMLResponse)
def events_page(q: str = "", db: Session = Depends(get_db)):
    scenario = get_active_scenario(db)
    if not scenario:
        return render("empty.html", title=settings.app_title, message="No active scenario loaded.")
    query_meta = parse_query_string(q)
    stmt = select(Event).where(Event.scenario_id == scenario.id)
    condition = build_condition(Event, q)
    if condition is not None:
        stmt = stmt.where(condition)
    events = db.execute(stmt.order_by(Event.id.desc()).limit(500)).scalars().all()
    return render("events.html", title=settings.app_title, scenario=scenario, events=events, q=q, query_meta=query_meta, examples=query_help_examples())

@app.get("/alerts", response_class=HTMLResponse)
def alerts_page(db: Session = Depends(get_db)):
    scenario = get_active_scenario(db)
    if not scenario:
        return render("empty.html", title=settings.app_title, message="No active scenario loaded.")
    alerts = db.execute(select(Alert).where(Alert.scenario_id == scenario.id).order_by(Alert.id.desc())).scalars().all()
    return render("alerts.html", title=settings.app_title, scenario=scenario, alerts=alerts)

@app.get("/assets", response_class=HTMLResponse)
def assets_page(db: Session = Depends(get_db)):
    scenario = get_active_scenario(db)
    if not scenario:
        return render("empty.html", title=settings.app_title, message="No active scenario loaded.")
    assets = db.execute(select(Asset).where(Asset.scenario_id == scenario.id)).scalars().all()
    return render("assets.html", title=settings.app_title, scenario=scenario, assets=assets)

@app.get("/flags", response_class=HTMLResponse)
def flags_page(db: Session = Depends(get_db)):
    scenario = get_active_scenario(db)
    if not scenario:
        return render("empty.html", title=settings.app_title, message="No active scenario loaded.")
    flags = db.execute(select(Flag).where(Flag.scenario_id == scenario.id)).scalars().all()
    return render("flags.html", title=settings.app_title, scenario=scenario, flags=flags)

@app.get("/scenarios", response_class=HTMLResponse)
def scenarios_page(db: Session = Depends(get_db)):
    scenarios = db.execute(select(Scenario).order_by(Scenario.id)).scalars().all()
    return render("scenarios.html", title=settings.app_title, scenarios=scenarios)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}
