.. tritoolkit introduction

.. currentmodule:: tritoolkit

Getting Started
===============

Installation
------------

This package requires that you have at least Python 3.8 installed.

Install with ``pip`` from github:

.. code:: bash

    pip install git+https://github.com/renae-r/tritoolkit.git


Retrieving TRI Data
-------------------

To use ``tritoolkit`` effectively, users should be basically familiar with the `TRI database model <https://www.epa.gov/enviro/tri-model>`_.

Use the :class:`tritoolkit.api.Table` class to retrieve data from a specifc table in the TRI database and return it as a Pandas data frame. The code snippet below shows how to retrieve the entry in the TRI_CHEM_INFO table for lead.

.. code:: python

    from tritoolkit import Table

    chem_info = Table("TRI_CHEM_INFO")

    lead_info = chem_info.filter({"CHEM_NAME": "Lead"})

The :meth:`.filter()` method can be used to retrieve a specific subset of records from a given database table by passing a dictionary of filter variables and conditions.

The code snippet below returns a data frame containing records for all TRI reporting forms that reported releases of Dioxins and dioxin-like compounds from the year 2020.

.. code:: python

    from tritoolkit import Table

    chem_info = Table("TRI_CHEM_INFO")
    forms = Table("TRI_REPORTING_FORM")

    # Dioxin and dioxin-like compound entry
    dlc_info = chem_info.filter({"CHEM_NAME": "Dioxin and dioxin-like compounds"})
    # pull out TRI chem id number
    dlc_id = chem_info["TRI_CHEM_ID"][0]
    # retrieve forms reporting Dioxin and dioxin-like compounds from 2020
    dlc_forms = forms.filter({"TRI_CHEM_ID": chem_id,
                              "REPORTING_YEAR": "2020"})


Working with TRI Geography
--------------------------

``tritoolkit`` offers several convenience methods for working with geographic information found in the TRI database, specifically, lat/lon coordinates of facilities and releases.

See :ref:`geography` for more information.