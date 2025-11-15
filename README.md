# AdPulse – Modules 1 & 2

Module 1 of **AdPulse** ingests ad platform CSV exports (mock Google/Meta/TikTok), normalizes them into the shared schema and stores the data inside a SQLite database. A Typer-based CLI lets you load CSVs, inspect summaries and verify what landed in the database.

Module 2 layers on a FastAPI service that reads from the same SQLite database to expose health checks, platform/campaign summaries and day-level time series metrics—this becomes the contract future dashboards/AI services consume instead of hitting the database directly.

## Project layout

```
PerformanceMarketExpert/
├── adpulse/                 # Python package with ingestion, storage, models and API code
├── data/                    # SQLite database lives here
├── sample_data/             # Ready-to-ingest example CSVs for Google/Meta/TikTok
├── tests/                   # Pytest smoke tests for the connectors
├── Makefile                 # Helper targets for install/test/CLI
├── pyproject.toml           # Project metadata and CLI entry point
└── requirements.txt
```

## Getting started

```bash
cd PlayGround/PerformanceMarketExpert
make install          # creates .venv/ and installs requirements
source .venv/bin/activate
adpulse --help        # or: python -m adpulse.cli --help
```

The CLI stores normalized data under `data/adpulse.db`. You can override the location by exporting `ADPULSE_DB_PATH=/custom/path/adpulse.db`.

## CLI usage

Load CSV exports into the DB:

```bash
adpulse load google sample_data/google_ads_sample.csv
adpulse load meta sample_data/meta_ads_sample.csv
adpulse load tiktok sample_data/tiktok_ads_sample.csv
# or generate larger synthetic exports (~500 rows each) then ingest:
python scripts/generate_synthetic_data.py
adpulse load google sample_data/synthetic/google_ads_synth.csv
...
```

View an aggregated summary (per platform totals + grand total):

```bash
adpulse summary
```

Sanity check that records exist:

```bash
adpulse verify
```

## Normalized schema

Every connector produces `NormalizedRecord` entries with the following fields:

| Field           | Type   | Description                                |
| --------------- | ------ | ------------------------------------------ |
| `platform`      | text   | Friendly platform name                     |
| `campaign_id`   | text   | Stable slug (platform + campaign)          |
| `campaign_name` | text   | Campaign display name                      |
| `event_date`    | text   | ISO-8601 date of the metric row            |
| `impressions`   | int    | Number of impressions                      |
| `clicks`        | int    | Number of clicks                           |
| `spend`         | float  | Cost / spend in account currency           |
| `conversions`   | int    | Conversion count (or analogous KPI)        |
| `revenue`       | float  | Revenue attributed to the row (derived)    |

The SQLite schema lives in `adpulse/storage/database.py` and is created automatically on first run (Module 1) or via `adpulse.database.init_db()` (Module 2).

## Tests

```bash
make test
```

Pytest validates the CSV connectors plus the FastAPI summary endpoint via dependency overrides. As new connectors or API routes land, extend the tests accordingly.

## Module 2 – FastAPI Metrics service

Start the API (after ingesting CSV data):

```bash
python -m adpulse.api.main
# or
uvicorn adpulse.api.main:app --reload
```

Example endpoints:

```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/health
curl "http://127.0.0.1:8000/summary/platforms?start_date=2024-05-01"
curl "http://127.0.0.1:8000/campaigns/summary?platform=Google%20Ads"
curl "http://127.0.0.1:8000/campaigns/google-brand-awareness/detail"
curl "http://127.0.0.1:8000/timeseries/daily?platform=Meta%20Ads"
```

Routes in brief:

- `/health` – verifies FastAPI is running and that the SQLite connection works.
- `/summary/platforms` – spend/clicks/conversions/revenue/ROAS, grouped by platform with optional date filters.
- `/campaigns/summary` – same metrics but per campaign with optional platform/date filters.
- `/campaigns/{campaign_id}/detail` – aggregates plus day-level breakdown for a specific campaign (optionally filtered by dates).
- `/timeseries/daily` – date-sorted daily aggregates with optional platform/campaign filters for dashboard timelines.

Future Streamlit/AI modules can now call these endpoints instead of reading SQLite directly, which keeps ingestion/storage concerns encapsulated.

## Module 3 – Streamlit Dashboard

