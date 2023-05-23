
import json
import os
from census import Census
import pandas as pd
from tqdm import tqdm

os.makedirs("data/census", exist_ok=True)

config = json.load(open("config.json"))

DATA_PROFILES_CENSUS_DF_PATH = "data/census/data_profiles_census_df.csv"
SUBJECT_CENSUS_DF_PATH = "data/census/subject_census_df.csv"
DECENNIAL_CENSUS_DF_PATH = "data/census/decennial_census_df.csv"

MA_FIPS = "25"
MIDDLESEX_FIPS = "017"

WALTHAM_CENSUS_TRACTS = [
    "3681.01",
    "3681.02",
    "3682",
    "3683",
    "3684",
    "3685",
    "3686",
    "3687",
    "3688",
    "3689.01",
    "3689.02",
    "3690",
    "3691",
]


# census fields
# ref. https://api.census.gov/data.html

# fields ending in E are estimates (i.e. a count)
# fields ending in P are percentages in the geography that fall into that bucket

data_profiles_census_fields = [
    # Estimate!!INCOME AND BENEFITS (IN 2020 INFLATION-ADJUSTED DOLLARS)!!Total households!!Less than $10,000
    "DP03_0052E",
    "DP03_0052PE",
    # Estimate!!INCOME AND BENEFITS (IN 2020 INFLATION-ADJUSTED DOLLARS)!!Total households!!$10,000 to $14,999
    "DP03_0053E",
    "DP03_0053PE",
    # Estimate!!INCOME AND BENEFITS (IN 2020 INFLATION-ADJUSTED DOLLARS)!!Total households!!$15,000 to $24,999
    "DP03_0054E",
    "DP03_0054PE",
    # Estimate!!INCOME AND BENEFITS (IN 2020 INFLATION-ADJUSTED DOLLARS)!!Total households!!$25,000 to $34,999
    "DP03_0055E",
    "DP03_0055PE",
    # Estimate!!INCOME AND BENEFITS (IN 2020 INFLATION-ADJUSTED DOLLARS)!!Total households!!$35,000 to $49,999
    "DP03_0056E",
    "DP03_0056PE",
    # Estimate!!INCOME AND BENEFITS (IN 2020 INFLATION-ADJUSTED DOLLARS)!!Total households!!$50,000 to $74,999
    "DP03_0057E",
    "DP03_0057PE",
    # Estimate!!INCOME AND BENEFITS (IN 2020 INFLATION-ADJUSTED DOLLARS)!!Total households!!$75,000 to $99,999
    "DP03_0058E",
    "DP03_0058PE",
    # Estimate!!INCOME AND BENEFITS (IN 2020 INFLATION-ADJUSTED DOLLARS)!!Total households!!$100,000 to $149,999
    "DP03_0059E",
    "DP03_0059PE",
    # Estimate!!INCOME AND BENEFITS (IN 2020 INFLATION-ADJUSTED DOLLARS)!!Total households!!$150,000 to $199,999
    "DP03_0060E",
    "DP03_0060PE",
    # Estimate!!INCOME AND BENEFITS (IN 2020 INFLATION-ADJUSTED DOLLARS)!!Total households!!$200,000 or more
    "DP03_0061E",
    "DP03_0061PE",
    # Estimate!!INCOME AND BENEFITS (IN 2020 INFLATION-ADJUSTED DOLLARS)!!Total households!!Median household income (dollars)
    "DP03_0062E",
    # Estimate!!GROSS RENT!!Occupied units paying rent!!Median (dollars)
    "DP04_0134E",
    # Estimate!!VEHICLES AVAILABLE!!Occupied housing units
    "DP04_0057E",
    # Estimate!!VEHICLES AVAILABLE!!Occupied housing units!!No vehicles available
    "DP04_0058E",
    # Estimate!!VEHICLES AVAILABLE!!Occupied housing units!!1 vehicle available
    "DP04_0059E",
    # Estimate!!VEHICLES AVAILABLE!!Occupied housing units!!2 vehicles available
    "DP04_0060E",
    # Estimate!!VEHICLES AVAILABLE!!Occupied housing units!!3 or more vehicles available
    "DP04_0061E"
]

subject_census_fields = [
    # Estimate!!Total!!Total population!!SELECTED AGE CATEGORIES!!18 years and over
    "S0101_C01_026E"
]

decennial_census_fields = [
    # P1 RACE table fields
    *[f"P1_{n:03}N" for n in range(1, 72)]
]


CENSUS_API_KEY = config["census_api_key"]
census_api = Census(CENSUS_API_KEY)

print("Data Profile tables fields")

# FYI - this takes several minutes to run... is it possible to query for more than one tract at a time?
if not os.path.exists(DATA_PROFILES_CENSUS_DF_PATH):
    data_profiles_census_df = pd.DataFrame(index=WALTHAM_CENSUS_TRACTS, columns=data_profiles_census_fields)

    for tract in tqdm(WALTHAM_CENSUS_TRACTS, desc="tracts"):
        for variable in tqdm(data_profiles_census_fields, desc="fields", leave=False):
            # make tract url friendly
            tract_url = str(int(float(tract)*100))

            value = census_api.acs5dp.state_county_tract(('NAME', variable), MA_FIPS, MIDDLESEX_FIPS, tract_url)

            data_profiles_census_df.at[tract, variable] = value[0][variable]

    data_profiles_census_df.index.name = "tract"
    data_profiles_census_df.to_csv(DATA_PROFILES_CENSUS_DF_PATH)


print("Subject table fields")

if not os.path.exists(SUBJECT_CENSUS_DF_PATH):
    subject_census_df = pd.DataFrame(index=WALTHAM_CENSUS_TRACTS, columns=subject_census_fields)

    for tract in tqdm(WALTHAM_CENSUS_TRACTS, desc="tracts"):
        for variable in tqdm(subject_census_fields, desc="fields", leave=False):
            # make tract url friendly
            tract_url = str(int(float(tract)*100))

            value = census_api.acs5st.state_county_tract(('NAME', variable), MA_FIPS, MIDDLESEX_FIPS, tract_url)

            subject_census_df.at[tract, variable] = value[0][variable]

    subject_census_df.index.name = "tract"
    subject_census_df.to_csv(SUBJECT_CENSUS_DF_PATH)
    

print("Decennial census fields")

if not os.path.exists(DECENNIAL_CENSUS_DF_PATH):
    decennical_census_df = pd.DataFrame(index=WALTHAM_CENSUS_TRACTS, columns=decennial_census_fields)
    
    for tract in tqdm(WALTHAM_CENSUS_TRACTS, desc="tracts"):
        for variable in tqdm(decennial_census_fields, desc="fields", leave=False):
            # make tract url friendly
            tract_url = str(int(float(tract)*100))
            
            value = census_api.pl.state_county_tract(('NAME', variable), MA_FIPS, MIDDLESEX_FIPS, tract_url)
            
            decennical_census_df.at[tract, variable] = value[0][variable]
            
    decennical_census_df.index.name = "tract"
    decennical_census_df.to_csv(DECENNIAL_CENSUS_DF_PATH)
    
