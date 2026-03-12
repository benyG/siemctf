# CTF SIEM

`CTF SIEM` est un faux SIEM réaliste pour CTF / formation SOC.

## Stack

- FastAPI + SQLite
- UI SOC multi-thèmes (7 thèmes)
- Ingestion de scénarios (dossiers + ZIP)
- Détection YAML + IOC matching
- Recherche pseudo-KQL/SPL

## Lancer avec Docker Compose

```bash
docker compose up --build
```

- Dashboard: `http://localhost:8000/dashboard`
- Docs API: `http://localhost:8000/docs`

## Injection de scénarios dans le container

Le `docker-compose.yml` monte ce dossier hôte dans le container:

- hôte: `./sample_scenarios`
- container: `/scenarios`
- variable: `SCENARIO_ROOT=/scenarios`

Donc il suffit de déposer plusieurs dossiers de scénarios dans `./sample_scenarios` **avant** ou **après** le démarrage.

Format attendu:

```text
scenario/
+-- manifest.yaml
+-- logs/
+-- assets/assets.csv
+-- detections/rules.yaml
+-- enrichments/iocs.yaml
+-- flags/flags.yaml
```

Au démarrage:

- `AUTO_IMPORT_SCENARIOS=true` active l'import automatique
- `AUTO_IMPORT_ALL_SCENARIOS=true` importe tous les scénarios présents dans `SCENARIO_ROOT`
- `DEFAULT_SCENARIO_ID` est activé en priorité s'il existe

## Clé API admin (variable d'environnement)

Les routes `/api/admin/*` supportent une protection par clé API:

- variable: `API_KEY`
- header HTTP attendu: `X-API-Key: <votre_cle>`

Comportement:

- si `API_KEY` est vide: routes admin ouvertes (dev/local)
- si `API_KEY` est définie: clé obligatoire sur toutes les routes admin

Exemple Compose:

```yaml
environment:
  API_KEY: "change-me"
```

## API d'ingestion (admin)

Toutes ces routes utilisent `X-API-Key` si `API_KEY` est configurée.

- `GET /api/admin/scenarios` liste les scénarios importés
- `GET /api/admin/scenarios/sources` liste les dossiers détectés dans `SCENARIO_ROOT`
- `POST /api/admin/scenarios/import-sample/{scenario_id}` importe un scénario depuis `SCENARIO_ROOT/{scenario_id}`
- `POST /api/admin/scenarios/import-zip` importe un ZIP de scénario
- `POST /api/admin/scenarios/{scenario_id}/activate` active un scénario
- `GET /api/admin/scenarios/{scenario_id}/validation` retourne les stats d'ingestion

### Exemples `curl`

Lister les sources disponibles:

```bash
curl -H "X-API-Key: change-me" \
  http://localhost:8000/api/admin/scenarios/sources
```

Importer un scénario monté dans `/scenarios`:

```bash
curl -X POST -H "X-API-Key: change-me" \
  http://localhost:8000/api/admin/scenarios/import-sample/phishing_chain
```

Importer un ZIP:

```bash
curl -X POST -H "X-API-Key: change-me" \
  -F "file=@./my_scenario.zip" \
  http://localhost:8000/api/admin/scenarios/import-zip
```

Activer un scénario:

```bash
curl -X POST -H "X-API-Key: change-me" \
  http://localhost:8000/api/admin/scenarios/phishing_chain/activate
```

## Thèmes UI

Valeurs supportées (`UI_THEME`):

- `scifi`
- `espionage`
- `urban`
- `adventure`
- `horror`
- `postapoc`
- `crisis`

Activer le sélecteur en UI:

- `ENABLE_THEME_SELECTOR=1`

## API data utiles

- `GET /api/dashboard`
- `GET /api/search?q=...`
- `GET /api/alerts`
- `GET /api/assets`
