
import requests
import os

def download(url):

    filename = url.rsplit("/", 1)[1]
    
    if(os.path.exists(f"data/gis/{filename}")):
        print(f"{filename} already exists")
        return

    with open(f"data/gis/{filename}", "wb") as f:
        r = requests.get(url)
        f.write(r.content)

# census tracts (for all of MA)
CENSUS_TRACTS_URL = "https://s3.us-east-1.amazonaws.com/download.massgis.digital.mass.gov/shapefiles/census2020/CENSUS2020_BLK_BG_TRCT.zip"
download(CENSUS_TRACTS_URL)

# property tax parcel data
PROPERTY_TAX_SHAPEFILES_URL = "https://s3.us-east-1.amazonaws.com/download.massgis.digital.mass.gov/shapefiles/l3parcels/L3_SHP_M308_WALTHAM.zip"
download(PROPERTY_TAX_SHAPEFILES_URL)
PROPERTY_TAX_DATABSE_URL = "https://s3.us-east-1.amazonaws.com/download.massgis.digital.mass.gov/gdbs/l3parcels/M308_parcels_gdb.zip"
download(PROPERTY_TAX_DATABSE_URL)

# wards and precincts map (for all of MA)
WARDS_URL = "https://s3.us-east-1.amazonaws.com/download.massgis.digital.mass.gov/shapefiles/state/wardsprecincts2022_poly.zip"
download(WARDS_URL)