"""
Utility functions for the Astronomy TAP Client.
"""
import json
import pandas as pd
import pyarrow.parquet as pq
import io
from datetime import datetime
from typing import Dict, Any, Optional, Union, List

from adss.exceptions import (
    ADSSClientError, AuthenticationError, PermissionDeniedError,
    ResourceNotFoundError, QueryExecutionError, ServerError
)

def handle_response_errors(response):
    """Handles HTTP response errors and raises appropriate exceptions."""
    if 200 <= response.status_code < 300:
        return response
    
    try:
        error_data = response.json()
        error_message = error_data.get('detail', str(error_data))
    except Exception:
        error_message = response.text or f"HTTP Error {response.status_code}"
    
    # For 401 errors, check if it's an anonymous query attempt
    if response.status_code == 401:
        # If the error mentions "authentication required for protected schemas"
        # or similar, it's likely an anonymous query trying to access restricted data
        if "protected" in error_message.lower() or "requires authentication" in error_message.lower():
            raise PermissionDeniedError(f"This query requires authentication: {error_message}", response)
        else:
            raise AuthenticationError(error_message, response)
    elif response.status_code == 403:
        raise PermissionDeniedError(error_message, response)
    elif response.status_code == 404:
        raise ResourceNotFoundError(error_message, response)
    elif response.status_code >= 500:
        raise ServerError(f"Server error: {error_message}", response)
    else:
        raise ADSSClientError(error_message, response)

def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """
    Parses a datetime string into a datetime object.
    """
    if not dt_str:
        return None
    
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return None


def parquet_to_dataframe(parquet_data: bytes) -> pd.DataFrame:
    """
    Converts Parquet bytes to a pandas DataFrame.
    """
    try:
        buffer = io.BytesIO(parquet_data)
        table = pq.read_table(buffer)
        return table.to_pandas()
    except Exception as e:
        raise ADSSClientError(f"Failed to convert Parquet data to DataFrame: {str(e)}")


def format_table_name(schema: str, table: str) -> str:
    """
    Formats a schema and table name into a fully qualified table name.
    """
    return f"{schema}.{table}"


def prepare_query_params(params: Dict[str, Any]) -> Dict[str, str]:
    """
    Prepares query parameters for API requests, handling different types.
    """
    processed_params = {}
    
    for key, value in params.items():
        if value is None:
            continue
        elif isinstance(value, bool):
            processed_params[key] = str(value).lower()
        elif isinstance(value, (list, dict)):
            processed_params[key] = json.dumps(value)
        else:
            processed_params[key] = str(value)
    
    return processed_params


def format_permission(permission_type: str) -> str:
    """
    Validates and formats a permission type (read, write, all).
    """
    valid_permissions = {'read', 'write', 'all'}
    permission = permission_type.lower()
    
    if permission not in valid_permissions:
        raise ValueError(f"Invalid permission type: {permission_type}. "
                         f"Must be one of: {', '.join(valid_permissions)}")
    
    return permission