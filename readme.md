
# ETL for Waltham, MA specific data

This project runs backend services that fetch data for various analyses on the built environment of Waltham, MA.

## Services

This app contains some containerized services that fetch data, provide an MCP server with select access to GIS functions,
and a PostGIS database for GIS queries.

## Instructions

Dependencies are managed with `uv`. Services should be testable on their own outside of a container, ideally. Some services
need API credentials to access, see the `config.default.json` file for an example and create a `config.json` with your creds
when you have them.

## Fetching data

### Census

To fetch US Census data, get an API key. Copy the `config.default.json` file in the
repository and name it `config.json`. Enter your API key into the file.

Run the python `get_census_data.py` script. This fetches a selection of
data from the Data Profiles and Subjects tables of the American Community Survey.

See [https://api.census.gov/data.html] for the actual tables and fields that are available.

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
