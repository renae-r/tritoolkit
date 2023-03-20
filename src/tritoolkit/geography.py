from typing import Any, Optional, Dict
import warnings

import pandas as pd
import numpy as np
import geopandas as gpd
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable

# TODO
# [] validation for lat and lon fields
# [] validaiton of TRI points - i.e. are tri facilities in the state and county the TRI data indicates?
# [] flag mis-matched geographies from above


class MissingCoordinatesWarning(Warning):
    pass


class RetriesExhaustedWarning(Warning):
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
    # maximum string length is 8
    # 1 for the -, 3 for d, 2 for m, 2 for s
    if len(dms_value) < 8:
        dms_value = dms_value.zfill(8)
    if "-" in dms_value:
        dms_value = dms_value.replace("-", "0")
        degrees = int(dms_value[:4])
        minutes = int(dms_value[4:6])
        seconds = int(dms_value[-2:])
        dd_value = - (degrees + (minutes / 60) + (seconds / 3600))
    else:
        degrees = int(dms_value[:4])
        minutes = int(dms_value[4:6])
        seconds = int(dms_value[-2:])
        dd_value = degrees + (minutes / 60) + (seconds / 3600)
    return dd_value


def to_geopandas_df(
    df: pd.DataFrame, lat_field: str, lon_field: str, dropna: bool = True
):
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
        warnings.warn(
            f"{missing_lat} missing values in {lat_field} and {missing_lon} missing values in {lon_field}. These rows will be dropped",
            MissingCoordinatesWarning,
        )

    gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df[lon_field], df[lat_field])
    )

    # set crs
    gdf.set_crs(epsg=4326, inplace=True)
    return gdf


def tri_points_to_polygons(gdf: gpd.GeoDataFrame, shape_file: str) -> gpd.GeoDataFrame:
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
    tri_polygons = gpd.sjoin(polygons, gdf, how="inner", predicate="contains")
    return tri_polygons


def geocode_from_raw_address(address_string: str, geolocator_obj: Nominatim, attempt=1, num_retries: int =5):
    """
    Convenience method for geocoding address strings.

    Args:
        address_string: Address
        geolocator_obj: A geopy Nominatim geolocator object
        attempt: Current attempt to connect to Geocoder. Always set to 1
        num_retries: The number of attempts to reconnect when the Geocoder is unavailable. Defaults to 5.

    Returns:
        Geocoder response. In the event no response can be reached, returns NaN
    """
    geocode = RateLimiter(
        geolocator_obj.geocode,
        min_delay_seconds=1,
        max_retries=0,
        swallow_exceptions=False,
    )
    try:
        location = geocode(address_string)
        return (location.latitude, location.longitude)
    except GeocoderUnavailable:
        if attempt > num_retries:
            warnings.warn(
                f"!! RAN OUT OF RETRIES: {address_string}", RetriesExhaustedWarning
            )
        if attempt <= num_retries:
            return geocode_from_raw_address(
                address_string, geolocator_obj, attempt=attempt + 1
            )
        # raise
    except AttributeError:
        # addresses not found returned as none
        return None
    except Exception as exec:
        return np.nan


def geocoder_wrapper(address_components: Dict[str, str]):
    """
    Convenience method to pass a set of address parts to `geocode_from_raw_address()`.

    Args:
        address_components: Dictionary of address parts, such as street address, city, state, etc.

    Returns:
        geopy location object
    """
    geolocator = Nominatim(user_agent="tritoolkit")
    address_string = " ".join(
        [
            address_components["STREET_ADDRESS"],
            address_components["CITY_NAME"],
            address_components["COUNTY_NAME"],
            address_components["STATE_ABBR"],
            address_components["ZIP_CODE"],
        ]
    )
    location = geocode_from_raw_address(address_string, geolocator)
    # if location not found, try without county
    if location is None:
        address_string = " ".join(
            [
                address_components["STREET_ADDRESS"],
                address_components["CITY_NAME"],
                address_components["STATE_ABBR"],
                address_components["ZIP_CODE"],
            ]
        )
        location = geocode_from_raw_address(address_string, geolocator)
    # if location still not found, try without cardinal directions in street address
    if location is None and address_components["STREET_ADDRESS"].strip()[-2:] in [
        "NE",
        "SE",
        "NW",
        "SW",
    ]:
        address_string = " ".join(
            [
                address_components["STREET_ADDRESS"][:-3],
                address_components["CITY_NAME"],
                address_components["COUNTY_NAME"],
                address_components["STATE_ABBR"],
                address_components["ZIP_CODE"],
            ]
        )
        location = geocode_from_raw_address(address_string, geolocator)
    return location
