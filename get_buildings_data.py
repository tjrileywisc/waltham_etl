
import geopandas as gpd

from massgis_api import MassGISAPI
from connect_db import get_db
import constants

TABLE_NAME = "waltham_buildings"

con = get_db()

api = MassGISAPI(service="Building_Structures", layer=0)
features = api.query(where="TOWN_ID=308")

gdf = gpd.GeoDataFrame.from_features(features)
gdf.set_crs(epsg=constants.DEFAULT_CRS, inplace=True)

gdf.to_postgis(TABLE_NAME, con, if_exists="replace")
print(f"Wrote {len(gdf)} rows to '{TABLE_NAME}'")
