"""PyHydroQuebec Error Module."""


class PyHydroQuebecError(Exception):
    """Base PyHydroQuebec Error."""


class PyHydroQuebecHTTPError(PyHydroQuebecError):
    """HTTP PyHydroQuebec Error."""


class PyHydroQuebecAnnualError(PyHydroQuebecError):
    """Annual PyHydroQuebec Error."""
