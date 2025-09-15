
import requests
import constants

class MassGISAPI:
    BASE_URL = "https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/"

    def __init__(self, service: str, layer: int):
        """Set up a query for data at a specific MassGIS service and layer.

        Args:
            service (str): the service to fetch from, for example "L3_TAXPAR_POLY_ASSESS_gdb"
            layer (int): the layer number within that service, for example 0
        """
        self.service = service
        self.layer = layer
        self.sess = requests.Session()

    def get_layer_url(self) -> str:
        return f"{self.BASE_URL}{self.service}/FeatureServer/{self.layer}"

    def query(self, where: str = "1=1", out_fields: str = "*", return_geometry: bool = True, out_format: str = "geojson") -> list:
        """Query the MassGIS API for data. Paginates data if necessary.

        Args:
            where (str, optional): a query to run, like `TOWN_ID=308`. Defaults to "1=1".
            out_fields (str, optional): a comma separted list of fields. Defaults to "*".
            return_geometry (bool, optional): whether or not to include geometry. Defaults to True.
            out_format (str, optional): output format of data. Defaults to "geojson".

        Returns:
            list: list of features in GeoJSON format
        """

        page_size = 2000
        
        params = {
            "where": where,
            "outFields": out_fields,
            "returnGeometry": str(return_geometry).lower(),
            "outSR": constants.DEFAULT_CRS,
            "f": out_format,
            "resultOffset": 0,
            "resultRecordCount": page_size,  # max per request
        }

        features = []

        while True:
            r = self.sess.get(
                f"{self.get_layer_url()}/query", params=params
            )
            r.raise_for_status()
            params["resultOffset"] += page_size
            new_features = r.json()["features"]
            if len(new_features) == 0:
                # out of results to fetch
                break
            features.extend(new_features)
            print(f"Fetched {len(features)} features...")

        return features