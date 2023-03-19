import pytest
import pickle
from pathlib import Path

import numpy as np

from tritoolkit import geography


def test_dms_to_dd():
    """test the degrees-minutes-seconds to decimal degrees conversion"""
    assert geography.dms_to_dd(324528.0) == 32.757777777777775

    assert geography.dms_to_dd(np.nan) is np.nan

    assert geography.dms_to_dd(-324528.0) == -32.757777777777775

    assert geography.dms_to_dd(1005305.0) == 100.88472222222222


def test_to_gopandas_df(fixtures_path: Path):
    # unpickle the test df
    with open(fixtures_path / "dlc_facilities.pkl", "rb") as infile:
        dlc_facilities_pkl = pickle.load(infile)

    with open(fixtures_path / "dlc_facilities_geo.pkl", "rb") as infile:
        dlc_facilities_geo_pkl = pickle.load(infile)

    dlc_facilities_geo = geography.to_geopandas_df(
        dlc_facilities_pkl, "PREF_LATITUDE", "PREF_LONGITUDE_NEG"
    )
    assert dlc_facilities_geo.equals(dlc_facilities_geo_pkl)


def test_tri_points_to_polygons(fixtures_path: Path):
    # unpickle the test df - facilites in mn geodf
    with open(fixtures_path / "nd_facilities_geo.pkl", "rb") as infile:
        nd_facilities_geo_pkl = pickle.load(infile)

    # mn counties w/ facilities
    with open(fixtures_path / "nd_counties_facilities.pkl", "rb") as infile:
        nd_counties_facilities_pkl = pickle.load(infile)

    nd_facilities_counties = geography.tri_points_to_polygons(
        nd_facilities_geo_pkl, fixtures_path / "nd_counties_all.zip"
    )
    print(len(nd_facilities_counties))
    print(len(nd_counties_facilities_pkl))
    print(nd_facilities_counties.head())
    print(nd_counties_facilities_pkl.head())
    assert nd_facilities_counties.equals(nd_counties_facilities_pkl)
