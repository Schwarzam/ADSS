"""
Custom exceptions for the Astronomy TAP Client.
"""

class ADSSClientError(Exception):
    """Base exception for all TAP client errors."""
    
    def __init__(self, message, response=None):
        self.message = message
        self.response = response
        super().__init__(self.message)


class AuthenticationError(ADSSClientError):
    """Exception raised for authentication failures."""
    pass


class PermissionDeniedError(ADSSClientError):
    """Exception raised when the user doesn't have sufficient permissions."""
    pass


class ResourceNotFoundError(ADSSClientError):
    """Exception raised when a requested resource is not found."""
    pass


class QueryExecutionError(ADSSClientError):
    """Exception raised when a query fails to execute."""
    
    def __init__(self, message, query=None, response=None):
        self.query = query
        super().__init__(message, response)


class ValidationError(ADSSClientError):
    """Exception raised when input validation fails."""
    
    def __init__(self, message, errors=None, response=None):
        self.errors = errors or {}
        super().__init__(message, response)


class ConnectionError(ADSSClientError):
    """Exception raised when connection to the API server fails."""
    pass


class TimeoutError(ADSSClientError):
    """Exception raised when a request times out."""
    pass


class ServerError(ADSSClientError):
    """Exception raised when the server returns a 5xx error."""
    pass