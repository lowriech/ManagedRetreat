import os
from utils import *
import geopandas as gpd
import pandas as pd
from config import *
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt


# TODO change this to be a package that lives outside of this project
class AbstractGeoHandler:

    """A parent handler for geospatial dataframes.
        This is intended to handle basic geodataframe operations."""
    def __init__(self, **kwargs):
        if "local_shp_path" in kwargs:
            self.local_shp_path = kwargs.get("local_shp_path")
            self.get_gdf()
        elif "gdf" in kwargs:
            self.local_shp_path = None
            self.gdf = kwargs.get("gdf")
        elif "dir" in kwargs:
            if "traverse_subdirs" in kwargs:
                self.local_shp_path = None
                self.get_gdf_by_directory(kwargs.get("dir"), kwargs.get("traverse_subdirs"))
            else:
                self.get_gdf_by_directory(kwargs.get("dir"))
        else:
            self.get_gdf()

    def get_gdf(self):
        """Search for the GDF locally, if not found look for a remote file.
        This will be overriden by subclasses to allow for remote fetching and such."""
        self.gdf = gpd.read_file(self.local_shp_path)

    def cut_data_by_values(self, keys):
        '''Filter a dataframe by specific values'''
        x = self.gdf
        for key, value in keys.items():
            x = x.loc[x[key] == value]
        self.gdf = x

    def create_spatial_index_fields(self):
        '''Potentially useful for spatial indexing and efficient calculation'''
        bounds = self.gdf["geometry"].bounds
        self.gdf["minx"] = bounds["minx"]
        self.gdf["maxx"] = bounds["maxx"]
        self.gdf["miny"] = bounds["miny"]
        self.gdf["maxy"] = bounds["maxy"]

    def cut_to_extent(self, extent):
        #TODO: try/except is currently implemented to handle empty dataframes.  Not optimal
        '''Takes an extent (lower left, upper right) and clips the GDF to these bounds'''
        lower_left, upper_right = extent
        extent_min_lon, extent_min_lat = lower_left
        extent_max_lon, extent_max_lat = upper_right
        try:
            c1 = self.gdf["geometry"].bounds["minx"] < extent_max_lon
            c2 = self.gdf["geometry"].bounds["maxx"] > extent_min_lon
            c3 = self.gdf["geometry"].bounds["miny"] < extent_max_lat
            c4 = self.gdf["geometry"].bounds["maxy"] > extent_min_lat
            self.gdf = self.gdf[c1][c2][c3][c4]
        except ValueError:
            pass

    def get_spatial_extent(self, buffer=0.01):
        self.create_spatial_index_fields()
        return ((min(self.gdf["minx"])-buffer, min(self.gdf["miny"])-buffer),
                (max(self.gdf["maxx"])+buffer, max(self.gdf["maxy"])+buffer))

    def get_gdf_by_directory(self, dir, traverse_subdirs=False):
        data = []
        for i in get_by_extension(dir, ".shp"):
            p = os.path.join(dir, i)
            data.append(gpd.read_file(p))
        if traverse_subdirs:
            for root, dirs, files in walk(dir):
                for d in dirs:
                    p = os.path.join(root, d)
                    for i in get_by_extension(p, ".shp"):
                        data.append(gpd.read_file(os.path.join(p, i)))
        self.gdf = pd.concat(data)


