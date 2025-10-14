"""
Image operations and management functionality for the Astronomy TAP Client.
"""
from typing import Dict, List, Optional, Union, Any
import os

from adss.exceptions import ResourceNotFoundError
from adss.utils import handle_response_errors

import re

class ImagesEndpoint:
    """
    Handles image-related operations and management.
    """
    def __init__(self, base_url: str, auth_manager):
        self.base_url = base_url.rstrip('/')
        self.auth_manager = auth_manager

    def get_collections(self, skip: int = 0, limit: int = 100, **kwargs) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/adss/v1/images/collections/"
        try:
            headers = self.auth_manager._get_auth_headers()
        except:
            headers = {"Accept": "application/json"}
        params = {"skip": skip, "limit": limit}

        try:
            resp = self.auth_manager.request(
                method="GET",
                url=url,
                headers=headers,
                params=params,
                auth_required=False,
                **kwargs
            )
            handle_response_errors(resp)
            return resp.json()
        except Exception as e:
            raise ResourceNotFoundError(f"Failed to get image collections: {e}")

    def get_collection(self, collection_id: int, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}/adss/v1/images/collections/{collection_id}"
        try:
            headers = self.auth_manager._get_auth_headers()
        except:
            headers = {"Accept": "application/json"}

        try:
            resp = self.auth_manager.request(
                method="GET",
                url=url,
                headers=headers,
                auth_required=False,
                **kwargs
            )
            handle_response_errors(resp)
            return resp.json()
        except Exception as e:
            raise ResourceNotFoundError(f"Failed to get image collection {collection_id}: {e}")

    def list_files(self,
                   collection_id: int,
                   skip: int = 0,
                   limit: int = 100,
                   filter_name: Optional[str] = None,
                   filter_str: Optional[str] = None,
                   object_name: Optional[str] = None,
                   ra: Optional[float] = None,
                   dec: Optional[float] = None,
                   radius: Optional[float] = None,
                   ra_min: Optional[float] = None,
                   ra_max: Optional[float] = None,
                   dec_min: Optional[float] = None,
                   dec_max: Optional[float] = None,
                   **kwargs) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/adss/v1/images/collections/{collection_id}/files"
        try:
            headers = self.auth_manager._get_auth_headers()
        except:
            headers = {"Accept": "application/json"}

        params: Dict[str, Union[int, float, str]] = {"skip": skip, "limit": limit}
        if filter_name:
            params["filter_name"] = filter_name
        if filter_str:
            params["filter_str"] = filter_str
        if object_name:
            params["object_name"] = object_name
        if ra is not None and dec is not None and radius is not None:
            params.update({"ra": ra, "dec": dec, "radius": radius})
        if ra_min is not None and ra_max is not None and dec_min is not None and dec_max is not None:
            params.update({"ra_min": ra_min, "ra_max": ra_max, "dec_min": dec_min, "dec_max": dec_max})

        try:
            resp = self.auth_manager.request(
                method="GET",
                url=url,
                headers=headers,
                params=params,
                auth_required=False,
                **kwargs
            )
            handle_response_errors(resp)
            return resp.json()
        except Exception as e:
            raise ResourceNotFoundError(f"Failed to list files in collection {collection_id}: {e}")

    def cone_search(self,
                    collection_id: int,
                    ra: float,
                    dec: float,
                    radius: float,
                    filter_name: Optional[str] = None,
                    limit: int = 100,
                    **kwargs) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/adss/v1/images/collections/{collection_id}/cone_search"
        try:
            headers = self.auth_manager._get_auth_headers()
        except:
            headers = {"Accept": "application/json"}

        params = {"ra": ra, "dec": dec, "radius": radius, "limit": limit}
        if filter_name:
            params["filter_name"] = filter_name

        try:
            resp = self.auth_manager.request(
                method="GET",
                url=url,
                headers=headers,
                params=params,
                auth_required=False,
                **kwargs
            )
            handle_response_errors(resp)
            return resp.json()
        except Exception as e:
            raise ResourceNotFoundError(f"Failed to perform cone search: {e}")

    def download_file(self, file_id: int, output_path: Optional[str] = None, **kwargs) -> Union[bytes, str]:
        url = f"{self.base_url}/adss/v1/images/files/{file_id}/download?token={self.auth_manager.token}"

        try:
            resp = self.auth_manager.download(
                method="GET",
                url=url,
                stream=True,
                auth_required=False,
                **kwargs
            )
            handle_response_errors(resp)

            cd = resp.headers.get('Content-Disposition', '')
            filename = cd.split('filename=')[1].strip('"') if 'filename=' in cd else ''

            if output_path and os.path.isdir(output_path):
                output_path = os.path.join(output_path, filename)
            if output_path:
                with open(output_path, 'wb') as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)
                return output_path
            return resp.read()
        except Exception as e:
            raise ResourceNotFoundError(f"Failed to download image file {file_id}: {e}")


