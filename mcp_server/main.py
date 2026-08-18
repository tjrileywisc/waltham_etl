
import argparse
import asyncpg
import json
import logging
import re
import sys

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP
from config import get_config

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("mcp_gis")

@dataclass
class AppContext:
    pool: asyncpg.Pool

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    config = get_config()

    pg_account = config["postgres"]["accounts"]["readonly"]

    user = pg_account["username"]
    password = pg_account["password"]
    host = config["postgres"]["host"]
    database = config["postgres"]["database"]

    logger.info("Connecting to postgres at %s/%s as %s", host, database, user)
    try:
        pool = await asyncpg.create_pool(dsn=f"postgresql://{user}:{password}@{host}/{database}")
    except Exception:
        logger.exception("Failed to connect to postgres at %s/%s", host, database)
        raise
    logger.info("Postgres connection pool ready")

    try:
        yield AppContext(pool=pool)
    finally:
        await pool.close()
        logger.info("Postgres connection pool closed")


_parser = argparse.ArgumentParser()
_parser.add_argument("--host", default="127.0.0.1")
_parser.add_argument("--port", type=int, default=8000)
_args, _ = _parser.parse_known_args()

app = FastMCP("gis-server", lifespan=app_lifespan, host=_args.host, port=_args.port)

@app.tool()
async def query_bbox(layer: str, min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> str:
    """
    Return features within a bounding box as geojson.
    """
    
    pool = app.get_context().request_context.lifespan_context.pool
    rows = await pool.fetch(f"""
        SELECT jsonb_build_object(
            'type', 'Feature', 'geometry', ST_AsGeoJSON(geom)::jsonb,
            'properties', to_jsonb(t) - 'geom'
        )
        
        FROM {layer} t
        WHERE geom && ST_MakeEnvelope($1, $2, $3, $4, 4326)
        LIMIT 500
    """, min_lon, min_lat, max_lon, max_lat)
    features = [json.loads(r[0]) for r in rows]
    
    return json.dumps({"type": "FeatureCollection", "features": features})

@app.tool()
async def point_in_layer(layer: str, lon: float, lat: float) -> str:
    """
    Find which feature(s) from a layer contain a point.
    """
    
    pool = app.get_context().request_context.lifespan_context.pool
    rows = await pool.fetch(f"""
        SELECT to_jsonb(t) - 'geom' AS props
        FROM {layer} t
        WHERE ST_Contains(geom, ST_SetSRID(ST_Point($1, $2), 4326))
    """, lon, lat)
    
    return json.dumps([dict(r["props"]) for r in rows])

@app.tool()
async def features_within_distance(layer: str, lon: float, lat: float, meters: float) -> str:
    """
    Return features within N meters of a point.
    """
    
    pool = app.get_context().request_context.lifespan_context.pool
    rows = await pool.fetch(f"""
        SELECT to_jsonb(t) - 'geom' AS props,
            ST_Distance(
                geom,
                ST_Transform(ST_SetSRID(ST_Point($1, $2), 4326), 26986)
            ) AS distance_m
        FROM \"{layer}\" t
        WHERE ST_DWithin(
            geom,
            ST_Transform(ST_SetSRID(ST_Point($1, $2), 4326), 26986),
            $3
        )
        ORDER BY distance_m
    """, lon, lat, meters)
    
    return json.dumps([
        {**dict(r["props"]), "distance_m": r["distance_m"]} for r in rows
    ])
    
@app.tool()
async def run_spatial_query(sql: str) -> str:
    """
    Run a read-only PostGIS query. SELECT only.
    """
    
    if not sql.strip().upper().startswith("SELECT"):
        return "Error: only SELECT statements allowed"
    
    pool = app.get_context().request_context.lifespan_context.pool
    async with pool.acquire() as conn:
        await conn.execute("SET TRANSACTION READ ONLY")
        rows = await conn.fetch(sql)
    
    return json.dumps([dict(r) for r in rows], default=str)
    
@app.resource("gis://layers")
async def list_layers() -> str:
    """List all available spatial layers and their geometry types."""
    pool = app.get_context().request_context.lifespan_context.pool
    rows = await pool.fetch("""
        SELECT f_table_name AS layer, type AS geometry_type, srid
        FROM geometry_columns
        ORDER BY f_table_name
    """)
    
    # restrict to specific tables
    entries = [dict(r) for r in rows]
    entries = filter(
        lambda x: re.match(r"^M308|RiverFrontOverlay|WalthamZoning|Buildings", x["layer"]), entries
    )
    
    return json.dumps(list(entries))

@app.resource("gis://layers/{layer_name}")
async def get_layer_schema(layer_name: str) -> str:
    """Describe the columns and geometry type of a layer."""
    pool = app.get_context().request_context.lifespan_context.pool
    rows = await pool.fetch("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = $1
    """, layer_name)
    return json.dumps([dict(r) for r in rows])

if __name__ == "__main__":
    app.run(transport="streamable-http")