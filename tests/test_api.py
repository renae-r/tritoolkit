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
    Confirm that test extract submits properly
    """
    chem_str = "Dioxin%20and%20dioxin%2Dlike%20compounds"
    chem_info_table = Table("TRI_CHEM_INFO").filter_on_single_values(filter_dict={"CHEM_NAME": chem_str})

    # unpickle the test df
    with open(fixtures_path / "chem_info_dlc.pkl", "rb") as infile:
        extract = pickle.load(infile)

    assert extract.equals(chem_info_table)