# TODO change this to be a package that lives outside of this project
class SimpleCensusSoVI:

    def __init__(self, config = SoVI_config):
        self.config = config
        self.raw_SoVI_variable_gdfs = self.csvs_to_gdf()
        self.pca = self.principal_component_analysis()

    def csvs_to_gdf(self):

        body = "ACS_17_5YR_{}_with_ann.csv"

        SoVIs = []

        for title, sheet_data in self.config.items():
            data = None
            for sheet_name, columns in sheet_data.items():
                p = os.path.join(CENSUS_TABLES, body.format(sheet_name))
                y = pd.read_csv(p)
                y = y[columns]
                y = y.set_index(columns[0])
                if data is None:
                    data = y
                else:
                    data = data.merge(y, right_index=True, left_index=True)
            for i in data.columns:
                data[i] = pd.to_numeric(data[i], errors="coerce")
            data = data.dropna()
            SoVIs.append({title: data})
        return SoVIs

    def principal_component_analysis(self):

        pcas = []
        for i in self.raw_SoVI_variable_gdfs:
            for title, raw_vars in i.items():
                features = raw_vars.columns
                x = raw_vars.loc[:, features].values
                x = StandardScaler().fit_transform(x)
                data = pd.DataFrame(x, columns=features, index=raw_vars.index)

                x = data.loc[:, data.columns].values
                pca = PCA()
                principalComponents = pca.fit_transform(x)
                df = pd.DataFrame(data=principalComponents,
                                  index=raw_vars.index)
                print(len(df.columns))

                columns = ["{} ".format(title) + str(i) for i in range(len(df.columns))]
                print(columns)
                pc_df = pd.DataFrame(data=principalComponents,
                                     columns=columns,
                                     index=raw_vars.index)
                pcas.append({"TITLE": title,
                             "vars": raw_vars.columns,
                             "PCs": pca,
                             "PC_df": pc_df})
        return pcas


def init_buildings(buildings_path=BUILDINGS_PATH, centroid=True):
    #Initiate based on the first buildings .shp found in the buildings path folder
    buildings = AbstractGeoHandler(
        local_shp_path=os.path.join(buildings_path, get_by_extension(buildings_path, ".shp")[0])
    )
    #For performance reasons
    if centroid is True:
        buildings.gdf["geometry"] = buildings.gdf["geometry"].centroid

    buildings.gdf = buildings.gdf.to_crs({'init': 'epsg:4326'})
    buildings.gdf = buildings.gdf[["type", "geometry"]]
    return buildings


def init_sea_levels(mean, sd, slr_path=SLR_PATH, simplify=0.003):
    data = dict()
    for root, dirs, files in walk(slr_path):
        for d in dirs:
            p = os.path.join(root, d)
            for i in get_by_extension(p, ".shp"):
                data[d] = os.path.join(p, i)
    print(data)

    slr_mappings = {
        "Baseline": 0,
        "SLR1": 1,
        "SLR2": 2,
        "SLR3": 3,
        "SLR4": 4,
        "SLR5": 5,
        "SLR6": 6
    }

    percentage_mapping = get_normal_distribution_mappings(mean, sd, slr_mappings.values())

    data = {key: AbstractGeoHandler(local_shp_path=value) for key, value in data.items()}
    for key, geo_handler in data.items():
        geo_handler.gdf = geo_handler.gdf.to_crs({'init': 'epsg:4326'})[["geometry"]]
        geo_handler.gdf["SLR_ft"] = slr_mappings[key]
        geo_handler.gdf["Likelihood"] = percentage_mapping[slr_mappings[key]]
    geo_handler.gdf["geometry"] = geo_handler.gdf["geometry"].simplify(tolerance=simplify)
    total_geo_handler = AbstractGeoHandler(gdf=pd.concat([v.gdf for k, v in data.items()]))
    return total_geo_handler


def init_census_geo(path=CENSUS_GEO):
    geo = AbstractGeoHandler(local_shp_path=os.path.join(path, get_by_extension(path, ".shp")[0]))
    geo.gdf = geo.gdf.set_index("ZCTA5CE10")
    geo.gdf = geo.gdf[["geometry"]]
    geo.gdf = geo.gdf.to_crs({'init': 'epsg:4326'})
    geo.gdf.index = pd.to_numeric(geo.gdf.index)
    return geo


def init_zillow(path=ZILLOW_PATH):
    zillow = pd.read_csv(path)[["RegionName", "Zhvi"]]
    zillow = zillow.set_index("RegionName")
    return zillow


