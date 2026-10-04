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
uv run python get_wards_precincts_data.py  # fetches Waltham's wards/precincts from the Secretary of the Commonwealth's ArcGIS server → `waltham_wards_precincts` table
uv run python get_buildings_data.py  # fetches Waltham's building footprints from MassGIS's Building_Structures layer → `waltham_buildings` table
uv run python load_zoning_data.py  # loads zoning districts/overlay/codes from the manually-downloaded data/gis/WalthamZoning.zip → 3 tables
uv run python apply_views.py  # runs every `.sql` file in `views/` against the DB (CREATE OR REPLACE VIEW ...)
uv run python load_neighbor_parcel_data.py   # loads all historical years for neighboring towns and Waltham from a manually-downloaded statewide archive zip
```

`get_roads_data.ipynb` — Jupyter notebook for road network data via MassGIS API.

## Architecture

**`massgis_api.py`** — `MassGISAPI` client for ArcGIS FeatureServer REST APIs. Handles pagination (2000 features/page), outputs GeoJSON. Defaults to the MassGIS ArcGIS Online host, but accepts a `base_url` override for other ArcGIS FeatureServer endpoints (e.g. the Secretary of the Commonwealth's server used by `get_wards_precincts_data.py`). All spatial data uses EPSG:26986 (MA Mainland / NAD83), defined in `constants.py`.

**`get_wards_precincts_data.py`** — queries layer 0 of the Secretary of the Commonwealth's `WardsPrecincts2022` FeatureServer (`arcgisserver.digital.mass.gov`, not the usual MassGIS AGOL host) filtered to `TOWN_ID=308`, and writes Waltham's 9 wards / 18 precincts to the `waltham_wards_precincts` table via `geopandas.to_postgis`.

**`get_buildings_data.py`** — queries layer 0 of MassGIS's `Building_Structures` FeatureServer (the standard MassGIS AGOL host, so no `base_url` override needed) filtered to `TOWN_ID=308`, and writes Waltham's ~16,200 building footprints to the `waltham_buildings` table via `geopandas.to_postgis`.

**`load_zoning_data.py`** — reads `WalthamZoning.shp` (zoning districts), `RiverFrontOverlay.shp`, and `ZoningCodes.xlsx` (code → description lookup) out of `data/gis/WalthamZoning.zip` via GDAL's `/vsizip/` mechanism, reprojects the shapefiles from the source CRS (EPSG:2249, MA Mainland feet) to EPSG:26986, and writes `waltham_zoning`, `waltham_zoning_riverfront_overlay`, and `waltham_zoning_codes`. This is an export from Waltham's own GIS department (no public URL), so the zip must be placed manually at that path — same convention as `load_taxparcel_data.py`'s `ZIP_PATH`. The source shapefile has a few self-intersecting rings and one shapeless row (the RB district); these are repaired with `.make_valid()` and coerced to an empty geometry respectively. All geometries are also normalized to `MultiPolygon` (matching the parcel tables' convention) so PostGIS gets a concrete typmod instead of a generic `Geometry` column, and both geometry tables get a `SERIAL PRIMARY KEY` added after load, since the source data has no usable unique field and QGIS otherwise falls back to an unstable `ctid`-derived feature id.

**`apply_views.py`** — reads every `.sql` file in `views/` (in sorted order) and executes it against the DB. The `.sql` files are plain, hand-editable `CREATE OR REPLACE VIEW ...` scripts (so they get proper SQL syntax highlighting and can be run directly against the DB too) rather than being embedded as Python strings.

**`views/vw_waltham_zoned_parcels_2026.sql`** — joins `M308TaxPar_CY26_FY26` to `waltham_zoning` on `ST_Intersects`, one row per parcel. Parcels that straddle a zoning boundary intersect more than one district, so it picks the majority district by overlap area (`DISTINCT ON` ordered by `ST_Area(ST_Intersection(...))` descending) rather than emitting a row per intersected zone, and excludes right-of-way "parcels" (`POLY_TYPE = 'ROW'`, e.g. the town's entire street grid merged into a single polygon by MassGIS) which would otherwise intersect nearly every district. Depends on both `load_zoning_data.py` and whatever loaded the current `M308TaxPar_CY##_FY##` table having already run; the parcel table name is hardcoded to the current vintage and needs updating by hand each year.

**`connect_db.py`** — returns a SQLAlchemy `Engine` connected to the local PostGIS instance. Called at module level in `get_census_data.py`, so the DB must be running before importing it.

**`get_census_data.py`** — queries three Census datasets for Waltham's 13 census tracts (see `WALTHAM_CENSUS_TRACTS` list) and writes each to a separate table via `pandas.to_sql`. Runs serially per-tract per-field — takes several minutes.

**`load_taxparcel_data.py`** — loads historical parcel data for the 6 towns bordering Waltham (Belmont 026, Lexington 155, Lincoln 157, Newton 207, Watertown 314, Weston 333) and Waltham itself from MassGIS's full statewide L3 parcels archive — a single zip containing a separate per-town, per-fiscal-year GDB going back to ~2011-2013. There's no stable URL for this archive (MassGIS serves it from a page, not a fixed link), so it must be downloaded manually and placed at the path set in `ZIP_PATH`; it's gitignored due to size (multiple GB). Reads every layer directly out of the zip via GDAL's `/vsizip/` virtual filesystem — no extraction needed, though GDAL pays a one-time cost building its central-directory index on first access within a process. Writes all 6 layers (`TaxPar`, `Assess`, `_LUT`, `OthLeg`, `UC_LUT`, `Misc`) for every available year of each neighboring town, using the same naming convention as Waltham's own tables.

**Data layout:**
- `data/gis/` — downloaded shapefiles and geodatabases (not committed; see `data/README.md`)
- `db/` — PostGIS init scripts (mounted into Docker container)

## Key reference values

- Waltham city code (MassGIS): `308`
- MA FIPS: `25`, Middlesex County FIPS: `017`
- Default CRS: EPSG 26986 (MA Mainland)
- MassGIS ArcGIS base URL: `https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/`
