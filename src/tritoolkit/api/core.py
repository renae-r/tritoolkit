from io import StringIO
from functools import wraps
from typing import Optional, Union, Dict, List
import warnings

import pandas as pd
import requests
from requests.models import Response
from joblib import Parallel, delayed
from tqdm import tqdm

from ..__version__ import __version__
from .exceptions import (
    TransientTriApiException,
    TriApiError,
)


def retry_on_transient_error(func):
    """
    Retry a request up to self.num_retries times. If it exits with a
    ``TransientIpumsApiException``, then retry, else just immediately ``raise``
    """

    @wraps(func)
    def wrapped_func(self, *args, **kwargs):
        for _ in range(self.num_retries - 1):
            try:
                return func(self, *args, **kwargs)
            except TransientTriApiException:
                pass
        return func(self, *args, **kwargs)

    return wrapped_func


class TriApiClient:
    def __init__(
        self,
        num_retries: int = 3,
        session: Optional[requests.Session] = None,
        base_url: Optional[str] = "https://data.epa.gov/efservice",
    ):
        """
        Class for retrieving TRI data via API

        Args:
            num_retries: number of times a request will be retried before
                        raising `TransientTriApiException`
            session: requests session object
            base_url: Envirofacts TRI url

        """
        self.num_retries = num_retries
        self.base_url = base_url
        self.session = session or requests.session()

    @retry_on_transient_error
    def request(self, method: str, *args, **kwargs) -> requests.Response:
        """
        Submit a request to the (envirofacts) TRI API
        """
        try:
            response = self.session.request(method, *args, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as http_err:
            raise TriApiError(f"An error occured: {http_err}")

    def get(self, *args, **kwargs) -> requests.Response:
        """GET a request from the TRI API"""
        return self.request("get", *args, **kwargs)
        

class Table(TriApiClient):
    def __init__(
        self,
        name: str = None,
    ):
        """
        Class for retrieving and filtering TRI database tables via API

        Args:
            name: The name of a table in the TRI database
        """
        super().__init__()
        self.name = name
        self.table_url = f"{self.base_url}/{self.name.upper()}"
        self.rows = self._get_rows()
        self.segments = list(
            self._divide_rows_into_chunks(range(0, self.rows + 1), 10000)
        )

    def _get_rows(self) -> int:
        count = self.session.get(f"{self.table_url}/COUNT/JSON")
        total_rows = count.json()[0]["TOTALQUERYRESULTS"]
        return total_rows

    def _divide_rows_into_chunks(self, l: List, n: int):
        # looping till length l
        for i in range(0, len(l), n):
            l2 = l[i : i + n]
            yield (l2[0], l2[-1])

    # In theory I should be able to do all of this with json returns,
    # but the /JSON option is causing internal server errors and I don't know why,
    # but CSV is working so I am rolling with that for now.
    def _csv_string_to_df(self, csv_string: str) -> pd.DataFrame:
        # make it a table
        table_data = StringIO(csv_string)
        # skip bad lines for now
        # TODO: incorporate database schema info to be able to specify
        # column names and retain bad/incomplete lines. Test on Forms
        table_df = pd.read_csv(table_data, sep=",", on_bad_lines="skip")
        return table_df

    def get_row_range(self, row_min: str, row_max: str, url: str = None):
        """
        Retrieve a specific set of rows from the table.

        Args:
            row_min: first row in the range as a string
            row_max: last row in the range as a string; must be <= row_min + 10000
            url: optional url specification

        Returns: A pandas data frame with the requested table rows
        """
        # if url not specified, default standard table url
        if url is None:
            _url = f"{self.table_url}/rows/{row_min}:{row_max}/CSV/"
        else:
            # if url ends with CSV, chop that off
            url_list = url.split("/")
            if url_list[-1] == "CSV":
                # add in the row bits
                url_list[-1] = f"rows/{row_min}:{row_max}/CSV/"
            else:
                url_list.append(f"rows/{row_min}:{row_max}/CSV/")
            _url = "/".join(url_list)
        # get table section
        csv_str = self.session.get(f"{_url}")
        # csv_str.raise_for_status()
        # put it into a data frame
        table_df = self._csv_string_to_df(csv_str.text)
        return table_df
    
    def all_rows(self, url: Optional[str] = None) -> pd.DataFrame:
        """
        Retrieves all rows in the table

        Args:
            url: optional url specification

        Returns: A pandas data frame containing the entire table.
        """
        if self.rows < 10001:
            df = self.get_row_range(0, self.rows, url)
        else:
            # use all but 2 cpu
            df_segments = Parallel(n_jobs=-3)(
                delayed(self.get_row_range)(str(i[0]), str(i[1]), url)
                for i in tqdm(self.segments)
            )
            df = pd.concat(df_segments, ignore_index=True)
        return df
    
    def _fix_filter_strings(self, filter_value: str) -> str:
        # replace spaces with %20
        fixed_filter_value = filter_value.replace(" ", "%20")
        # replace dashes with %2D
        fixed_filter_value = fixed_filter_value.replace("-", "%2D")
        return fixed_filter_value

    def filter(self, filters: Dict[str, Union[str, List[str]]] = {}) -> pd.DataFrame:
        """
        Select rows in the table that meet specific conditions. If multiple filter
        conditions are specified, the returned table will contain only rows for which
        all conditions are True.

        Args:
            filters: A dictionary of filter conditions where keys are table column names
                     and values are table column values to retain.

        Returns: A pandas data frame of the filtered rows
        """
        # split filters into strings and lists
        single_filters = [f for f in filters.keys() if isinstance(filters[f], str)]
        list_filters = [f for f in filters.keys() if isinstance(filters[f], list)]
        # first assemble url based on single filters
        updated_url = [self.table_url]
        # TODO: better error handling for non-existant columns
        for col in single_filters:
            # fix strings for url
            filter_value = self._fix_filter_strings(filters[col.upper()])
            updated_url.append(f"{col.upper()}/{filter_value}")
        updated_url.append("CSV")
        filtered_url = "/".join(updated_url)
        csv_str = self.session.get(filtered_url).text
        table_df = self._csv_string_to_df(csv_str)
        # if the table has exactly 10001 records, that means that
        # the request maxed out the number of rows that could be requested
        # in this case, we'll grab and filter the whole table...
        # Same deal if the first return is empty (i.e. only list type filters
        # were specified and none of those values were found in the first return)
        # This also falls down if bad rows are dropped when the serialized csv is
        # converted to a data frame...the request is maxed out, but fewer than 10001
        # rows in the df...
        if len(table_df.index) == 10001 or len(table_df.index) == 0:
            table_df = self.all_rows(filtered_url)
        # once we're sure we have all rows required from the single-value filters
        # filter the resulting data frame based on the list filters
        for col in list_filters:
            # no need to modify filter strings in the list case
            # as these aren't actually going in a url
            table_df = table_df[table_df[col].isin(filters[col])]
        return table_df
