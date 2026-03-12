from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.admin import router as admin_router
from app.api.data import router as data_router
from app.core.config import settings
from app.core.db import Base, SessionLocal, engine, get_db
from app.models import Alert, Asset, Event, Scenario
from app.services.dashboard import build_dashboard
from app.services.scenarios import (
    activate_scenario,
    get_active_scenario,
    import_scenario_directory,
    list_scenario_sources,
)
from app.services.search import build_condition, parse_query_string, query_help_examples

template_dir = Path(__file__).resolve().parent / "templates"
templates = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=select_autoescape(["html", "xml"]))


def render(name: str, **ctx):
    base_ctx = {
        "title": settings.app_title,
        "app_title": settings.app_title,
        "theme": settings.ui_theme,
        "theme_selector_enabled": settings.enable_theme_selector,
        "available_themes": settings.allowed_themes,
        "search_examples": query_help_examples(),
    }
    base_ctx.update(ctx)
    return HTMLResponse(templates.get_template(name).render(**base_ctx))


app = FastAPI(title=settings.app_title)
app.include_router(admin_router)
app.include_router(data_router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    if settings.auto_import_scenarios:
        db = SessionLocal()
        try:
            if settings.auto_import_all_scenarios:
                imported_ids: list[str] = []
                for source_dir in list_scenario_sources(settings.scenario_root):
                    result = import_scenario_directory(db, str(source_dir))
                    imported_ids.append(result["scenario_id"])
                if settings.default_scenario_id in imported_ids:
                    activate_scenario(db, settings.default_scenario_id)
                elif imported_ids:
                    activate_scenario(db, imported_ids[0])
            else:
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
def dashboard_page(q: str = "", db: Session = Depends(get_db)):
    scenario = get_active_scenario(db)
    if not scenario:
        return render("empty.html", message="No active scenario loaded.", current_path="/dashboard", global_q=q)
    return render(
        "dashboard.html",
        scenario=scenario,
        dashboard=build_dashboard(db, scenario.id, q=q),
        q=q,
        global_q=q,
        current_path="/dashboard",
        query_meta=parse_query_string(q),
    )


@app.get("/events", response_class=HTMLResponse)
def events_page(q: str = "", db: Session = Depends(get_db)):
    scenario = get_active_scenario(db)
    if not scenario:
        return render("empty.html", message="No active scenario loaded.", current_path="/events", global_q=q)
    query_meta = parse_query_string(q)
    stmt = select(Event).where(Event.scenario_id == scenario.id)
    condition = build_condition(Event, q)
    if condition is not None:
        stmt = stmt.where(condition)
    events = db.execute(stmt.order_by(Event.id.desc()).limit(500)).scalars().all()
    return render(
        "events.html",
        scenario=scenario,
        events=events,
        q=q,
        global_q=q,
        current_path="/events",
        query_meta=query_meta,
        examples=query_help_examples(),
    )


@app.get("/alerts", response_class=HTMLResponse)
def alerts_page(q: str = "", db: Session = Depends(get_db)):
    scenario = get_active_scenario(db)
    if not scenario:
        return render("empty.html", message="No active scenario loaded.", current_path="/alerts", global_q=q)
    stmt = select(Alert).where(Alert.scenario_id == scenario.id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Alert.rule_id.ilike(like),
                Alert.title.ilike(like),
                Alert.description.ilike(like),
                Alert.severity.ilike(like),
                Alert.status.ilike(like),
            )
        )
    alerts = db.execute(stmt.order_by(Alert.id.desc())).scalars().all()
    return render(
        "alerts.html",
        scenario=scenario,
        alerts=alerts,
        q=q,
        global_q=q,
        current_path="/alerts",
        query_meta=parse_query_string(q),
    )


@app.get("/assets", response_class=HTMLResponse)
def assets_page(q: str = "", db: Session = Depends(get_db)):
    scenario = get_active_scenario(db)
    if not scenario:
        return render("empty.html", message="No active scenario loaded.", current_path="/assets", global_q=q)
    stmt = select(Asset).where(Asset.scenario_id == scenario.id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Asset.hostname.ilike(like),
                Asset.ip.ilike(like),
                Asset.os.ilike(like),
                Asset.owner.ilike(like),
                Asset.criticality.ilike(like),
                Asset.department.ilike(like),
            )
        )
    assets = db.execute(stmt.order_by(Asset.hostname.asc())).scalars().all()
    return render(
        "assets.html",
        scenario=scenario,
        assets=assets,
        q=q,
        global_q=q,
        current_path="/assets",
        query_meta=parse_query_string(q),
    )


@app.get("/scenarios", response_class=HTMLResponse)
def scenarios_page(q: str = "", db: Session = Depends(get_db)):
    stmt = select(Scenario).order_by(Scenario.id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Scenario.id.ilike(like),
                Scenario.name.ilike(like),
                Scenario.description.ilike(like),
                Scenario.difficulty.ilike(like),
                Scenario.version.ilike(like),
            )
        )
    scenarios = db.execute(stmt).scalars().all()
    return render("scenarios.html", scenarios=scenarios, q=q, global_q=q, current_path="/scenarios", query_meta=parse_query_string(q))


@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "theme": settings.ui_theme,
        "theme_selector_enabled": settings.enable_theme_selector,
        "available_themes": settings.allowed_themes,
        "scenario_root": settings.scenario_root,
        "api_key_enabled": bool(settings.api_key),
    }
