.. tritoolkit documentation master file

What is tritoolkit?
-------------------

``tritoolkit`` is a Python library for interacting with the Environmental Protection Agency's (EPA) Toxics Release Inventory (TRI) database through the `Envirofacts Data Service API <https://www.epa.gov/enviro/envirofacts-data-service-api>`_. Some of the information contained in this database is also available through the `TRI Explorer <https://enviro.epa.gov/triexplorer/tri_release.chemical>`_ interface. 

So why might you want to use the ``tritoolkit``? You may find the ``tritoolkit`` library useful if you want to access information that is not easily available through this interface. For example, State/County FIPS codes needed to merge TRI data with other spatial datasets can be obtained from the TRI database using ``tritoolkit``, but are not available through the TRI Explorer. ``tritoolkit`` also provides some convenience methods for creating GIS layers from latitude/longitude coordinates of facilities or release locations found in the TRI database.

``tritoolkit`` currently requires the user to have some understanding of the TRI database model, which the EPA has `documented in detail <https://www.epa.gov/enviro/tri-model>`_.

What is the Toxics Release Inventory?
-------------------------------------

The Toxics Release Inventory is a dataset about toxic chemical releases and related prevention activities reported by industrial and federal facilities. Learn more about the TRI program, reporting, and data on the `EPA's website <https://www.epa.gov/toxics-release-inventory-tri-program>`_.

Quickstart
----------


Releases
--------

This library's :doc:`change-log` details changes and fixes made with each release.


Indices and tables
==================

* :ref:`genindex`

.. toctree::
   :maxdepth: 6
   :caption: User Guide
   :hidden:

   getting_started
   
.. toctree::
   :maxdepth: 6
   :caption: Reference
   :hidden:

   reference/index

.. toctree::
   :maxdepth: 0
   :caption: Community
   :hidden:

   CONTRIBUTING

.. toctree::
   :maxdepth: 6
   :caption: Project History
   :hidden:

   change-log