Module 3 consumes the FastAPI service to deliver a lightweight analytics UI.

Prerequisites:

1. Ingest data through Module 1 (`adpulse load ...`).
2. Start the FastAPI server (Module 2) on the default port or set `ADPULSE_API_BASE_URL`.

Run the dashboard:

```bash
streamlit run adpulse/dashboard/app.py
```

This launches a Streamlit app with date + platform filters, overview metrics, platform/campaign tables and daily time-series charts powered entirely by the API. Set `ADPULSE_API_BASE_URL` if the FastAPI service is reachable at a non-default URL (e.g. when running remotely).

## Module 4 – AI Insights Layer

Module 4 adds an AI assistant that reads Module 2 endpoints, detects anomalies and asks OpenAI for human-friendly explanations.

### Configure OpenAI or Ollama access

```bash
export ADPULSE_LLM_PROVIDER=openai        # or 'ollama'
export OPENAI_API_KEY="sk-..."            # required when provider=openai
export OLLAMA_API_URL="http://127.0.0.1:11434/api/chat"  # used when provider=ollama
export OLLAMA_MODEL="gpt-oss-20b"
export ADPULSE_API_BASE_URL="https://api.yourdomain.com" # optional if API runs remotely
```

### Insights API

Start the FastAPI server (Module 2) and hit:

- `GET /insights/account-health?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
- `GET /insights/roas-drop?platform=Google%20Ads&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`

Both endpoints respond with an `analysis` string sourced from OpenAI plus metadata (platform/date window). Errors (like missing API keys) return HTTP 500 with a descriptive message.

### Dashboard integration

The Streamlit UI now includes **AI Insights** and **Chatbot** tabs that:

- Displays the account health summary.
- Provides ROAS drop explanations for the selected platform (pick a platform in the sidebar).
- Lets you chat with "AdPulse Copilot" powered by your configured LLM (OpenAI or Ollama) to ask ad-hoc questions about spend/ROAS.

Under the hood: Module 3 calls `/insights/*`, which call Module 2 metrics, which in turn rely on Module 1’s database. The data path is therefore:

`Module 1 (SQLite) → Module 2 (FastAPI metrics) → Module 4 (AI insights) → Module 3 (Streamlit UI)`

## Module 5 – Reporting & Automation

Module 5 automates weekly PDFs that stitch together raw metrics (Module 2) and AI explanations (Module 4). Reports can be generated via CLI or exposed through the API.

### CLI

```bash
# generate PDF in reports/ and optionally trigger the email stub
python -m adpulse.cli generate-report --start-date 2024-05-01 --end-date 2024-05-07 --email you@example.com

# list generated PDFs
python -m adpulse.cli list-reports
```

### API

```bash
# generate a report (POST body includes optional send_email + email fields)
curl -X POST http://127.0.0.1:8000/reports/generate \
  -H "Content-Type: application/json" \
  -d '{"start_date":"2024-05-01","end_date":"2024-05-07"}'

# list existing PDFs
curl http://127.0.0.1:8000/reports/list
```

Module 5 calls the metrics endpoints for platform/campaign data, fetches AI summaries from Module 4, renders a PDF via ReportLab, and (optionally) logs that an email would be sent. This keeps the automation layer decoupled: Module 1 feeds the DB, Module 2/4 provide the data/intelligence, Module 5 packages it for stakeholders or future scheduling workflows.

## Extending the ingestion layer & API

- Add new connectors by subclassing `CSVConnector` (or `BaseConnector` for non-CSV sources) and register them via `connectors.registry`.
- `DataIngestor` depends only on the `ConnectorRegistry` interface and the `DatabaseManager`, so swapping in API-backed connectors or different storage layers will not require CLI changes.
- Settings loading consumes the `ADPULSE_DB_PATH` environment variable, which also feeds `adpulse.database` (and therefore the API). This keeps CLI/API/tests pointed at the same DB without editing code.
- New consumers (Streamlit dashboard, upcoming AI assistants, etc.) should rely on the FastAPI endpoints instead of talking to SQLite directly—this isolates persistence details and keeps higher-level modules focused on UX and intelligence rather than plumbing.
You can also open the Streamlit dashboard and use the **Upload CSV** widget in the sidebar to ingest platform files directly without touching the CLI.
