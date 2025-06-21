"""
API endpoint handlers for the Astronomy TAP Client.
"""

from .queries import QueriesEndpoint
from .users import UsersEndpoint
from .metadata import MetadataEndpoint
from .admin import AdminEndpoint
from .images import ImagesEndpoint, LuptonImagesEndpoint, StampImagesEndpoint, TrilogyImagesEndpoint

__all__ = [
    'QueriesEndpoint', 'UsersEndpoint', 'MetadataEndpoint', 'AdminEndpoint',
    'ImagesEndpoint', 'LuptonImagesEndpoint', 'StampImagesEndpoint', 'TrilogyImagesEndpoint'
]