class LuptonImagesEndpoint:
    """
    Handles Lupton RGB image operations.
    """
    def __init__(self, base_url: str, auth_manager):
        self.base_url = base_url.rstrip('/')
        self.auth_manager = auth_manager

    def create_rgb(self,
                   r_file_id: int, g_file_id: int, b_file_id: int,
                   ra: Optional[float] = None, dec: Optional[float] = None,
                   size: Optional[float] = None, size_unit: str = "arcmin",
                   stretch: float = 3.0, Q: float = 8.0,
                   output_path: Optional[str] = None,
                   **kwargs) -> Union[bytes, str]:
        url = f"{self.base_url}/adss/v1/images/lupton_images/rgb"
        try:
            headers = self.auth_manager._get_auth_headers()
        except:
            headers = {"Accept": "image/png"}

        payload: Dict[str, Any] = {
            "r_file_id": r_file_id,
            "g_file_id": g_file_id,
            "b_file_id": b_file_id,
            "stretch": stretch,
            "Q": Q,
            "size_unit": size_unit,
            "format": "png"
        }
        if ra is not None:
            payload["ra"] = ra
        if dec is not None:
            payload["dec"] = dec
        if size is not None:
            payload["size"] = size

        try:
            resp = self.auth_manager.download(
                method="POST",
                url=url,
                headers=headers,
                json=payload,
                auth_required=False,
                **kwargs
            )
            handle_response_errors(resp)

            cd = resp.headers.get('Content-Disposition', '')
            filename = cd.split('filename=')[1].strip('"') if 'filename=' in cd else 'rgb_image.png'

            if output_path and os.path.isdir(output_path):
                output_path = os.path.join(output_path, filename)
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(resp.read())
                return resp.read()
            return resp.read()

        except Exception as e:
            raise ResourceNotFoundError(f"Failed to create RGB image: {e}")
            
    def create_rgb_by_filenames(self,
                              r_filename: str, g_filename: str, b_filename: str,
                              ra: Optional[float] = None, dec: Optional[float] = None,
                              size: Optional[float] = None, size_unit: str = "arcmin",
                              stretch: float = 3.0, Q: float = 8.0,
                              output_path: Optional[str] = None,
                              **kwargs) -> Union[bytes, str]:
        """Create an RGB composite from three images using their filenames.
        
        Args:
            r_filename: Filename of the red channel image
            g_filename: Filename of the green channel image
            b_filename: Filename of the blue channel image
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
        url = f"{self.base_url}/adss/v1/images/lupton_images/rgb/by-name"
        try:
            headers = self.auth_manager._get_auth_headers()
        except:
            headers = {"Accept": "image/png"}

        payload: Dict[str, Any] = {
            "r_filename": r_filename,
            "g_filename": g_filename,
            "b_filename": b_filename,
            "stretch": stretch,
            "Q": Q,
            "size_unit": size_unit,
            "format": "png"
        }
        if ra is not None:
            payload["ra"] = ra
        if dec is not None:
            payload["dec"] = dec
        if size is not None:
            payload["size"] = size

        try:
            resp = self.auth_manager.download(
                method="POST",
                url=url,
                headers=headers,
                json=payload,
                auth_required=False,
                **kwargs
            )
            handle_response_errors(resp)

            cd = resp.headers.get('Content-Disposition', '')
            filename = cd.split('filename=')[1].strip('"') if 'filename=' in cd else 'rgb_image.png'

            if output_path and os.path.isdir(output_path):
                output_path = os.path.join(output_path, filename)
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(resp.read())
                return resp.read()
            return resp.read()

        except Exception as e:
            raise ResourceNotFoundError(f"Failed to create RGB image by filenames: {e}")

    def create_rgb_by_coordinates(self,
                                  collection_id: int, ra: float, dec: float, size: float,
                                  r_filter: str, g_filter: str, b_filter: str,
                                  size_unit: str = "arcmin", stretch: float = 3.0, Q: float = 8.0,
                                  pattern: Optional[str] = None,
                                  output_path: Optional[str] = None,
                                  **kwargs) -> Union[bytes, str]:
        url = f"{self.base_url}/adss/v1/images/collections/{collection_id}/rgb_by_coordinates"
        try:
            headers = self.auth_manager._get_auth_headers()
        except:
            headers = {"Accept": "image/png"}

        payload: Dict[str, Any] = {
            "ra": ra, "dec": dec, "size": size,
            "r_filter": r_filter, "g_filter": g_filter, "b_filter": b_filter,
            "size_unit": size_unit, "stretch": stretch, "Q": Q,
            "format": "png"
        }
        if pattern:
            payload["pattern"] = pattern

        try:
            resp = self.auth_manager.download(
                method="POST",
                url=url,
                headers=headers,
                json=payload,
                auth_required=False,
                **kwargs
            )
            handle_response_errors(resp)

            cd = resp.headers.get('Content-Disposition', '')
            filename = cd.split('filename=')[1].strip('"') if 'filename=' in cd else 'rgb_image.png'

            if output_path and os.path.isdir(output_path):
                output_path = os.path.join(output_path, filename)
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(resp.read())
                return resp.read()
            return resp.read()

        except Exception as e:
            raise ResourceNotFoundError(f"Failed to create RGB image by coordinates: {e}")

    def create_rgb_by_object(self,
                             collection_id: int, object_name: str,
                             r_filter: str, g_filter: str, b_filter: str,
                             ra: Optional[float] = None, dec: Optional[float] = None,
                             size: Optional[float] = None, size_unit: str = "arcmin",
                             stretch: float = 3.0, Q: float = 8.0,
                             pattern: Optional[str] = None,
                             output_path: Optional[str] = None,
                             **kwargs) -> Union[bytes, str]:
        url = f"{self.base_url}/adss/v1/images/collections/{collection_id}/rgb_by_object"
        try:
            headers = self.auth_manager._get_auth_headers()
        except:
            headers = {"Accept": "image/png"}

        payload: Dict[str, Any] = {
            "object_name": object_name,
            "r_filter": r_filter, "g_filter": g_filter, "b_filter": b_filter,
            "size_unit": size_unit, "stretch": stretch, "Q": Q,
            "format": "png"
        }
        if ra is not None:
            payload["ra"] = ra
        if dec is not None:
            payload["dec"] = dec
        if size is not None:
            payload["size"] = size
        if pattern:
            payload["pattern"] = pattern

        try:
            resp = self.auth_manager.download(
                method="POST",
                url=url,
                headers=headers,
                json=payload,
                auth_required=False,
                **kwargs
            )
            handle_response_errors(resp)

            cd = resp.headers.get('Content-Disposition', '')
            filename = cd.split('filename=')[1].strip('"') if 'filename=' in cd else 'rgb_image.png'

            if output_path and os.path.isdir(output_path):
                output_path = os.path.join(output_path, filename)
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(resp.read())
                return resp.read()
            return resp.read()

        except Exception as e:
            raise ResourceNotFoundError(f"Failed to create RGB image by object: {e}")


class StampImagesEndpoint:
    """
    Handles stamp image operations.
    """
    def __init__(self, base_url: str, auth_manager):
        self.base_url = base_url.rstrip('/')
        self.auth_manager = auth_manager

    def create_stamp(self,
                     file_id: int, ra: float, dec: float, size: float,
                     size_unit: str = "arcmin", format: str = "fits",
                     zmin: Optional[float] = None, zmax: Optional[float] = None,
                     output_path: Optional[str] = None,
                     **kwargs) -> Union[bytes, str]:
        url = f"{self.base_url}/adss/v1/images/collections/{file_id}/stamp"
        try:
            headers = self.auth_manager._get_auth_headers()
        except:
            headers = {"Accept": "image/png" if format == "png" else "application/fits"}

        payload: Dict[str, Any] = {
            "ra": ra, "dec": dec, "size": size,
            "size_unit": size_unit, "format": format
        }
        if zmin is not None:
            payload["zmin"] = zmin
        if zmax is not None:
            payload["zmax"] = zmax

        try:
            resp = self.auth_manager.download(
                method="POST",
                url=url,
                headers=headers,
                json=payload,
                auth_required=False,
                **kwargs
            )
            handle_response_errors(resp)

            cd = resp.headers.get('Content-Disposition', '')
            ext = "fits" if format == "fits" else "png"
            filename = cd.split('filename=')[1].strip('"') if 'filename=' in cd else f"stamp.{ext}"

            if output_path and os.path.isdir(output_path):
                output_path = os.path.join(output_path, filename)
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(resp.read())
                return resp.read()
            return resp.read()

        except Exception as e:
            raise ResourceNotFoundError(f"Failed to create stamp from file {file_id}: {e}")
            
    def create_stamp_by_filename(self,
                               filename: str, ra: float, dec: float, size: float,
                               size_unit: str = "arcmin", format: str = "fits",
                               zmin: Optional[float] = None, zmax: Optional[float] = None,
                               output_path: Optional[str] = None,
                               **kwargs) -> Union[bytes, str]:
        """Create a postage stamp cutout from an image identified by its filename.
        
        Args:
            filename: Filename of the image file to use
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
        url = f"{self.base_url}/adss/v1/images/stamp_images/files/by-name/{filename}/stamp"
        try:
            headers = self.auth_manager._get_auth_headers()
        except:
            headers = {"Accept": "image/png" if format == "png" else "application/fits"}

        payload: Dict[str, Any] = {
            "ra": ra, "dec": dec, "size": size,
            "size_unit": size_unit, "format": format
        }
        if zmin is not None:
            payload["zmin"] = zmin
        if zmax is not None:
            payload["zmax"] = zmax

        try:
            resp = self.auth_manager.download(
                method="POST",
                url=url,
                headers=headers,
                json=payload,
                auth_required=False,
                **kwargs
            )
            handle_response_errors(resp)

            cd = resp.headers.get('Content-Disposition', '')
            ext = "fits" if format == "fits" else "png"
            filename = cd.split('filename=')[1].strip('"') if 'filename=' in cd else f"stamp.{ext}"

            if output_path and os.path.isdir(output_path):
                output_path = os.path.join(output_path, filename)
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(resp.read())
                return resp.read()
            return resp.read()

        except Exception as e:
            raise ResourceNotFoundError(f"Failed to create stamp from file {filename}: {e}")

    def create_stamp_by_coordinates(self,
                                    collection_id: int, ra: float, dec: float,
                                    size: float, filter: str, size_unit: str = "arcmin",
                                    format: str = "fits", zmin: Optional[float] = None,
                                    zmax: Optional[float] = None, pattern: Optional[str] = None,
                                    output_path: Optional[str] = None,
                                    **kwargs) -> Union[bytes, str]:
        url = f"{self.base_url}/adss/v1/images/collections/{collection_id}/stamp_by_coordinates"
        try:
            headers = self.auth_manager._get_auth_headers()
        except:
            headers = {"Accept": "image/png" if format == "png" else "application/fits"}

        payload: Dict[str, Any] = {
            "ra": ra, "dec": dec, "size": size,
            "filter": filter, "size_unit": size_unit, "format": format
        }
        if zmin is not None:
            payload["zmin"] = zmin
        if zmax is not None:
            payload["zmax"] = zmax
        if pattern:
            payload["pattern"] = pattern

        try:
            resp = self.auth_manager.download(
                method="POST",
                url=url,
                headers=headers,
                json=payload,
                auth_required=False,
                **kwargs
            )
            handle_response_errors(resp)

            cd = resp.headers.get('Content-Disposition', '')
            ext = "fits" if format == "fits" else "png"
            filename = cd.split('filename=')[1].strip('"') if 'filename=' in cd else f"stamp.{ext}"

            if output_path and os.path.isdir(output_path):
                output_path = os.path.join(output_path, filename)
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(resp.read())
                return resp.read()
            return resp.read()

        except Exception as e:
            raise ResourceNotFoundError(f"Failed to create stamp by coordinates: {e}")

    # TODO: Apply the same pattern of this functions to all download functions in this file
    def create_stamp_by_object(
        self,
        collection_id: int,
        object_name: str,
        filter_name: str,
        ra: float,
        dec: float,
        size: float,
        size_unit: str = "arcmin",
        format: str = "fits",
        zmin: Optional[float] = None,
        zmax: Optional[float] = None,
        pattern: Optional[str] = None,
        output_path: Optional[str] = None,
        **kwargs
    ) -> Union[bytes, str]:
        url = f"{self.base_url}/adss/v1/images/collections/{collection_id}/stamp_by_object"

        # Build headers (auth if available), prefer identity for big binaries
        try:
            headers = self.auth_manager._get_auth_headers()
        except Exception:
            headers = {}
        headers.setdefault("Accept", "image/png" if format == "png" else "application/fits")
        headers.setdefault("Accept-Encoding", "identity")

        # Payload
        payload: Dict[str, Any] = {
            "object_name": object_name,
            "filter_name": filter_name,
            "ra": ra,
            "dec": dec,
            "size": size,
            "size_unit": size_unit,
            "format": format,
        }
        if zmin is not None:
            payload["zmin"] = zmin
        if zmax is not None:
            payload["zmax"] = zmax
        if pattern:
            payload["pattern"] = pattern

        # Download bytes in one go (no Response object leaked to callers)
        try:
            data = self.auth_manager.download_bytes(
                method="POST",
                url=url,
                headers=headers,
                json=payload,
                auth_required=False,
                **kwargs
            )
        except Exception as e:
            raise ResourceNotFoundError(f"Failed to create stamp by object: {e}")

        # If no output_path => return bytes
        if not output_path:
            return data

        # If writing to disk, synthesize a stable filename
        ext = "fits" if format == "fits" else "png"

        # sanitize components for filesystem safety
        def _safe(s: str) -> str:
            s = s.strip()
            s = re.sub(r"\s+", "_", s)           # spaces -> underscores
            s = re.sub(r"[^A-Za-z0-9._\-+]", "", s)  # drop weird chars
            return s or "unknown"

        obj = _safe(object_name)
        filt = _safe(filter_name)
        size_str = f"{size:g}{size_unit}"

        filename = f"stamp_{obj}_{filt}_{size_str}.{ext}"

        # If output_path is a dir, append filename; otherwise treat as full path
        final_path = output_path
        if os.path.isdir(final_path):
            final_path = os.path.join(final_path, filename)

        os.makedirs(os.path.dirname(final_path) or ".", exist_ok=True)
        with open(final_path, "wb") as f:
            f.write(data)

        return final_path


