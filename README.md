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



## Documentation API (reference)

Base URL locale: `http://localhost:8000`

Documentation OpenAPI interactive:

- Swagger UI: `GET /docs`
- Schema OpenAPI JSON: `GET /openapi.json`

### Authentification (routes admin)

- Header: `X-API-Key: <votre_cle>`
- Obligatoire uniquement si la variable d'environnement `API_KEY` est definie.

Exemple:

```bash
curl -H "X-API-Key: change-me" http://localhost:8000/api/admin/scenarios
```

### Endpoints data (`/api/*`)

#### `GET /api/dashboard`

Retourne les metriques agregees du scenario actif.

Parametres:

- `q` (query, optionnel): filtre de recherche applique au dashboard.

Comportement special:

- S'il n'y a pas de scenario actif: `{ "message": "No active scenario" }`.

#### `GET /api/search`

Recherche des evenements dans le scenario actif avec une pseudo-syntaxe KQL/SPL.

Parametres:

- `q` (query, optionnel): expression de recherche.

Reponse:

- `query`: metadonnees d'interpretation de la requete.
- `results`: liste d'evenements (max 200), triee par id decroissant.

Exemple:

```bash
curl "http://localhost:8000/api/search?q=src_ip:10.0.0.5%20AND%20event_type:process"
```

#### `GET /api/alerts`

Retourne les alertes du scenario actif.

Reponse:

- Liste d'objets avec: `id`, `rule_id`, `title`, `severity`, `status`, `event_id`.
- Si aucun scenario actif: `[]`.

#### `GET /api/assets`

Retourne les assets du scenario actif.

Reponse:

- Liste d'objets avec: `hostname`, `ip`, `os`, `owner`, `criticality`, `department`.
- Si aucun scenario actif: `[]`.

### Endpoints admin (`/api/admin/*`)

Toutes ces routes sont protegees par `X-API-Key` si `API_KEY` est configuree.

#### `GET /api/admin/scenarios`

Liste les scenarios presents en base.

Champs retournes:

- `id`, `name`, `description`, `difficulty`, `version`, `is_active`.

#### `GET /api/admin/scenarios/sources`

Liste les dossiers de scenarios detectes sous `SCENARIO_ROOT`.

Reponse:

- `root`: chemin racine de scan.
- `sources`: liste avec `source_id`, `manifest`, `logs` (nombre de fichiers de logs).

#### `POST /api/admin/scenarios/import-sample/{scenario_id}`

Importe un scenario depuis `SCENARIO_ROOT/{scenario_id}`.

Erreurs possibles:

- `400`: id invalide.
- `404`: source introuvable.

#### `POST /api/admin/scenarios/import-zip`

Importe un scenario depuis un fichier ZIP (multipart/form-data).

Exemple:

```bash
curl -X POST -H "X-API-Key: change-me" \
  -F "file=@./my_scenario.zip" \
  http://localhost:8000/api/admin/scenarios/import-zip
```

#### `POST /api/admin/scenarios/{scenario_id}/activate`

Active un scenario existant.

Reponse:

```json
{
  "status": "ok",
  "active_scenario": "phishing_chain"
}
```

Erreur possible:

- `404`: scenario non trouve.

#### `GET /api/admin/scenarios/{scenario_id}/validation`

Retourne le dernier resume d'ingestion du scenario.

Champs retournes:

- `scenario_id`, `total_records`, `parsed_records`, `partial_records`, `failed_records`, `started_at`, `finished_at`.

Erreur possible:

- `404`: aucun historique d'ingestion.

### Endpoint utilitaire

#### `GET /healthz`

Endpoint de sante applicative (non versionne) qui expose:

- `status`
- `theme`
- `theme_selector_enabled`
- `available_themes`
- `scenario_root`
- `api_key_enabled`
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
