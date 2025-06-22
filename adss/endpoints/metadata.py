"""
Database metadata functionality for the Astronomy TAP Client.
"""
import requests
from typing import Dict, List, Optional, Any

from ..exceptions import (
    AuthenticationError, ResourceNotFoundError, PermissionDeniedError
)
from adss.utils import handle_response_errors
from adss.models.metadata import Column, Table, Schema, DatabaseMetadata


class MetadataEndpoint:
    """
    Handles database metadata discovery.
    """
    
    def __init__(self, base_url: str, auth_manager):
        """
        Initialize the Metadata endpoint.
        
        Args:
            base_url: The base URL of the API server
            auth_manager: Authentication manager providing auth headers
        """
        self.base_url = base_url.rstrip('/')
        self.auth_manager = auth_manager
    
    def get_schemas(self, **kwargs) -> List[str]:
        """
        Get a list of accessible database schemas.
        
        Args:
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            List of schema names accessible to the current user
            
        Raises:
            AuthenticationError: If not authenticated (for protected schemas)
        """
        try:
            response = self.auth_manager.request(
                method="GET",
                url="/adss/v1/metadata/schemas",
                **kwargs
            )
            handle_response_errors(response)
            
            return response.json()
            
        except Exception as e:
            # Authentication error only if trying to access protected schemas
            # Anonymous users should still see public schemas
            if hasattr(e, 'response') and e.response.status_code == 401:
                raise AuthenticationError("Authentication required for protected schemas")
            raise
    
    def get_tables(self, schema_name: str, **kwargs) -> List[str]:
        """
        Get a list of accessible tables in a schema.
        
        Args:
            schema_name: Name of the schema
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            List of table names in the schema accessible to the current user
            
        Raises:
            AuthenticationError: If not authenticated (for protected schemas)
            PermissionDeniedError: If the user doesn't have access to the schema
            ResourceNotFoundError: If the schema doesn't exist
        """
        try:
            response = self.auth_manager.request(
                method="GET",
                url=f"/adss/v1/metadata/schemas/{schema_name}/tables",
                **kwargs
            )
            handle_response_errors(response)
            
            return response.json()
            
        except Exception as e:
            if hasattr(e, 'response'):
                if e.response.status_code == 401:
                    raise AuthenticationError("Authentication required for protected schemas")
                elif e.response.status_code == 403:
                    raise PermissionDeniedError(f"Access denied to schema: {schema_name}")
                elif e.response.status_code == 404:
                    raise ResourceNotFoundError(f"Schema not found: {schema_name}")
            raise
    
    def get_columns(self, schema_name: str, table_name: str, **kwargs) -> List[Column]:
        """
        Get a list of columns in a table.
        
        Args:
            schema_name: Name of the schema
            table_name: Name of the table
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            List of Column objects in the table
            
        Raises:
            AuthenticationError: If not authenticated (for protected schemas)
            PermissionDeniedError: If the user doesn't have access to the table
            ResourceNotFoundError: If the schema or table doesn't exist
        """
        try:
            response = self.auth_manager.request(
                method="GET",
                url=f"/adss/v1/metadata/schemas/{schema_name}/tables/{table_name}/columns",
                **kwargs
            )
            handle_response_errors(response)
            
            columns_data = response.json()
            return [Column.from_dict(col_data) for col_data in columns_data]
            
        except Exception as e:
            if hasattr(e, 'response'):
                if e.response.status_code == 401:
                    raise AuthenticationError("Authentication required for protected schemas")
                elif e.response.status_code == 403:
                    raise PermissionDeniedError(f"Access denied to table: {schema_name}.{table_name}")
                elif e.response.status_code == 404:
                    raise ResourceNotFoundError(f"Table not found: {schema_name}.{table_name}")
            raise
    
    def get_database_metadata(self, **kwargs) -> DatabaseMetadata:
        """
        Get comprehensive database metadata for accessible schemas and tables.
        
        Args:
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            DatabaseMetadata object containing all accessible schema and table information
            
        Raises:
            AuthenticationError: If not authenticated (for protected schemas)
        """
        try:
            response = self.auth_manager.request(
                method="GET",
                url="/adss/v1/metadata/database",
                **kwargs
            )
            handle_response_errors(response)
            
            metadata = response.json()
            return DatabaseMetadata.from_dict(metadata)
            
        except Exception as e:
            if hasattr(e, 'response') and e.response.status_code == 401:
                raise AuthenticationError("Authentication required for protected schemas")
            raise
    
    def get_table_info(self, schema_name: str, table_name: str, **kwargs) -> Table:
        """
        Get detailed information about a specific table.
        
        Args:
            schema_name: Name of the schema
            table_name: Name of the table
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            Table object with column information
            
        Raises:
            AuthenticationError: If not authenticated (for protected schemas)
            PermissionDeniedError: If the user doesn't have access to the table
            ResourceNotFoundError: If the schema or table doesn't exist
        """
        # Get columns for the table
        columns = self.get_columns(schema_name, table_name, **kwargs)
        
        # Create and return Table object
        return Table(name=table_name, columns=columns)
    
    def get_schema_info(self, schema_name: str, **kwargs) -> Schema:
        """
        Get detailed information about a specific schema.
        
        Args:
            schema_name: Name of the schema
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            Schema object with table information
            
        Raises:
            AuthenticationError: If not authenticated (for protected schemas)
            PermissionDeniedError: If the user doesn't have access to the schema
            ResourceNotFoundError: If the schema doesn't exist
        """
        # Get tables in the schema
        table_names = self.get_tables(schema_name, **kwargs)
        
        # Get information for each table
        tables = []
        for table_name in table_names:
            try:
                table = self.get_table_info(schema_name, table_name, **kwargs)
                tables.append(table)
            except PermissionDeniedError:
                # Skip tables we don't have access to
                continue
        
        # Create and return Schema object
        return Schema(name=schema_name, tables=tables)