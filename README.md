# BrewDesk

A coffee-and-workspace finder by Jason Breedlove. BrewDesk combines `python_coffee_wifi_flask` and `cafe_db_v2_flask` into one Flask application, keeping the original café collection while replacing the old Bootstrap pages and unsafe public mutation routes.

## Features

- SQL-backed name search, minimum coffee/Wi-Fi/power ratings, and stable sorting.
- A responsive café directory, map links, and side-by-side comparison of up to three cafés.
- Browser-local bookmarks and personal café creation, editing, and removal.
- Legacy CSV import that converts emoji ratings and inconsistent time strings, validates the whole file before writing, and preserves existing records.
- Tests for routes, filtering, unsafe writes, import validation, and personal-workspace data.

## Run

Use Python 3.12 or newer:

```sh
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
flask --app app run
```

Open http://127.0.0.1:5000. Run `pytest -q` and `node --test public/static/workspace.test.mjs` to verify the backend and browser data rules.

## Storage and scope

Without `DATABASE_URL`, the server loads five original sample cafés into an isolated in-memory SQLite catalog. Public catalog requests are read-only, so this mode is safe on serverless hosts. The sample catalog is reproducible after a cold start; it is not shared writable storage. No external database account is required for the demo.

Personal cafés and bookmarks are stored in the current browser's local storage, never sent to the server. They are device-specific and can be lost when browser data is cleared. No login, crowdsourced submissions, cross-device synchronization, live opening status, or real-time Wi-Fi verification is claimed.

For a persistent, operator-managed catalog, set `DATABASE_URL` to a PostgreSQL URL (or an absolute SQLite URL for a persistent local host), then run:

```sh
flask --app app init-db
flask --app app import-legacy data/legacy-cafes.csv
```

The namespaced `brewdesk_cafes` table leaves old `cafe` tables untouched. Schema creation and import are explicit operator commands; HTTP routes cannot delete or change catalog records. Keep database credentials in deployment environment variables, never Git.

## Data provenance

`data/legacy-cafes.csv` is copied from the original `python_coffee_wifi_flask/static/cafe-data.csv`. `data/catalog.json` is its normalized equivalent, verified by a test. All five rows retain their original names, links, ratings, and hours. They are visibly labeled as legacy samples because their current accuracy has not been verified. The inherited Starbucks and Mare Street Market map links are identical in the source; they are preserved as samples, not presented as independently verified locations.

The original SQLite/CSV project contributed the sample collection and local-use concept; the v2 project contributed the relational café model and external-database direction. Original commits remain in each repository's Git history. This repository is the maintained successor; the earlier project links here.

## Deploy

Import this repository into Vercel as a Flask project, with the repository root as the root directory. Vercel discovers `app.py` and `requirements.txt`; Python 3.12+ is declared in `pyproject.toml`. No build command or environment variables are required for sample mode. `/health` checks the database connection.

Production security headers restrict scripts to this origin. Text is rendered with DOM text APIs; personal map links require HTTPS and reject embedded credentials. GET requests have no mutation side effects. The old public `/add` and `/delete/<id>` routes are intentionally absent.
