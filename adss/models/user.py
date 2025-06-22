"""
User-related data models for the Astronomy TAP Client.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime

from adss.utils import parse_datetime


@dataclass
class SchemaPermission:
    """Schema-level permission."""
    schema_name: str
    permission: str  # 'read', 'write', or 'all'


@dataclass
class TablePermission:
    """Table-level permission."""
    schema_name: str
    table_name: str
    permission: str  # 'read', 'write', or 'all'


@dataclass
class RolePermissions:
    """Permissions associated with a role."""
    schema_permissions: List[SchemaPermission] = field(default_factory=list)
    table_permissions: List[TablePermission] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RolePermissions':
        """Create a RolePermissions object from a dictionary."""
        schema_perms = [
            SchemaPermission(**p) 
            for p in data.get('schema_permissions', [])
        ]
        
        table_perms = [
            TablePermission(**p) 
            for p in data.get('table_permissions', [])
        ]
        
        return cls(
            schema_permissions=schema_perms,
            table_permissions=table_perms
        )


@dataclass
class Role:
    """User role with associated permissions."""
    id: int
    name: str
    description: Optional[str] = None
    permissions: Optional[RolePermissions] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Role':
        """Create a Role object from a dictionary."""
        role_id = data.get('id')
        name = data.get('name')
        description = data.get('description')
        
        permissions_data = data.get('permissions')
        permissions = None
        if permissions_data:
            permissions = RolePermissions.from_dict(permissions_data)
        
        return cls(
            id=role_id,
            name=name,
            description=description,
            permissions=permissions
        )


@dataclass
class User:
    """User model with authentication and role information."""
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_staff: bool = False
    is_superuser: bool = False
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    roles: List[Role] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create a User object from a dictionary."""
        user_id = data.get('id')
        username = data.get('username')
        email = data.get('email')
        full_name = data.get('full_name')
        is_active = data.get('is_active', True)
        is_staff = data.get('is_staff', False)
        is_superuser = data.get('is_superuser', False)
        
        created_at = parse_datetime(data.get('created_at'))
        last_login = parse_datetime(data.get('last_login'))
        
        roles = [
            Role.from_dict(role_data) 
            for role_data in data.get('roles', [])
        ]
        
        return cls(
            id=user_id,
            username=username,
            email=email,
            full_name=full_name,
            is_active=is_active,
            is_staff=is_staff,
            is_superuser=is_superuser,
            created_at=created_at,
            last_login=last_login,
            roles=roles
        )