# CTF SIEM

`CTF SIEM` est un faux SIEM réaliste pour CTF / formation SOC.

## Ce que contient cette V3

- FastAPI + SQLite
- UI SOC légère mais crédible
- Dashboard réel
- Ingestion de scénarios
- Import ZIP et import depuis un dossier sample
- Parsers:
  - JSON line
  - key=value tolérant
  - regex fallback
- Pipeline:
  - raw records
  - parsing / normalisation
  - IOC matching
  - détection par règles YAML
- Recherche simple `field:value` + texte libre
- Pivot IP / user / host
- Validation d'ingestion
- Dockerfile + docker-compose

## Lancer

```bash
docker compose up --build
```

- Dashboard: `http://localhost:8000/dashboard`
- Docs API: `http://localhost:8000/docs`

## API utiles

- `POST /api/admin/scenarios/import-zip`
- `POST /api/admin/scenarios/import-sample/{scenario_id}`
- `POST /api/admin/scenarios/{scenario_id}/activate`
- `GET /api/admin/scenarios/{scenario_id}/validation`
- `GET /api/search?q=...`

## Exemple de recherche

- `powershell`
- `source:firewall dst_ip:45.77.12.99`
- `hostname:HR-LT-17 user:jdupont`

## Structure d'un scénario

```text
scenario/
├── manifest.yaml
├── logs/
├── assets/assets.csv
├── detections/rules.yaml
├── enrichments/iocs.yaml
└── flags/flags.yaml
```


## V4 search

The Events page now supports a pseudo-KQL/SPL syntax:

- `field:value` exact match
- `field~value` contains match
- wildcard `*` inside `field:value`
- operators `AND`, `OR`, `NOT`
- parentheses `( )`
- quoted free text, e.g. `"encodedcommand"`

Examples:

- `source:sysmon AND process_name:powershell.exe`
- `hostname:HR-LT-17 AND "encodedcommand"`
- `source:firewall AND dst_ip:45.77.*`
- `username:jdupont AND NOT severity:info`
- `message~phishing OR command_line~base64`
