FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY sample_scenarios ./sample_scenarios

RUN mkdir -p /data

ENV DATABASE_URL=sqlite:////data/ctf_siem.db \
    APP_TITLE="CTF SIEM" \
    DATA_DIR=/data \
    AUTO_IMPORT_SCENARIOS=true \
    AUTO_IMPORT_ALL_SCENARIOS=true \
    SCENARIO_ROOT=/app/sample_scenarios \
    DEFAULT_SCENARIO_ID=phishing_chain \
    API_KEY=

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
