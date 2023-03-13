"""
Exceptions which can arise in calls to the envirofacts TRI API
"""
__all__ = ["TriApiException", "TransientTriApiException"]


class TriApiException(Exception):
    pass


class TransientTriApiException(TriApiException):
    pass


class TriApiError(TriApiException):
    """Represents the case when an unknown API error occurs."""
