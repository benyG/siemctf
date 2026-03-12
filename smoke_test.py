from app.core.db import Base, engine
from app.main import app, startup
from fastapi.testclient import TestClient

Base.metadata.create_all(bind=engine)
startup()

def run():
    with TestClient(app) as client:
        for path in ["/healthz", "/dashboard", "/events", "/alerts", "/assets", "/scenarios"]:
            r = client.get(path)
            assert r.status_code in (200, 307), (path, r.status_code)

        r = client.get("/healthz")
        assert r.status_code == 200
        data = r.json()
        assert "theme" in data
        assert "theme_selector_enabled" in data
        assert "available_themes" in data
        assert len(data["available_themes"]) == 7

        r = client.get("/dashboard")
        assert r.status_code == 200
        assert "CTF SIEM" in r.text

if __name__ == "__main__":
    run()
    print("OK")