class Analysis:

    def __init__(self, sea_level_mean=91/2.54/12, sea_level_sd=30/2.54/12):
        self.census_sovi = SimpleCensusSoVI()

        self.slr = init_sea_levels(sea_level_mean, sea_level_sd)
        self.extent = self.slr.get_spatial_extent()

        self.buildings = init_buildings()
        self.buildings.cut_to_extent(self.extent)

        self.census_geo = init_census_geo()

        self.census_geo.cut_to_extent(self.extent)

        for i in self.census_sovi.pca:
            self.census_geo.gdf = self.census_geo.gdf.merge(
                i["PC_df"], left_index=True, right_index=True
            )

        zillow = init_zillow()
        self.census_geo.gdf = self.census_geo.gdf.merge(
            zillow, left_index=True, right_index=True
        )

        self.census_geo.gdf["ZCTA"] = self.census_geo.gdf.index

        self.buildings_x_slr = gpd.sjoin(
            self.buildings.gdf[["geometry", "type"]],
            self.slr.gdf[["geometry", "SLR_ft", "Likelihood"]],
            how="inner", op="intersects"
        )

        self.buildings_x_slr = self.buildings_x_slr.drop(columns="index_right")

        self.buildings_x_slr_x_census = gpd.sjoin(
            self.buildings_x_slr,
            self.census_geo.gdf,
            how="inner", op="intersects"
        )

        self.buildings_x_slr_x_census = self.buildings_x_slr_x_census.drop(columns="index_right")

        self.earliest_encountered_slr = self.parse_earliest_encountered_slr()

        self.marginal_buildings_at_risk, self.marginal_value_at_risk = self.find_marginal_risk()
        self.marginal_social_vulnerability = self.find_social_vulnerability()

    def parse_earliest_encountered_slr(self):

        self.buildings_x_slr_x_census["idx"] = self.buildings_x_slr_x_census.index

        agg = self.buildings_x_slr_x_census[["SLR_ft", "idx"]].groupby(by=["idx"])

        earliest_encountered_slr = agg.min()
        earliest_encountered_slr["idx"] = earliest_encountered_slr.index
        earliest_encountered_slr = earliest_encountered_slr[["SLR_ft"]].merge(
            self.buildings_x_slr_x_census,
            on=["SLR_ft", "idx"],
            how="inner"
        )

        return earliest_encountered_slr

    def find_marginal_risk(self):

        earliest_encountered_slr = self.earliest_encountered_slr

        earliest_encountered_slr["EMV"] = earliest_encountered_slr["Zhvi"] * earliest_encountered_slr["Likelihood"]

        agg = earliest_encountered_slr[["SLR_ft", "Zhvi", "EMV"]].groupby(by="SLR_ft")
        marginal_buildings_at_risk = agg["Zhvi"].count()
        marginal_value_at_risk = agg["Zhvi", "EMV"].sum()
        return marginal_buildings_at_risk, marginal_value_at_risk

    def find_social_vulnerability(self):

        earliest_encountered_slr = self.earliest_encountered_slr

        earliest_encountered_slr["poverty_rank"] = earliest_encountered_slr["Poverty and Unemployment 0"].rank(pct=True)

        def func(row):
            if row['poverty_rank'] <= 0.33:
                return "1"
            elif row['poverty_rank'] <= 0.67:
                return "2"
            else:
                return "3"

        earliest_encountered_slr["tercile"] = earliest_encountered_slr.apply(func, axis=1)
        agg = earliest_encountered_slr[["SLR_ft", "tercile", "idx"]].groupby(by=["SLR_ft", "tercile"])
        marginal_vulnerability = agg.count()

        return marginal_vulnerability


if __name__ == "__main__":
    rcp2_6 = Analysis(24/2.54/12, 5/2.54/12)
    rcp4_5 = Analysis(26/2.54/12, 5/2.54/12)
    rcp8_5 = Analysis(29/2.54/12, 6/2.54/12)



