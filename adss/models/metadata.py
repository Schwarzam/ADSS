"""
Database metadata models for the Astronomy TAP Client.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class Column:
    """
    Represents a database column and its metadata.
    """
    name: str
    data_type: str
    is_nullable: bool
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Column':
        """Create a Column object from a dictionary."""
        return cls(
            name=data.get('name'),
            data_type=data.get('data_type'),
            is_nullable=data.get('is_nullable', False)
        )


@dataclass
class Table:
    """
    Represents a database table and its columns.
    """
    name: str
    columns: List[Column] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Table':
        """Create a Table object from a dictionary."""
        columns = [
            Column.from_dict(col_data) 
            for col_data in data.get('columns', [])
        ]
        
        return cls(
            name=data.get('name'),
            columns=columns
        )
    
    def get_column(self, name: str) -> Optional[Column]:
        """Get a column by name."""
        for column in self.columns:
            if column.name == name:
                return column
        return None
    
    def has_column(self, name: str) -> bool:
        """Check if the table has a column with the given name."""
        return any(col.name == name for col in self.columns)
    
    def column_names(self) -> List[str]:
        """Get a list of all column names."""
        return [col.name for col in self.columns]


@dataclass
class Schema:
    """
    Represents a database schema and its tables.
    """
    name: str
    tables: List[Table] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Schema':
        """Create a Schema object from a dictionary."""
        tables = [
            Table.from_dict(table_data) 
            for table_data in data.get('tables', [])
        ]
        
        return cls(
            name=data.get('name'),
            tables=tables
        )
    
    def get_table(self, name: str) -> Optional[Table]:
        """Get a table by name."""
        for table in self.tables:
            if table.name == name:
                return table
        return None
    
    def has_table(self, name: str) -> bool:
        """Check if the schema has a table with the given name."""
        return any(table.name == name for table in self.tables)
    
    def table_names(self) -> List[str]:
        """Get a list of all table names in the schema."""
        return [table.name for table in self.tables]


@dataclass
class DatabaseMetadata:
    """
    Represents database metadata, including schemas and their tables.
    """
    schemas: List[Schema] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatabaseMetadata':
        """Create a DatabaseMetadata object from a dictionary."""
        schemas = [
            Schema.from_dict(schema_data) 
            for schema_data in data.get('schemas', [])
        ]
        
        return cls(schemas=schemas)
    
    def get_schema(self, name: str) -> Optional[Schema]:
        """Get a schema by name."""
        for schema in self.schemas:
            if schema.name == name:
                return schema
        return None
    
    def has_schema(self, name: str) -> bool:
        """Check if the database has a schema with the given name."""
        return any(schema.name == name for schema in self.schemas)
    
    def schema_names(self) -> List[str]:
        """Get a list of all schema names."""
        return [schema.name for schema in self.schemas]
    
    def get_table(self, schema_name: str, table_name: str) -> Optional[Table]:
        """Get a table by schema and table name."""
        schema = self.get_schema(schema_name)
        if schema:
            return schema.get_table(table_name)
        return None