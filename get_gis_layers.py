
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
