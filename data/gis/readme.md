
# waltham gis data

NOTE: Waltham seems to have the ID 308, which is the 1 indexed row number in this
excel file (so Waltham is on row 307):
https://www.mass.gov/doc/massgis-parcel-data-download-links-table/download

Neighbooring cities:
Arlington 10
Lexington 155
Lincoln 157
Newton 207
Watertown 314
Weston 333

## what's in here?

- L3_SHIP_M308_WALTHAM
    Content: Waltham property tax data
    Obtained from: http://download.massgis.digital.mass.gov/shapefiles/l3parcels/L3_SHP_M308_WALTHAM.zip
    Shapefiles of interest:
        - M308TaxPar_CY22_FY23
            Content: the actual vector shapes of each parcel
        - M308Misc_CY22_FY23
            Content: something about wetlands and other undeveloped land?
    Databases of interest:
        - M308UC_LUT_CY22_FY23
            Content: definitions of land uses
        - M308Assess_CY22_FY23
            Content: the main tax assessment db
        - M308_LUT_CY22_FY23
            Content: miscellaneous land feature defintions

- M308_parcels_gdb
    Content: Property tax data per parcel
    Obtained from: http://download.massgis.digital.mass.gov/gdbs/l3parcels/M308_parcels_gdb.zip'
    Obtained on: 2023/01/08

- wardsprecints2022_poly
    Content: Waltham political wards in 2022
    Obtained from: https://www.mass.gov/info-details/massgis-data-2022-wards-and-precincts

- MassGIS Data: 2020 U.S. Census
    Where to get it: https://www.mass.gov/info-details/massgis-data-2020-us-census


