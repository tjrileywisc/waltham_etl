
import zipfile

import pyogrio
import pandas as pd
from shapely.geometry import MultiPolygon
from sqlalchemy import text

from connect_db import get_db
import constants


def to_multipolygon(geom):
    # the source shapefile has one row (the RB district) with no shape at all --
    # store it as an empty MultiPolygon rather than NULL so the column keeps a
    # single, concrete PostGIS type instead of falling back to generic Geometry
    if geom is None:
        return MultiPolygon()
    if geom.geom_type == "Polygon":
        return MultiPolygon([geom])
    return geom

# Manually-placed export from Waltham's own GIS department (not from a public
# MassGIS/state URL) -- see data/gis/.gitignore
ZIP_PATH = "data/gis/WalthamZoning.zip"

con = get_db()

for shp_name, table_name in [
    ("WalthamZoning", "waltham_zoning"),
    ("RiverFrontOverlay", "waltham_zoning_riverfront_overlay"),
]:
    path = f"/vsizip/{ZIP_PATH}/WalthamZoning/{shp_name}.shp"
    gdf = pyogrio.read_dataframe(path)
    gdf = gdf.to_crs(epsg=constants.DEFAULT_CRS)
    gdf = gdf.rename_geometry("geom")
    # source shapefile has a handful of self-intersecting rings (e.g. the RA3/RA4/RC/I
    # districts) that fail ST_IsValid and trip up QGIS/PostGIS intersections
    gdf["geom"] = gdf["geom"].make_valid()
    # keep a single, consistent type (matching the parcel tables' convention) so
    # PostGIS gets a real MultiPolygon typmod instead of a generic Geometry column
    gdf["geom"] = gdf["geom"].apply(to_multipolygon)
    gdf.to_postgis(table_name, con, if_exists="replace")
    with con.begin() as conn:
        # no natural unique field in the source data (its own ID column is all zeroes),
        # and without a primary key QGIS falls back to an unstable ctid-derived feature id
        conn.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN id SERIAL PRIMARY KEY'))
    print(f"Wrote {len(gdf)} rows to '{table_name}'")

with zipfile.ZipFile(ZIP_PATH) as z:
    with z.open("WalthamZoning/ZoningCodes.xlsx") as f:
        codes_df = pd.read_excel(f)

codes_df.to_sql("waltham_zoning_codes", con, if_exists="replace", index=False)
print(f"Wrote {len(codes_df)} rows to 'waltham_zoning_codes'")
