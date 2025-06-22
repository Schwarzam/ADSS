"""
Astronomy TAP Client - A Python client for interacting with the Astronomy TAP Service API.

This package provides a comprehensive client for working with the Astronomy TAP Service,
including authentication, query execution, user management, and administrative functions.
"""

#__version__ = "0.1.0"

from adss.client import ADSSClient
from adss.exceptions import (
    ADSSClientError, AuthenticationError, PermissionDeniedError, 
    ResourceNotFoundError, QueryExecutionError
)
from adss.models.user import User, Role
from adss.models.query import Query, QueryResult
from adss.models.metadata import Schema, Table, Column

from adss.utils import (
    handle_response_errors, parse_datetime, parquet_to_dataframe
)

__all__ = [
    'ADSSClient',
    'ADSSClientError', 'AuthenticationError', 'PermissionDeniedError',
    'ResourceNotFoundError', 'QueryExecutionError',
    'User', 'Role', 'Query', 'QueryResult', 'Schema', 'Table', 'Column',
    'handle_response_errors', 'parse_datetime', 'parquet_to_dataframe'
]