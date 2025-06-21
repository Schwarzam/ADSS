"""
Astronomy TAP Client - A Python client for interacting with the Astronomy TAP Service API.

This package provides a comprehensive client for working with the Astronomy TAP Service,
including authentication, query execution, user management, and administrative functions.
"""

__version__ = "0.1.0"

from .client import ADSSClient
from .exceptions import (
    ADSSClientError, AuthenticationError, PermissionDeniedError, 
    ResourceNotFoundError, QueryExecutionError
)
from .models.user import User, Role
from .models.query import Query, QueryResult
from .models.metadata import Schema, Table, Column

__all__ = [
    'ADSSClient',
    'ADSSClientError', 'AuthenticationError', 'PermissionDeniedError',
    'ResourceNotFoundError', 'QueryExecutionError',
    'User', 'Role', 'Query', 'QueryResult', 'Schema', 'Table', 'Column'
]