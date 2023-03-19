import time
import subprocess
import pickle
from pathlib import Path

import pandas as pd

import pytest
import vcr

from tritoolkit import api
from tritoolkit.api import (
    TriApiClient,
    Table,
)
from tritoolkit.api.exceptions import (
    TriApiException,
)


@pytest.fixture(scope="module")
def mock_api() -> str:
    # TODO: Would be good to randomly assign a port and return it
    p = subprocess.Popen(
        ["uvicorn", "tests.mock_api:app", "--host", "127.0.0.1", "--port", "8989"]
    )
    time.sleep(1)  # Give it enough time to warm up
    try:
        yield "http://127.0.0.1:8989/extracts"
    finally:
        p.kill()


@pytest.fixture(scope="function")
def api_client(environment_variables, mock_api: str) -> TriApiClient:
    client = TriApiClient()
    client.base_url = mock_api
    return client


@pytest.mark.vcr
def test_table_filter_on_single_value(fixtures_path: Path):
    """
    Confirm that table is filtered on single value
    """
    # one single value
    chem_str = "Dioxin%20and%20dioxin%2Dlike%20compounds"
    chem_info_table = Table("TRI_CHEM_INFO").filter(filters={"CHEM_NAME": chem_str})

    # unpickle the test df
    with open(fixtures_path / "chem_info_dlc.pkl", "rb") as infile:
        chem_info_pkl = pickle.load(infile)

    assert chem_info_pkl.equals(chem_info_table)

    reporting_forms = Table("TRI_REPORTING_FORM").filter(
        filters={"TRI_CHEM_ID": "N150", "REPORTING_YEAR": "2021"}
    )
    # multiple single values# unpickle the test df
    with open(fixtures_path / "reporting_forms_dlc_2021.pkl", "rb") as infile:
        reporting_forms_pkl = pickle.load(infile)

    assert reporting_forms_pkl.equals(reporting_forms)


@pytest.mark.vcr
def test_table_filter_on_multiple_values(fixtures_path: Path):
    """
    Confirm that table is filtered on multiple values
    """
    # unpickle the list of test facilities
    with open(fixtures_path / "facilities_list.pkl", "rb") as infile:
        facilities_list = pickle.load(infile)

    dioxin_facilities = Table("TRI_FACILITY").filter(
        filters={"TRI_FACILITY_ID": facilities_list}
    )

    # unpickle the test df
    with open(fixtures_path / "facilities_dlc_2017_2021.pkl", "rb") as infile:
        dioxin_facilities_pkl = pickle.load(infile)

    assert dioxin_facilities_pkl.equals(dioxin_facilities)
