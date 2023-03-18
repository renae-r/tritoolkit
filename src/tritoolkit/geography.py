from typing import Any, Optional
import warnings

import pandas as pd
import numpy as np
import geopandas as gpd

# TODO
# [] validation for lat and lon fields
# [] validaiton of TRI points - i.e. are tri facilities in the state and county the TRI data indicates?
# [] flag mis-matched geographies from above

class MissingCoordinatesWarning(Warning):
    pass


def dms_to_dd(dms_value: Any) -> float:
    """
    Utility function to convert degrees minutes seconds coordinates to decimal degrees.

    Args:
        dms_value: A degrees-minutes-seconds location value.

    Returns: The same value in decimal degrees.
    """

    # if the dms_value passed is nan, return nan
    try:
        # convert decimal degree value to string value
        if not isinstance(dms_value, str):
            dms_value = str(int(dms_value))
    except ValueError:
        return np.nan

    # break the dd_value string into 3 parts
    if dms_value[0] == "-":
        # if the string less than 7 digits, left pad it
        if len(dms_value) < 7:
            dms_value = dms_value.ljust(7, "0")
        degrees = int(dms_value[1:3])
        minutes = int(dms_value[3:5])
        seconds = int(dms_value[-2:])
        dd_value = -(degrees + (minutes / 60) + (seconds / 3600))
    else:
        # if the string less than 6 digits, left pad it
        if len(dms_value) < 6:
            dms_value = dms_value.ljust(6, "0")
        degrees = int(dms_value[:2])
        minutes = int(dms_value[2:4])
        seconds = int(dms_value[-2:])
        print(dms_value, degrees, minutes, seconds)
        dd_value = degrees + (minutes / 60) + (seconds / 3600)
    return dd_value


def to_geopandas_df(df: pd.DataFrame, 
                    lat_field: str, 
                    lon_field: str, 
                    dropna: bool = True):
    """
    Convert pandas data frame to geopandas data frame
    
    Args:
        df: pandas data frame containing latitude and longitude fields
        lat_field: Name of the column containing Latitude in df
        lon_field: Name of the column containing Longitude in df
        dropna: drop rows with missing lat or lon values. Default is True
    
    Returns:
        A geopandas data frame using lat_field and lon_field to generate geometry
    """
    # TODO: validation of contents of lat and lon field to make sure they are plausibly lat/lon values
    if dropna:
        missing_lat = len(df[(df[lat_field].isna() == True)])
        missing_lon = len(df[(df[lon_field].isna() == True)])
        df = df[(df[lat_field].isna() == False) & (df[lon_field].isna() == False)]
        warnings.warn(f"{missing_lat} missing values in {lat_field} and {missing_lon} missing values in {lon_field}. These rows will be dropped",
                      MissingCoordinatesWarning)

    gdf = gpd.GeoDataFrame(df,
                           geometry=gpd.points_from_xy(df[lon_field], 
                                                       df[lat_field]))
    return gdf


def tri_points_to_polygons(gdf: gpd.GeoDataFrame,
                           shape_file: str) -> gpd.GeoDataFrame:
    """
    A convenience method to perform a spatial join of TRI lat/lon point geometries
    with user-specified polygon geometries.

    Args:
        gdf: A geopandas data frame that contains point geometry of TRI facilities or release sites.
        shape_file: Path to a shape file that contains a polygon layer

    Returns: a geopandas GeoDataFrame with polygon geometry for polygons in the shape_file containing TRI points
    """
    polygons = gpd.read_file(shape_file)
    # if gdf crs is not defined, assume these are manual lat/lon, and assign WSG4
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    # set crs of point gdf to match the polygons
    gdf = gdf.to_crs(polygons.crs)
    # spatial join - polygons that contain points
    tri_polygons = gpd.sjoin(polygons, 
                             gdf, 
                             how="inner", 
                             predicate="contains")
    return tri_polygons