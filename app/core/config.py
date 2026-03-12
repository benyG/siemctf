import os
from dataclasses import dataclass


def as_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    app_title: str = os.getenv("APP_TITLE", "CTF SIEM")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./ctf_siem.db")
    data_dir: str = os.getenv("DATA_DIR", "./data")
    auto_import_scenarios: bool = as_bool("AUTO_IMPORT_SCENARIOS", True)
    auto_import_all_scenarios: bool = as_bool("AUTO_IMPORT_ALL_SCENARIOS", True)
    scenario_root: str = os.getenv("SCENARIO_ROOT", "./sample_scenarios")
    default_scenario_id: str = os.getenv("DEFAULT_SCENARIO_ID", "phishing_chain")
    api_key: str = os.getenv("API_KEY", "").strip()
    reset_db_on_boot: bool = as_bool("RESET_DB_ON_BOOT", False)
    ui_theme: str = os.getenv("UI_THEME", "crisis").strip().lower()
    enable_theme_selector: bool = as_bool("ENABLE_THEME_SELECTOR", False)
    allowed_themes: tuple[str, ...] = (
        "scifi",
        "espionage",
        "urban",
        "adventure",
        "horror",
        "postapoc",
        "crisis",
    )


settings = Settings()
