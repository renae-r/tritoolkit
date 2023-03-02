from io import StringIO
from functools import wraps
from typing import Optional

import pandas as pd
import requests
from requests.models import Response
from joblib import Parallel, delayed
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
        base_url: str = 'https://data.epa.gov/efservice',
        num_retries: int = 3,
        session: Optional[requests.Session] = None,
    ):
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
        """GET a request from the IPUMS API"""
        return self.request("get", *args, **kwargs)
    

class Table(TriApiClient):
    def __init__(
        self,
        name
    ):
        super().__init__()
        self.name = name
        self.table_url = f"{self.base_url}/{self.name.upper()}"
        
    @property
    def rows(self):
        count = self.get(f"{self.table_url}/COUNT/JSON")
        total_rows = count.json()[0]["TOTALQUERYRESULTS"]
        return total_rows
    
    def _divide_rows_into_chunks(self, l, n):
        # looping till length l
        for i in range(0, len(l), n):
            l2 = l[i:i + n]
            yield (l2[0], l2[-1])
        
    # In theory I should be able to do all of this with json returns,
    # but the /JSON option is giving me fits and I don't know why,
    # but CSV is working so I am rolling with that for now.
    def _isolate_csv_header(self, csv_string_list):
        # grab the first item in the list
        first = csv_string_list[0]
        # split it along new lines
        first_list = first.split("\n")
        # keep the first item to use as a header
        head = first_list[0]
        # now grab everything after the header for
        # every item in the list
        body_list = ["\n".join(text.split("\n")[1:]) for text in csv_string_list]
        body = "".join(body_list)
        serialized_csv = f"{head}\n{body}"
        return serialized_csv
    
    def _csv_string_to_df(self, csv_string):
        # make it a table
        table_data = StringIO(csv_string)
        table_df = pd.read_csv(table_data, sep=",")
        return table_df
        
    def get_row_range(self, row_min, row_max):
        # get table section
        csv_str = self.get(f"{self.table_url}/rows/{row_min}:{row_max}/CSV/")
        csv_str.raise_for_status()
        # put it into a data frame
        table_df = self._csv_string_to_df(csv_str.text)   
        return table_df
    
    def filter_on_single_values(self, filter_dict={}):
        updated_url = [self.table_url]
        # need better error handling for non-existant columns
        for col in filter_dict.keys():
            updated_url.append(f"{col.upper()}/{filter_dict[col.upper()]}")
        updated_url.append("CSV")
        filtered_url = "/".join(updated_url)
        csv_str = self.get(filtered_url).text
        table_df = self._csv_string_to_df(csv_str)
        return table_df
    
    def filter_on_multiple_values(self, filter_column, filter_values):
        max_row = self.rows
        # break the range of maximum row into chunks of 10k
        row_tuples = list(self._divide_rows_into_chunks(range(0, max_row + 1), 10000))
        # use all but 2 cpu
        df_segments = Parallel(n_jobs=-3, verbose=1)\
                                 (delayed(self.get_row_range)
                                         (str(i[0]), str(i[1])) 
                                  for i in row_tuples)
        df = pd.concat(df_segments, ignore_index=True)
        filtered_df = df[df[filter_column].isin(filter_values)]
        return filtered_df