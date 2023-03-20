.. _api-interface:

REST API Interface
==================

These objects are used to interact with the TRI API from Python.

Core API Interface
------------------

.. autosummary::
   :toctree: generated
   :template: class.rst
   :nosignatures:

   tritoolkit.api.TriApiClient
   tritoolkit.api.Table

Exceptions
----------

Several different exceptions may be raised when interacting with the TRI API.

.. autosummary::
   :toctree: generated
   :template: class.rst
   :nosignatures:

   tritoolkit.api.exceptions.TriApiException
   tritoolkit.api.exceptions.TransientTriApiException
   tritoolkit.api.exceptions.TriApiError