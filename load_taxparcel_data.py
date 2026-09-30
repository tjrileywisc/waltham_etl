
import re
import zipfile

import pyogrio
import pandas as pd

from connect_db import get_db

# Full statewide L3 parcels archive: one sub-GDB per town per fiscal year,
# each containing the same 6 layers as a single-town L3 parcels download
# (TaxPar, Assess, LUT, OthLeg, UC_LUT, Misc). Read directly out of the zip
# via GDAL's /vsizip/ mechanism -- no need to extract ~8GB to disk.
ZIP_PATH = "data/L3_AGGREGATE_FGDB_20260702.zip"

# Communities neighboring Waltham, and Waltham itself (308)
NEIGHBOR_TOWN_CODES = ["026", "155", "157", "207", "314", "333", "308"]

GEOMETRY_LAYER_SUFFIXES = ["TaxPar", "OthLeg", "Misc"]
TABLE_LAYER_SUFFIXES = ["Assess", "_LUT", "UC_LUT"]

GDB_NAME_RE = re.compile(r"^M(\d{3})_parcels_(CY\d{2}_FY\d{2})_sde\.gdb$")

con = get_db()

with zipfile.ZipFile(ZIP_PATH) as z:
    gdb_folders = sorted({n.split("/")[0] for n in z.namelist()})

for code in NEIGHBOR_TOWN_CODES:
    town_gdbs = [
        (m.group(2), folder)
        for folder in gdb_folders
        if (m := GDB_NAME_RE.match(folder)) and m.group(1) == code
    ]

    for suffix, gdb_folder in sorted(town_gdbs):
        path = f"/vsizip/{ZIP_PATH}/{gdb_folder}"

        for layer_suffix in GEOMETRY_LAYER_SUFFIXES:
            layer = f"M{code}{layer_suffix}"
            gdf = pyogrio.read_dataframe(path, layer=layer)
            gdf = gdf.rename_geometry("geom")
            table_name = f"{layer}_{suffix}"
            gdf.to_postgis(table_name, con, if_exists="replace")
            print(f"Wrote {len(gdf)} rows to '{table_name}'")

        for layer_suffix in TABLE_LAYER_SUFFIXES:
            layer = f"M{code}{layer_suffix}"
            df = pd.DataFrame(pyogrio.read_dataframe(path, layer=layer))
            table_name = f"{layer}_{suffix}"
            df.to_sql(table_name, con, if_exists="replace", index=False)
            print(f"Wrote {len(df)} rows to '{table_name}'")
