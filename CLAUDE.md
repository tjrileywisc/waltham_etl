# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

ETL pipeline for Waltham, MA civic data. Fetches from three sources — US Census API, MassGIS ArcGIS REST API, and MassGIS S3 file downloads — and loads into a local PostGIS database.

## Setup

**Dependencies** (uses `uv`):
```
uv sync
```

**Config** — copy `config.default.json` to `config.json` and add your Census API key:
```json
{ "census_api_key": "<your key>" }
```

**Database** — PostGIS runs in Docker. Connect details hardcoded in `connect_db.py`: `postgresql://walthamdata@127.0.0.1:5432/walthamdata`. Read the config.json file to get the password.:
```
docker compose up -d
```

## Running the ETL scripts

Scripts are run directly — no CLI wrapper or orchestrator:

```
uv run python get_census_data.py   # fetches ACS + decennial census → writes 3 tables to DB
uv run python get_gis_layers.py    # downloads shapefiles/GDBs from MassGIS S3 → data/gis/
```

`get_roads_data.ipynb` — Jupyter notebook for road network data via MassGIS API.

## Architecture

**`massgis_api.py`** — `MassGISAPI` client for the MassGIS ArcGIS FeatureServer REST API. Handles pagination (2000 features/page), outputs GeoJSON. All spatial data uses EPSG:26986 (MA Mainland / NAD83), defined in `constants.py`.

**`connect_db.py`** — returns a SQLAlchemy `Engine` connected to the local PostGIS instance. Called at module level in `get_census_data.py`, so the DB must be running before importing it.

**`get_census_data.py`** — queries three Census datasets for Waltham's 13 census tracts (see `WALTHAM_CENSUS_TRACTS` list) and writes each to a separate table via `pandas.to_sql`. Runs serially per-tract per-field — takes several minutes.

**Data layout:**
- `data/gis/` — downloaded shapefiles and geodatabases (not committed; see `data/README.md`)
- `db/` — PostGIS init scripts (mounted into Docker container)

## Key reference values

- Waltham city code (MassGIS): `308`
- MA FIPS: `25`, Middlesex County FIPS: `017`
- Default CRS: EPSG 26986 (MA Mainland)
- MassGIS ArcGIS base URL: `https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/`
