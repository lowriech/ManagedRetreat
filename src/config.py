import os

HOME_PATH = "/Users/christopherjlowrie/Repos/ManagedRetreat"

DATA_PATH = os.path.join(HOME_PATH, "data")

SLR_PATH = os.path.join(DATA_PATH, "slr")

INFRA_PATH = os.path.join(DATA_PATH, "infrastructure")

ZCTA_PATH = os.path.join(DATA_PATH, "zctas")

CENSUS_TABLES = os.path.join(ZCTA_PATH, "tables")

CENSUS_GEO = os.path.join(ZCTA_PATH, "geography")

BUILDINGS_PATH = os.path.join(INFRA_PATH, "osm-alabama/buildings")

ZILLOW_PATH = os.path.join(DATA_PATH, "zillow/zillow_summary.csv")

TMP_DIR = os.path.join(DATA_PATH, "tmp")


SoVI_config = {
    "Female" :
        {
            "S1101": [
                "Id2",
                "Female householder, no husband present, family household; Estimate; Average household size",
                "Female householder, no husband present, family household; Estimate; FAMILIES - Total families"
            ]
        },
    "Poverty and Unemployment":
        {
            "S2301": [
                "Id2",
                "Unemployment rate; Estimate; Population 16 years and over"
            ],
            "S1701": [
                "Id2",
                "Below poverty level; Estimate; Population for whom poverty status is determined"
            ]
        }
}

