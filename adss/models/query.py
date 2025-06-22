"""
Query-related data models for the Astronomy TAP Client.
"""
from dataclasses import dataclass
from typing import Dict, Optional, Any, List
from datetime import datetime
import pandas as pd

from adss.utils import parse_datetime


@dataclass
class Query:
    """
    Represents a database query and its metadata.
    """
    id: str
    query_text: str
    status: str  # 'PENDING', 'QUEUED', 'RUNNING', 'COMPLETED', 'ERROR'
    created_at: datetime
    mode: str = 'adql'  # 'adql' or 'sql'
    user_id: Optional[str] = None
    completed_at: Optional[datetime] = None
    result_url: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None
    row_count: Optional[int] = None
    position_in_queue: Optional[int] = None
    expires_at: Optional[datetime] = None
    query_metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Query':
        """Create a Query object from a dictionary."""
        query_id = data.get('id')
        query_text = data.get('query_text')
        status = data.get('status')
        mode = data.get('mode', 'adql')
        user_id = data.get('user_id')
        
        created_at = parse_datetime(data.get('created_at'))
        completed_at = parse_datetime(data.get('completed_at'))
        expires_at = parse_datetime(data.get('expires_at'))
        
        result_url = data.get('result_url')
        error = data.get('error')
        execution_time_ms = data.get('execution_time_ms')
        row_count = data.get('row_count')
        position_in_queue = data.get('position_in_queue')
        query_metadata = data.get('query_metadata')
        
        return cls(
            id=query_id,
            query_text=query_text,
            status=status,
            mode=mode,
            user_id=user_id,
            created_at=created_at,
            completed_at=completed_at,
            result_url=result_url,
            error=error,
            execution_time_ms=execution_time_ms,
            row_count=row_count,
            position_in_queue=position_in_queue,
            expires_at=expires_at,
            query_metadata=query_metadata
        )
    
    @property
    def is_complete(self) -> bool:
        """Check if the query has completed (successfully or with error)."""
        return self.status in ['COMPLETED', 'ERROR']
    
    @property
    def is_running(self) -> bool:
        """Check if the query is currently running."""
        return self.status == 'RUNNING'
    
    @property
    def is_queued(self) -> bool:
        """Check if the query is queued."""
        return self.status == 'QUEUED'
    
    @property
    def is_successful(self) -> bool:
        """Check if the query completed successfully."""
        return self.status == 'COMPLETED'
    
    @property
    def is_failed(self) -> bool:
        """Check if the query failed."""
        return self.status == 'ERROR'


@dataclass
class QueryResult:
    """
    Represents the result of a query, including the data and metadata.
    """
    query: Query
    data: pd.DataFrame
    execution_time_ms: Optional[int] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    
    def to_csv(self, path: str, **kwargs) -> None:
        """Save the query result to a CSV file."""
        self.data.to_csv(path, **kwargs)
    
    def to_parquet(self, path: str, **kwargs) -> None:
        """Save the query result to a Parquet file."""
        self.data.to_parquet(path, **kwargs)
    
    def to_json(self, path: str = None, **kwargs) -> Optional[str]:
        """
        Convert the query result to JSON.
        If path is provided, saves to file, otherwise returns a JSON string.
        """
        if path:
            self.data.to_json(path, **kwargs)
            return None
        return self.data.to_json(**kwargs)
    
    def head(self, n: int = 5) -> pd.DataFrame:
        """Return the first n rows of the result."""
        return self.data.head(n)
    
    def tail(self, n: int = 5) -> pd.DataFrame:
        """Return the last n rows of the result."""
        return self.data.tail(n)
    
    def describe(self) -> pd.DataFrame:
        """Return summary statistics of the result."""
        return self.data.describe()