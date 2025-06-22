"""
Main client class for the Astronomy TAP Client.
"""
from typing import Optional, Dict, List, Union, BinaryIO, Any
import pandas as pd
import urllib.parse

from adss.auth import Auth
from adss.endpoints.queries import QueriesEndpoint
from adss.endpoints.users import UsersEndpoint
from adss.endpoints.metadata import MetadataEndpoint
#from .endpoints.admin import AdminEndpoint
from adss.endpoints.images import ImagesEndpoint, LuptonImagesEndpoint, StampImagesEndpoint, TrilogyImagesEndpoint
from adss.models.user import User, Role, SchemaPermission, TablePermission
from adss.models.query import Query, QueryResult
from adss.models.metadata import Column, Table, Schema, DatabaseMetadata
from adss.exceptions import AuthenticationError


class ADSSClient:
    """
    Client for interacting with the Astronomy TAP Service API.
    
    This is the main entry point for the client library, providing
    access to all API functionality through a single interface.
    """
    
    def __init__(self, base_url: str, username: Optional[str] = None, password: Optional[str] = None, verify_ssl: bool = True, **kwargs):
        """
        Initialize the TAP Client.
        
        Args:
            base_url: The base URL of the API server
            username: Optional username for immediate authentication
            password: Optional password for immediate authentication
            verify_ssl: Whether to verify SSL certificates for HTTPS requests. Set to False to disable SSL verification.
            **kwargs: Additional keyword arguments to pass to the request
        """
        # Ensure base URL is properly formatted
        parsed_url = urllib.parse.urlparse(base_url)
        if not parsed_url.scheme:
            base_url = "http://" + base_url
        self.base_url = base_url.rstrip('/')
        
        # Initialize authentication with SSL verification setting
        self.auth = Auth(self.base_url, verify_ssl=verify_ssl)
        
        if not verify_ssl:
            # ignore warnings
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Initialize endpoints
        self.queries = QueriesEndpoint(self.base_url, self.auth)
        self.users = UsersEndpoint(self.base_url, self.auth)
        self.metadata = MetadataEndpoint(self.base_url, self.auth)
        #self.admin = AdminEndpoint(self.base_url, self.auth)
        self.images = ImagesEndpoint(self.base_url, self.auth)
        self.lupton_images = LuptonImagesEndpoint(self.base_url, self.auth)
        self.stamp_images = StampImagesEndpoint(self.base_url, self.auth)
        self.trilogy_images = TrilogyImagesEndpoint(self.base_url, self.auth)
        
        # Authenticate if credentials provided
        if username and password:
            self.login(username, password, **kwargs)
    
    def login(self, username: str, password: str, **kwargs) -> User:
        """
        Log in with username and password.
        
        Args:
            username: User's username
            password: User's password
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            User object for the authenticated user
            
        Raises:
            AuthenticationError: If authentication fails
        """
        _, user = self.auth.login(username, password, **kwargs)
        return user
    
    def logout(self) -> None:
        """Log out the current user."""
        self.auth.logout()
    
    @property
    def is_authenticated(self) -> bool:
        """Check if the client is currently authenticated."""
        return self.auth.is_authenticated()
    
    @property
    def current_user(self) -> Optional[User]:
        """Get the currently authenticated user, or None if not authenticated."""
        return self.auth.current_user
    
    def register(self, username: str, email: str, password: str, full_name: Optional[str] = None, **kwargs) -> User:
        """
        Register a new user account.
        
        Args:
            username: Desired username
            email: User's email address
            password: User's password
            full_name: Optional full name
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            The newly created User object
        """
        return self.users.register(username, email, password, full_name, **kwargs)
    
    def query(self, 
             query_text: str, 
             mode: str = 'adql', 
             file: Optional[Union[str, BinaryIO]] = None,
             table_name: Optional[str] = None,
             **kwargs) -> QueryResult:
        """
        Execute a query synchronously.
        
        Args:
            query_text: The query to execute (ADQL or SQL)
            mode: Query mode ('adql' or 'sql')
            file: Optional file path or file-like object to upload as a temporary table
            table_name: Name for the uploaded table (required if file is provided)
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            QueryResult object containing the query data and metadata
        """
        return self.queries.execute_sync(query_text, mode, file, table_name, **kwargs)
    
    def async_query(self,
                   query_text: str,
                   mode: str = 'adql',
                   file: Optional[Union[str, BinaryIO]] = None,
                   table_name: Optional[str] = None,
                   **kwargs) -> Query:
        """
        Start an asynchronous query.
        
        Args:
            query_text: The query to execute (ADQL or SQL)
            mode: Query mode ('adql' or 'sql')
            file: Optional file path or file-like object to upload as a temporary table
            table_name: Name for the uploaded table (required if file is provided)
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            Query object with status information
        """
        return self.queries.execute_async(query_text, mode, file, table_name, **kwargs)
    
    def get_query_status(self, query_id: str, **kwargs) -> Query:
        """
        Get the status of an asynchronous query.
        
        Args:
            query_id: ID of the query to check
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            Updated Query object with current status
        """
        return self.queries.get_status(query_id, **kwargs)
    
    def get_query_results(self, query_id: str, **kwargs) -> QueryResult:
        """
        Get the results of a completed asynchronous query.
        
        Args:
            query_id: ID of the completed query
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            QueryResult object with the query data
        """
        return self.queries.get_results(query_id, **kwargs)
    
    def cancel_query(self, query_id: str, **kwargs) -> bool:
        """
        Cancel an asynchronous query.
        
        Args:
            query_id: ID of the query to cancel
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            True if the query was successfully canceled
        """
        return self.queries.cancel_query(query_id, **kwargs)
    
    def query_and_wait(self,
                      query_text: str,
                      mode: str = 'adql',
                      file: Optional[Union[str, BinaryIO]] = None,
                      table_name: Optional[str] = None,
                      timeout: Optional[int] = None,
                      **kwargs) -> QueryResult:
        """
        Execute a query asynchronously and wait for the results.
        
        Args:
            query_text: The query to execute (ADQL or SQL)
            mode: Query mode ('adql' or 'sql')
            file: Optional file path or file-like object to upload as a temporary table
            table_name: Name for the uploaded table (required if file is provided)
            timeout: Maximum time to wait in seconds (None for no timeout)
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            QueryResult object containing the query data and metadata
        """
        return self.queries.execute_and_wait(query_text, mode, file, table_name, timeout, **kwargs)
    
    def get_query_history(self, limit: int = 50, **kwargs) -> List[Query]:
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
        if not self.is_authenticated:
            raise AuthenticationError("Authentication required to access query history")
        
        return self.queries.get_history(limit, **kwargs)
    
    def get_schemas(self, **kwargs) -> List[str]:
        """
        Get a list of accessible database schemas.
        
        Args:
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            List of schema names accessible to the current user
        """
        return self.metadata.get_schemas(**kwargs)
    
    def get_tables(self, schema_name: str, **kwargs) -> List[str]:
        """
        Get a list of accessible tables in a schema.
        
        Args:
            schema_name: Name of the schema
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            List of table names in the schema accessible to the current user
        """
        return self.metadata.get_tables(schema_name, **kwargs)
    
    def get_columns(self, schema_name: str, table_name: str, **kwargs) -> List[Column]:
        """
        Get a list of columns in a table.
        
        Args:
            schema_name: Name of the schema
            table_name: Name of the table
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            List of Column objects in the table
        """
        return self.metadata.get_columns(schema_name, table_name, **kwargs)
    
    def get_database_metadata(self, **kwargs) -> DatabaseMetadata:
        """
        Get comprehensive database metadata for accessible schemas and tables.
        
        Args:
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            DatabaseMetadata object containing all accessible schema and table information
        """
        return self.metadata.get_database_metadata(**kwargs)
    
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
        """
        if not self.is_authenticated:
            raise AuthenticationError("Authentication required to update profile")
        
        return self.users.update_profile(email, full_name, **kwargs)
    
    # Admin methods (these require superuser/staff privileges)
    
    def create_role(self, name: str, description: Optional[str] = None, **kwargs) -> Role:
        """
        Create a new role (superuser only).
        
        Args:
            name: Role name
            description: Optional role description
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            The newly created Role object
        """
        return self.admin.create_role(name, description, **kwargs)
    
    def get_roles(self, skip: int = 0, limit: int = 100, **kwargs) -> List[Role]:
        """
        Get a list of roles (staff only).
        
        Args:
            skip: Number of roles to skip (for pagination)
            limit: Maximum number of roles to return
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            List of Role objects
        """
        return self.admin.get_roles(skip, limit, **kwargs)
    
    def add_user_to_role(self, user_id: str, role_id: int, **kwargs) -> bool:
        """
        Add a user to a role (superuser only).
        
        Args:
            user_id: ID of the user
            role_id: ID of the role
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            True if the user was successfully added to the role
        """
        return self.admin.add_user_to_role(user_id, role_id, **kwargs)
    
    def remove_user_from_role(self, user_id: str, role_id: int, **kwargs) -> bool:
        """
        Remove a user from a role (superuser only).
        
        Args:
            user_id: ID of the user
            role_id: ID of the role
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            True if the user was successfully removed from the role
        """
        return self.admin.remove_user_from_role(user_id, role_id, **kwargs)
    
    def add_schema_permission(self, role_id: int, schema_name: str, permission: str, **kwargs) -> bool:
        """
        Add a schema permission to a role (superuser only).
        
        Args:
            role_id: ID of the role
            schema_name: Name of the schema
            permission: Permission type ('read', 'write', or 'all')
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            True if the permission was successfully added
        """
        return self.admin.add_schema_permission(role_id, schema_name, permission, **kwargs)
    
    def add_table_permission(self, role_id: int, schema_name: str, table_name: str, permission: str, **kwargs) -> bool:
        """
        Add a table permission to a role (superuser only).
        
        Args:
            role_id: ID of the role
            schema_name: Name of the schema
            table_name: Name of the table
            permission: Permission type ('read', 'write', or 'all')
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            True if the permission was successfully added
        """
        return self.admin.add_table_permission(role_id, schema_name, table_name, permission, **kwargs)
    
    def remove_schema_permission(self, role_id: int, schema_name: str, **kwargs) -> bool:
        """
        Remove a schema permission from a role (superuser only).
        
        Args:
            role_id: ID of the role
            schema_name: Name of the schema
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            True if the permission was successfully removed
        """
        return self.admin.remove_schema_permission(role_id, schema_name, **kwargs)
    
    def remove_table_permission(self, role_id: int, schema_name: str, table_name: str, **kwargs) -> bool:
        """
        Remove a table permission from a role (superuser only).
        
        Args:
            role_id: ID of the role
            schema_name: Name of the schema
            table_name: Name of the table
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            True if the permission was successfully removed
        """
        return self.admin.remove_table_permission(role_id, schema_name, table_name, **kwargs)
    
    def get_role_permissions(self, role_id: int, **kwargs) -> Dict[str, Any]:
        """
        Get permissions for a role (staff only).
        
        Args:
            role_id: ID of the role
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            Dictionary containing schema and table permissions
        """
        return self.admin.get_role_permissions(role_id, **kwargs)
    
    # === Image methods ===
    
    def get_image_collections(self, skip: int = 0, limit: int = 100, **kwargs) -> List[Dict[str, Any]]:
        """
        Get a list of accessible image collections.
        
        Args:
            skip: Number of collections to skip (for pagination)
            limit: Maximum number of collections to return
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            List of image collection objects
        """
        return self.images.get_collections(skip, limit, **kwargs)
    
    def get_image_collection(self, collection_id: int, **kwargs) -> Dict[str, Any]:
        """
        Get a specific image collection by ID.
        
        Args:
            collection_id: ID of the collection to retrieve
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            Image collection object
        """
        return self.images.get_collection(collection_id, **kwargs)
    
    def list_image_files(self, collection_id: int, skip: int = 0, limit: int = 100, 
                        filter_name: Optional[str] = None, filter_str: Optional[str] = None,
                        object_name: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        List image files in a collection with optional filtering.
        
        Args:
            collection_id: ID of the image collection
            skip: Number of files to skip (for pagination)
            limit: Maximum number of files to return
            filter_name: Filter by specific filter name (e.g., 'r', 'g', 'i')
            filter_str: Filter filenames that contain this string
            object_name: Filter by object name
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            List of image file objects
        """
        return self.images.list_files(collection_id, skip, limit, filter_name, filter_str, object_name, **kwargs)
    
    def cone_search_images(self, collection_id: int, ra: float, dec: float, radius: float,
                         filter_name: Optional[str] = None, limit: int = 100, **kwargs) -> List[Dict[str, Any]]:
        """
        Find images containing a position using a cone search.
        
        Args:
            collection_id: ID of the image collection
            ra: Right ascension in degrees
            dec: Declination in degrees
            radius: Search radius in degrees
            filter_name: Optional filter name to restrict results
            limit: Maximum number of results to return
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            List of image file objects that intersect with the search cone
        """
        return self.images.cone_search(collection_id, ra, dec, radius, filter_name, limit, **kwargs)
    
    def download_image(self, file_id: int, output_path: Optional[str] = None, **kwargs) -> Union[bytes, str]:
        """
        Download an image file.
        
        Args:
            file_id: ID of the image file to download
            output_path: Optional path to save the file to. If not provided, the file content is returned as bytes.
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            If output_path is provided, returns the path to the saved file.
            Otherwise, returns the file content as bytes.
        """
        return self.images.download_file(file_id, output_path, **kwargs)
    
    def create_rgb_image(self, r_file_id: int, g_file_id: int, b_file_id: int, 
                      ra: Optional[float] = None, dec: Optional[float] = None,
                      size: Optional[float] = None, size_unit: str = "arcmin", 
                      stretch: float = 3.0, Q: float = 8.0,
                      output_path: Optional[str] = None, **kwargs) -> Union[bytes, str]:
        """
        Create an RGB composite image using Lupton's method from three images using file IDs.
        
        Args:
            r_file_id: ID of the red channel image file
            g_file_id: ID of the green channel image file
            b_file_id: ID of the blue channel image file
            ra: Optional right ascension in degrees (for cutout)
            dec: Optional declination in degrees (for cutout)
            size: Optional size in arcminutes by default
            size_unit: Units for size ("arcmin", "arcsec", or "pixels")
            stretch: Stretch parameter for Lupton algorithm
            Q: Q parameter for Lupton algorithm
            output_path: Optional path to save the image to. If not provided, the image data is returned as bytes.
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            If output_path is provided, returns the path to the saved file.
            Otherwise, returns the image data as bytes.
        """
        return self.lupton_images.create_rgb(r_file_id, g_file_id, b_file_id, ra, dec, size, 
                                           size_unit, stretch, Q, output_path, **kwargs)
    
    def create_rgb_image_by_coordinates(self, collection_id: int, ra: float, dec: float, 
                                     size: float, r_filter: str, g_filter: str, b_filter: str,
                                     size_unit: str = "arcmin", stretch: float = 3.0, Q: float = 8.0,
                                     pattern: Optional[str] = None, output_path: Optional[str] = None,
                                     **kwargs) -> Union[bytes, str]:
        """
        Create an RGB composite image using Lupton's method by finding the nearest images to given coordinates.
        
        Args:
            collection_id: ID of the image collection
            ra: Right ascension in degrees
            dec: Declination in degrees
            size: Size in arcminutes by default
            r_filter: Filter name for the red channel
            g_filter: Filter name for the green channel
            b_filter: Filter name for the blue channel
            size_unit: Units for size ("arcmin", "arcsec", or "pixels")
            stretch: Stretch parameter for Lupton algorithm
            Q: Q parameter for Lupton algorithm
            pattern: Optional pattern to match filenames
            output_path: Optional path to save the image to. If not provided, the image data is returned as bytes.
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            If output_path is provided, returns the path to the saved file.
            Otherwise, returns the image data as bytes.
        """
        return self.lupton_images.create_rgb_by_coordinates(collection_id, ra, dec, size, 
                                                         r_filter, g_filter, b_filter,
                                                         size_unit, stretch, Q, pattern, 
                                                         output_path, **kwargs)
    
    def create_stamp(self, file_id: int, ra: float, dec: float, size: float,
                  size_unit: str = "arcmin", format: str = "fits",
                  zmin: Optional[float] = None, zmax: Optional[float] = None,
                  output_path: Optional[str] = None, **kwargs) -> Union[bytes, str]:
        """
        Create a postage stamp cutout from an image.
        
        Args:
            file_id: ID of the image file
            ra: Right ascension in degrees
            dec: Declination in degrees
            size: Size of the cutout
            size_unit: Units for size ("arcmin", "arcsec", or "pixels")
            format: Output format ("fits" or "png")
            zmin: Optional minimum intensity percentile for PNG output
            zmax: Optional maximum intensity percentile for PNG output
            output_path: Optional path to save the stamp to. If not provided, the image data is returned as bytes.
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            If output_path is provided, returns the path to the saved file.
            Otherwise, returns the image data as bytes.
        """
        return self.stamp_images.create_stamp(file_id, ra, dec, size, size_unit, format,
                                           zmin, zmax, output_path, **kwargs)
    
    def create_stamp_by_coordinates(self, collection_id: int, ra: float, dec: float,
                                 size: float, filter: str, size_unit: str = "arcmin",
                                 format: str = "fits", zmin: Optional[float] = None,
                                 zmax: Optional[float] = None, pattern: Optional[str] = None,
                                 output_path: Optional[str] = None, **kwargs) -> Union[bytes, str]:
        """
        Create a postage stamp by finding the nearest image to given coordinates in a specific filter.
        
        Args:
            collection_id: ID of the image collection
            ra: Right ascension in degrees
            dec: Declination in degrees
            size: Size of the cutout
            filter: Filter name
            size_unit: Units for size ("arcmin", "arcsec", or "pixels")
            format: Output format ("fits" or "png")
            zmin: Optional minimum intensity percentile for PNG output
            zmax: Optional maximum intensity percentile for PNG output
            pattern: Optional pattern to match filenames
            output_path: Optional path to save the stamp to. If not provided, the image data is returned as bytes.
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            If output_path is provided, returns the path to the saved file.
            Otherwise, returns the image data as bytes.
        """
        return self.stamp_images.create_stamp_by_coordinates(collection_id, ra, dec, size, filter,
                                                         size_unit, format, zmin, zmax, pattern,
                                                         output_path, **kwargs)
    
    def create_trilogy_rgb(self, r_file_ids: List[int], g_file_ids: List[int], b_file_ids: List[int],
                         ra: Optional[float] = None, dec: Optional[float] = None,
                         size: Optional[float] = None, size_unit: str = "arcmin",
                         noiselum: float = 0.15, satpercent: float = 15.0, colorsatfac: float = 2.0,
                         output_path: Optional[str] = None, **kwargs) -> Union[bytes, str]:
        """
        Create an RGB composite image using the Trilogy method from multiple images per channel.
        
        Args:
            r_file_ids: List of IDs for red channel image files
            g_file_ids: List of IDs for green channel image files
            b_file_ids: List of IDs for blue channel image files
            ra: Optional right ascension in degrees (for cutout)
            dec: Optional declination in degrees (for cutout)
            size: Optional size in arcminutes by default
            size_unit: Units for size ("arcmin", "arcsec", or "pixels")
            noiselum: Noise luminance parameter for Trilogy algorithm
            satpercent: Saturation percentage parameter for Trilogy algorithm
            colorsatfac: Color saturation factor for Trilogy algorithm
            output_path: Optional path to save the image to. If not provided, the image data is returned as bytes.
            **kwargs: Additional keyword arguments to pass to the request (e.g., verify=False)
            
        Returns:
            If output_path is provided, returns the path to the saved file.
            Otherwise, returns the image data as bytes.
        """
        return self.trilogy_images.create_trilogy_rgb(r_file_ids, g_file_ids, b_file_ids,
                                                   ra, dec, size, size_unit,
                                                   noiselum, satpercent, colorsatfac,
                                                   output_path, **kwargs)