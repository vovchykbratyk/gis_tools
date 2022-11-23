"""
Custom exceptions
"""


class ExceptionNetworkFailure(Exception):
    """
    Raised upon network timeout or other failure
    """
    pass

class PkiPasswordError(Exception):
    """
    Raised when no password is provided to PKI challenge
    """
    pass
