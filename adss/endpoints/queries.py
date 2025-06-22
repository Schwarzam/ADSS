"""
Query execution and management functionality for the Astronomy TAP Client.
"""
import time
import requests
from typing import Dict, List, Optional, Union, Any, BinaryIO, Tuple
import io
import pandas as pd

from adss.exceptions import QueryExecutionError, ResourceNotFoundError
from adss.utils import handle_response_errors, parquet_to_dataframe
from adss.models.query import Query, QueryResult


class QueriesEndpoint:
    """
    Handles query execution and management.
    """
    
    def __init__(self, base_url: str, auth_manager):
        """
        Initialize the Queries endpoint.
        
        Args:
            base_url: The base URL of the API server
            auth_manager: Authentication manager providing auth headers
        """
        self.base_url = base_url.rstrip('/')
        self.auth_manager = auth_manager
    
    def execute_sync(self, 
                    query: str, 
                    mode: str = 'adql', 
                    file: Optional[Union[str, BinaryIO]] = None,
                    table_name: Optional[str] = None,
                    **kwargs) -> QueryResult:
        """
        Execute a query synchronously and return the results.
        
        Args:
            query: The query to execute (ADQL or SQL)
            mode: Query mode ('adql' or 'sql')
            file: Optional file path or file-like object to upload as a temporary table
            table_name: Name for the uploaded table (required if file is provided)
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            QueryResult object containing the query data and metadata
            
        Raises:
            QueryExecutionError: If the query execution fails
        """
        # Don't include content-type in headers as requests will set it for multipart/form-data
        data = {
            "query": query,
            "mode": mode
        }
        
        files = {}
        
        # Handle file upload if provided
        if file:
            if not table_name:
                raise ValueError("table_name is required when uploading a file")
            
            # If file is a string, open the file
            if isinstance(file, str):
                file_obj = open(file, 'rb')
                close_file = True
            else:
                file_obj = file
                close_file = False
            
            try:
                files = {
                    "file": file_obj
                }
                data["table_name"] = table_name
                
                response = self.auth_manager.request(
                    method="POST",
                    url="/adss/sync",
                    data=data,
                    files=files,
                    **kwargs
                )
            finally:
                if close_file:
                    file_obj.close()
        else:
            # No file upload
            response = self.auth_manager.request(
                method="POST",
                url="/adss/sync",
                data=data,
                **kwargs
            )
        
        try:
            handle_response_errors(response)
            
            # Extract metadata from headers
            execution_time = int(response.headers.get('X-Execution-Time-Ms', 0))
            row_count = int(response.headers.get('X-Row-Count', 0))
            
            # Create a minimal Query object for the QueryResult
            query_obj = Query(
                id="sync_query",  # Synchronous queries don't have an ID
                query_text=query,
                status="COMPLETED",
                created_at=pd.Timestamp.now(),
                mode=mode,
                completed_at=pd.Timestamp.now(),
                execution_time_ms=execution_time,
                row_count=row_count
            )
            
            # Parse Parquet data
            df = parquet_to_dataframe(response.content)
            
            return QueryResult(
                query=query_obj,
                data=df,
                execution_time_ms=execution_time,
                row_count=row_count,
                column_count=len(df.columns) if not df.empty else 0
            )
            
        except Exception as e:
            raise QueryExecutionError(f"Synchronous query execution failed: {str(e)}", query)
    
    def execute_async(self,
                     query: str,
                     mode: str = 'adql',
                     file: Optional[Union[str, BinaryIO]] = None,
                     table_name: Optional[str] = None,
                     **kwargs) -> Query:
        """
        Start an asynchronous query execution.
        
        Args:
            query: The query to execute (ADQL or SQL)
            mode: Query mode ('adql' or 'sql')
            file: Optional file path or file-like object to upload as a temporary table
            table_name: Name for the uploaded table (required if file is provided)
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            Query object with status information
            
        Raises:
            QueryExecutionError: If starting the query fails
        """
        data = {
            "query": query,
            "mode": mode
        }
        
        files = {}
        
        # Handle file upload if provided
        if file:
            if not table_name:
                raise ValueError("table_name is required when uploading a file")
            
            # If file is a string, open the file
            if isinstance(file, str):
                file_obj = open(file, 'rb')
                close_file = True
            else:
                file_obj = file
                close_file = False
            
            try:
                files = {
                    "file": file_obj
                }
                data["table_name"] = table_name
                
                response = self.auth_manager.request(
                    method="POST",
                    url="/adss/async",
                    data=data,
                    files=files,
                    auth_required=True,
                    **kwargs
                )
            finally:
                if close_file:
                    file_obj.close()
        else:
            # No file upload
            response = self.auth_manager.request(
                method="POST",
                url="/adss/async",
                data=data,
                auth_required=True,
                **kwargs
            )
        
        try:
            handle_response_errors(response)
            job_data = response.json()
            return Query.from_dict(job_data)
            
        except Exception as e:
            raise QueryExecutionError(f"Failed to start asynchronous query: {str(e)}", query)
    
    def get_status(self, query_id: str, **kwargs) -> Query:
        """
        Get the status of an asynchronous query.
        
        Args:
            query_id: ID of the query to check
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            Updated Query object with current status
            
        Raises:
            ResourceNotFoundError: If the query is not found
        """
        try:
            response = self.auth_manager.request(
                method="GET",
                url=f"/adss/async/{query_id}",
                auth_required=True,
                **kwargs
            )
            handle_response_errors(response)
            
            job_data = response.json()
            return Query.from_dict(job_data)
            
        except ResourceNotFoundError:
            raise
        except Exception as e:
            raise QueryExecutionError(f"Failed to get query status: {str(e)}")
    
    def get_results(self, query_id: str, **kwargs) -> QueryResult:
        """
        Get the results of a completed asynchronous query.
        
        Args:
            query_id: ID of the completed query
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            QueryResult object with the query data
            
        Raises:
            ResourceNotFoundError: If the query is not found
            QueryExecutionError: If the query is not completed or results can't be retrieved
        """
        # First get the query status
        query = self.get_status(query_id, **kwargs)
        
        if not query.is_complete:
            raise QueryExecutionError(
                f"Cannot get results: Query is not completed (status: {query.status})",
                query_id
            )
        
        if query.is_failed:
            raise QueryExecutionError(
                f"Cannot get results: Query failed with error: {query.error}",
                query_id
            )
        
        # Get the results
        try:
            response = self.auth_manager.request(
                method="GET",
                url=f"/adss/async/{query_id}/results",
                auth_required=True,
                **kwargs
            )
            handle_response_errors(response)
            
            # Parse Parquet data
            df = parquet_to_dataframe(response.content)
            
            # Extract metadata
            expires_at = response.headers.get('X-Expires-At')
            if expires_at:
                query.expires_at = pd.Timestamp(expires_at)
            
            return QueryResult(
                query=query,
                data=df,
                execution_time_ms=query.execution_time_ms,
                row_count=query.row_count or len(df),
                column_count=len(df.columns) if not df.empty else 0
            )
            
        except Exception as e:
            raise QueryExecutionError(f"Failed to get query results: {str(e)}", query_id)
    
    def cancel_query(self, query_id: str, **kwargs) -> bool:
        """
        Cancel an asynchronous query.
        
        Args:
            query_id: ID of the query to cancel
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            True if the query was successfully canceled
            
        Raises:
            ResourceNotFoundError: If the query is not found
            QueryExecutionError: If canceling the query fails
        """
        try:
            response = self.auth_manager.request(
                method="DELETE",
                url=f"/adss/async/{query_id}",
                auth_required=True,
                **kwargs
            )
            handle_response_errors(response)
            
            return True
            
        except ResourceNotFoundError:
            raise
        except Exception as e:
            raise QueryExecutionError(f"Failed to cancel query: {str(e)}", query_id)
    
    def wait_for_completion(self, 
                           query_id: str, 
                           timeout: Optional[int] = None, 
                           poll_interval: int = 2,
                           **kwargs) -> Query:
        """
        Wait for an asynchronous query to complete.
        
        Args:
            query_id: ID of the query to wait for
            timeout: Maximum time to wait in seconds (None for no timeout)
            poll_interval: Time between status checks in seconds
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            Completed Query object
            
        Raises:
            ResourceNotFoundError: If the query is not found
            TimeoutError: If the query doesn't complete within the timeout
            QueryExecutionError: If the query fails
        """
        start_time = time.time()
        
        while True:
            query = self.get_status(query_id, **kwargs)
            
            if query.is_complete:
                return query
            
            if timeout and (time.time() - start_time > timeout):
                raise TimeoutError(f"Query did not complete within {timeout} seconds")
            
            time.sleep(poll_interval)
    
    def execute_and_wait(self,
                        query: str,
                        mode: str = 'adql',
                        file: Optional[Union[str, BinaryIO]] = None,
                        table_name: Optional[str] = None,
                        timeout: Optional[int] = None,
                        poll_interval: int = 2,
                        **kwargs) -> QueryResult:
        """
        Execute a query asynchronously and wait for the results.
        
        Args:
            query: The query to execute (ADQL or SQL)
            mode: Query mode ('adql' or 'sql')
            file: Optional file path or file-like object to upload as a temporary table
            table_name: Name for the uploaded table (required if file is provided)
            timeout: Maximum time to wait in seconds (None for no timeout)
            poll_interval: Time between status checks in seconds
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            QueryResult object containing the query data and metadata
            
        Raises:
            QueryExecutionError: If the query execution fails
            TimeoutError: If the query doesn't complete within the timeout
        """
        # Start async query
        query_obj = self.execute_async(query, mode, file, table_name, **kwargs)
        
        # Wait for completion
        completed_query = self.wait_for_completion(query_obj.id, timeout, poll_interval, **kwargs)
        
        if completed_query.is_failed:
            raise QueryExecutionError(
                f"Query failed with error: {completed_query.error}",
                query
            )
        
        # Get results
        return self.get_results(completed_query.id, **kwargs)
    
    def get_history(self, limit: int = 50, **kwargs) -> List[Query]:
        """
        Get the current user's query history.
        
        Args:
            limit: Maximum number of queries to return
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            List of Query objects representing past queries
            
        Raises:
            AuthenticationError: If not authenticated
        """
        params = {"limit": limit}
        
        try:
            response = self.auth_manager.request(
                method="GET",
                url="/adss/v1/queries/me",
                params=params,
                auth_required=True,
                **kwargs
            )
            handle_response_errors(response)
            
            queries_data = response.json()
            return [Query.from_dict(q) for q in queries_data]
            
        except Exception as e:
            raise QueryExecutionError(f"Failed to get query history: {str(e)}")
    
    def get_query_details(self, query_id: str, **kwargs) -> Query:
        """
        Get detailed information about a specific query.
        
        Args:
            query_id: ID of the query
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            Query object with detailed information
            
        Raises:
            ResourceNotFoundError: If the query is not found
        """
        try:
            response = self.auth_manager.request(
                method="GET",
                url=f"/adss/v1/queries/{query_id}",
                auth_required=True,
                **kwargs
            )
            handle_response_errors(response)
            
            query_data = response.json()
            return Query.from_dict(query_data)
            
        except ResourceNotFoundError:
            raise
        except Exception as e:
            raise QueryExecutionError(f"Failed to get query details: {str(e)}")
    
    def delete_query_from_history(self, query_id: str, **kwargs) -> bool:
        """
        Delete a query from the user's history.
        
        Args:
            query_id: ID of the query to delete
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            True if the query was successfully deleted
            
        Raises:
            ResourceNotFoundError: If the query is not found
        """
        try:
            response = self.auth_manager.request(
                method="DELETE",
                url=f"/adss/v1/queries/{query_id}",
                auth_required=True,
                **kwargs
            )
            handle_response_errors(response)
            
            return True
            
        except ResourceNotFoundError:
            raise
        except Exception as e:
            raise QueryExecutionError(f"Failed to delete query from history: {str(e)}")