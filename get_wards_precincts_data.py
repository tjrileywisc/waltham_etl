
import geopandas as gpd

from massgis_api import MassGISAPI
from connect_db import get_db
import constants

# Secretary of the Commonwealth's ArcGIS server (not the usual MassGIS AGOL host)
WARDS_PRECINCTS_BASE_URL = "https://arcgisserver.digital.mass.gov/arcgisserver/rest/services/"

TABLE_NAME = "waltham_wards_precincts"

con = get_db()

api = MassGISAPI(service="AGOL/WardsPrecincts2022", layer=0, base_url=WARDS_PRECINCTS_BASE_URL)
features = api.query(where="TOWN_ID=308")

gdf = gpd.GeoDataFrame.from_features(features)
gdf.set_crs(epsg=constants.DEFAULT_CRS, inplace=True)

gdf.to_postgis(TABLE_NAME, con, if_exists="replace")
print(f"Wrote {len(gdf)} rows to '{TABLE_NAME}'")
