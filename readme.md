
# ETL for Waltham, MA specific data

## Instructions

This project uses [`pdm`](https://pdm.fming.dev/latest/) as a dependencies manager and [`dvc`](https://dvc.org/doc) to manage data versioning.

Firstly, make sure you have pdm (get it from the cheeseshop), then just do `pdm install` to install dependencies.

If you know how to reach me, I may be able to provide you with a remote for the `dvc` data.

## Fetching data

### Census

To fetch US Census data, get an API key. Copy the `config.default.json` file in the
repository and name it `config.json`. Enter your API key into the file.

Run the python `get_census_data.py` script. This fetches a selection of
data from the Data Profiles and Subjects tables of the American Community Survey.

### MassGIS layers

This data doesn't require any authentication - just run the `get_gis_layers.py` script.

## Referenced values

### US Census

- tracts

3681.01

3681.02

3682

3683

3684

3685

3686

3687

3688

3689.01

3689.02

3690

3691

- FIPS codes

MA = 25

Middlesex County = 017

### Massachusetts' specific codes

Waltham's city code = 308

- Residential building [types](https://www.mass.gov/files/documents/2016/08/wr/classificationcodebook.pdf)

10 Residences

101 ...... Single Family

102 ...... Condominium

103 ...... Mobile Home (includes land used for purpose
of a mobile home park)

104 ...... Two-Family

105 ...... Three-Family

106 ...... Accessory Land with Improvement - garage,
etc.

107 ...... (Intentionally left blank)

108 ...... (Intentionally left blank)

109 ...... Multiple Houses on one parcel (for example, a
single and a two-family on one parcel)

11 Apartments

111 ...... Four to Eight Units

112 ...... More than Eight Units

12 Non-Transient Group Quarters

121...... Rooming and Boarding Houses

122...... Fraternity and Sorority Houses

123...... Residence Halls or Dormitories

124...... Rectories, Convents, Monasteries

125...... Other Congregate Housing which includes
non-transient shared living arrangements
