"""
User management functionality for the Astronomy TAP Client.
"""
import requests
from typing import Dict, List, Optional, Any

from adss.exceptions import (
    AuthenticationError, ResourceNotFoundError, PermissionDeniedError,
    ValidationError
)
from adss.utils import handle_response_errors
from adss.models.user import User, Role


class UsersEndpoint:
    """
    Handles user management operations.
    """
    
    def __init__(self, base_url: str, auth_manager):
        """
        Initialize the Users endpoint.
        
        Args:
            base_url: The base URL of the API server
            auth_manager: Authentication manager providing auth headers
        """
        self.base_url = base_url.rstrip('/')
        self.auth_manager = auth_manager
    
    def register(self, username: str, email: str, password: str, full_name: Optional[str] = None, **kwargs) -> User:
        """
        Register a new user account.
        
        Args:
            username: Desired username
            email: User's email address
            password: User's password (will be validated for strength)
            full_name: Optional full name
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            The newly created User object
            
        Raises:
            ValidationError: If input validation fails (e.g., password too weak)
        """
        data = {
            "username": username,
            "email": email,
            "password": password
        }
        
        if full_name:
            data["full_name"] = full_name
        
        try:
            response = self.auth_manager.request(
                method="POST",
                url="/adss/v1/users",
                json=data,
                **kwargs
            )
            handle_response_errors(response)
            
            user_data = response.json()
            return User.from_dict(user_data)
            
        except Exception as e:
            if hasattr(e, 'response') and e.response.status_code == 400:
                try:
                    error_data = e.response.json()
                    raise ValidationError(
                        f"User registration failed: {error_data.get('detail', str(e))}",
                        error_data.get('errors')
                    )
                except (ValueError, AttributeError):
                    pass
            raise
    
    def get_me(self, **kwargs) -> User:
        """
        Get information about the currently authenticated user.
        
        Args:
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            The current User object
            
        Raises:
            AuthenticationError: If not authenticated
        """
        try:
            response = self.auth_manager.request(
                method="GET",
                url="/adss/v1/users/me",
                auth_required=True,
                **kwargs
            )
            handle_response_errors(response)
            
            user_data = response.json()
            return User.from_dict(user_data)
            
        except Exception as e:
            if hasattr(e, 'response') and e.response.status_code == 401:
                raise AuthenticationError("Authentication required")
            raise
    
    def update_profile(self, 
                     email: Optional[str] = None, 
                     full_name: Optional[str] = None,
                     **kwargs) -> User:
        """
        Update the current user's profile information.
        
        Args:
            email: New email address (optional)
            full_name: New full name (optional)
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            The updated User object
            
        Raises:
            AuthenticationError: If not authenticated
            ValidationError: If input validation fails
        """
        data = {}
        if email is not None:
            data["email"] = email
        if full_name is not None:
            data["full_name"] = full_name
        
        if not data:
            # Nothing to update
            return self.get_me(**kwargs)
        
        try:
            response = self.auth_manager.request(
                method="PATCH",
                url="/adss/v1/users/me",
                json=data,
                auth_required=True,
                **kwargs
            )
            handle_response_errors(response)
            
            user_data = response.json()
            return User.from_dict(user_data)
            
        except Exception as e:
            if hasattr(e, 'response') and e.response.status_code == 400:
                try:
                    error_data = e.response.json()
                    raise ValidationError(
                        f"Profile update failed: {error_data.get('detail', str(e))}",
                        error_data.get('errors')
                    )
                except (ValueError, AttributeError):
                    pass
            elif hasattr(e, 'response') and e.response.status_code == 401:
                raise AuthenticationError("Authentication required")
            raise
    
    def get_users(self, skip: int = 0, limit: int = 100, **kwargs) -> List[User]:
        """
        Get a list of users (staff only).
        
        Args:
            skip: Number of users to skip (for pagination)
            limit: Maximum number of users to return
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            List of User objects
            
        Raises:
            AuthenticationError: If not authenticated
            PermissionDeniedError: If not a staff user
        """
        params = {"skip": skip, "limit": limit}
        
        try:
            response = self.auth_manager.request(
                method="GET",
                url="/adss/v1/users",
                params=params,
                auth_required=True,
                **kwargs
            )
            handle_response_errors(response)
            
            users_data = response.json()
            return [User.from_dict(user_data) for user_data in users_data]
            
        except Exception as e:
            if hasattr(e, 'response'):
                if e.response.status_code == 401:
                    raise AuthenticationError("Authentication required")
                elif e.response.status_code == 403:
                    raise PermissionDeniedError("Staff access required")
            raise
    
    def get_user(self, user_id: str, **kwargs) -> User:
        """
        Get information about a specific user (staff only).
        
        Args:
            user_id: ID of the user to get
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            User object
            
        Raises:
            AuthenticationError: If not authenticated
            PermissionDeniedError: If not a staff user
            ResourceNotFoundError: If the user is not found
        """
        try:
            response = self.auth_manager.request(
                method="GET",
                url=f"/adss/v1/users/{user_id}",
                auth_required=True,
                **kwargs
            )
            handle_response_errors(response)
            
            user_data = response.json()
            return User.from_dict(user_data)
            
        except Exception as e:
            if hasattr(e, 'response'):
                if e.response.status_code == 401:
                    raise AuthenticationError("Authentication required")
                elif e.response.status_code == 403:
                    raise PermissionDeniedError("Staff access required")
                elif e.response.status_code == 404:
                    raise ResourceNotFoundError(f"User not found: {user_id}")
            raise
    
    def update_user(self, 
                   user_id: str, 
                   email: Optional[str] = None, 
                   full_name: Optional[str] = None, 
                   is_active: Optional[bool] = None,
                   **kwargs) -> User:
        """
        Update a user's information (staff only).
        
        Args:
            user_id: ID of the user to update
            email: New email address (optional)
            full_name: New full name (optional)
            is_active: New active status (optional)
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            The updated User object
            
        Raises:
            AuthenticationError: If not authenticated
            PermissionDeniedError: If not a staff user
            ResourceNotFoundError: If the user is not found
            ValidationError: If input validation fails
        """
        data = {}
        if email is not None:
            data["email"] = email
        if full_name is not None:
            data["full_name"] = full_name
        if is_active is not None:
            data["is_active"] = is_active
        
        if not data:
            # Nothing to update
            return self.get_user(user_id, **kwargs)
        
        try:
            response = self.auth_manager.request(
                method="PATCH",
                url=f"/adss/v1/users/{user_id}",
                json=data,
                auth_required=True,
                **kwargs
            )
            handle_response_errors(response)
            
            user_data = response.json()
            return User.from_dict(user_data)
            
        except Exception as e:
            if hasattr(e, 'response'):
                if e.response.status_code == 401:
                    raise AuthenticationError("Authentication required")
                elif e.response.status_code == 403:
                    raise PermissionDeniedError("Staff access required")
                elif e.response.status_code == 404:
                    raise ResourceNotFoundError(f"User not found: {user_id}")
                elif e.response.status_code == 400:
                    try:
                        error_data = e.response.json()
                        raise ValidationError(
                            f"User update failed: {error_data.get('detail', str(e))}",
                            error_data.get('errors')
                        )
                    except (ValueError, AttributeError):
                        pass
            raise