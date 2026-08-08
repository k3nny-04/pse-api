class PSEError(Exception):
    """Base for all PSE scraping errors."""

class CompanyNotFoundError(PSEError):
    """cmpy_id/symbol not found, or insufficient data to build a request — maps to 404."""

class PSEBadRequestError(PSEError):
    """Sent PSE something it rejected (400), e.g. bad date format — maps to 422."""

class PSEUnavailableError(PSEError):
    """Network failure or non-400 HTTP error from PSE — maps to 502."""

class PSEParseError(PSEError):
    """Response received but couldn't be parsed as expected — maps to 502."""