class TrilogyImagesEndpoint:
    """
    Handles Trilogy RGB image operations.
    """
    def __init__(self, base_url: str, auth_manager):
        self.base_url = base_url.rstrip('/')
        self.auth_manager = auth_manager

    def create_trilogy_rgb(self,
                           r_file_ids: List[int], g_file_ids: List[int], b_file_ids: List[int],
                           ra: Optional[float] = None, dec: Optional[float] = None,
                           size: Optional[float] = None, size_unit: str = "arcmin",
                           noiselum: float = 0.15, satpercent: float = 15.0, colorsatfac: float = 2.0,
                           output_path: Optional[str] = None,
                           **kwargs) -> Union[bytes, str]:
        url = f"{self.base_url}/adss/v1/images/trilogy-rgb"
        try:
            headers = self.auth_manager._get_auth_headers()
        except:
            headers = {"Accept": "image/png"}

        payload: Dict[str, Any] = {
            "r_file_ids": r_file_ids,
            "g_file_ids": g_file_ids,
            "b_file_ids": b_file_ids,
            "noiselum": noiselum,
            "satpercent": satpercent,
            "colorsatfac": colorsatfac,
            "size_unit": size_unit,
            "format": "png"
        }
        if ra is not None:
            payload["ra"] = ra
        if dec is not None:
            payload["dec"] = dec
        if size is not None:
            payload["size"] = size

        try:
            resp = self.auth_manager.download(
                method="POST",
                url=url,
                headers=headers,
                json=payload,
                auth_required=False,
                **kwargs
            )
            handle_response_errors(resp)

            cd = resp.headers.get('Content-Disposition', '')
            filename = cd.split('filename=')[1].strip('"') if 'filename=' in cd else 'trilogy_rgb.png'

            if output_path and os.path.isdir(output_path):
                output_path = os.path.join(output_path, filename)
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(resp.read())
                return resp.read()
            return resp.read()

        except Exception as e:
            raise ResourceNotFoundError(f"Failed to create Trilogy RGB image: {e}")

    def create_trilogy_rgb_by_coordinates(self,
                                          collection_id: int, ra: float, dec: float, size: float,
                                          r_filters: List[str], g_filters: List[str], b_filters: List[str],
                                          size_unit: str = "arcmin",
                                          noiselum: float = 0.15, satpercent: float = 15.0,
                                          colorsatfac: float = 2.0, pattern: Optional[str] = None,
                                          output_path: Optional[str] = None,
                                          **kwargs) -> Union[bytes, str]:
        url = f"{self.base_url}/adss/v1/images/collections/{collection_id}/trilogy-rgb_by_coordinates"
        try:
            headers = self.auth_manager._get_auth_headers()
        except:
            headers = {"Accept": "image/png"}

        payload: Dict[str, Any] = {
            "ra": ra, "dec": dec, "size": size,
            "r_filters": r_filters, "g_filters": g_filters, "b_filters": b_filters,
            "size_unit": size_unit, "noiselum": noiselum,
            "satpercent": satpercent, "colorsatfac": colorsatfac,
            "format": "png"
        }
        if pattern:
            payload["pattern"] = pattern

        try:
            resp = self.auth_manager.download(
                method="POST",
                url=url,
                headers=headers,
                json=payload,
                auth_required=False,
                **kwargs
            )
            handle_response_errors(resp)

            cd = resp.headers.get('Content-Disposition', '')
            filename = cd.split('filename=')[1].strip('"') if 'filename=' in cd else 'trilogy_rgb.png'

            if output_path and os.path.isdir(output_path):
                output_path = os.path.join(output_path, filename)
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(resp.read())
                return output_path
            return resp.read()

        except Exception as e:
            raise ResourceNotFoundError(f"Failed to create Trilogy RGB image by coordinates: {e}")

    def create_trilogy_rgb_by_object(self,
                                     collection_id: int, object_name: str,
                                     r_filters: List[str], g_filters: List[str], b_filters: List[str],
                                     ra: Optional[float] = None, dec: Optional[float] = None,
                                     size: Optional[float] = None, size_unit: str = "arcmin",
                                     noiselum: float = 0.15, satpercent: float = 15.0,
                                     colorsatfac: float = 2.0, pattern: Optional[str] = None,
                                     output_path: Optional[str] = None,
                                     **kwargs) -> Union[bytes, str]:
        url = f"{self.base_url}/adss/v1/images/collections/{collection_id}/trilogy-rgb_by_object"
        try:
            headers = self.auth_manager._get_auth_headers()
        except:
            headers = {"Accept": "image/png"}

        payload: Dict[str, Any] = {
            "object_name": object_name,
            "r_filters": r_filters, "g_filters": g_filters, "b_filters": b_filters,
            "size_unit": size_unit, "noiselum": noiselum,
            "satpercent": satpercent, "colorsatfac": colorsatfac,
            "format": "png"
        }
        if ra is not None:
            payload["ra"] = ra
        if dec is not None:
            payload["dec"] = dec
        if size is not None:
            payload["size"] = size
        if pattern:
            payload["pattern"] = pattern

        try:
            resp = self.auth_manager.download(
                method="POST",
                url=url,
                headers=headers,
                json=payload,
                auth_required=False,
                **kwargs
            )
            handle_response_errors(resp)

            cd = resp.headers.get('Content-Disposition', '')
            filename = cd.split('filename=')[1].strip('"') if 'filename=' in cd else 'trilogy_rgb.png'

            if output_path and os.path.isdir(output_path):
                output_path = os.path.join(output_path, filename)
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(resp.read())
                return resp.read()
            return resp.read()

        except Exception as e:
            raise ResourceNotFoundError(f"Failed to create Trilogy RGB image by object: {e}")