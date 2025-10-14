import os
import time
from typing import Dict, Optional, Tuple

import requests  # kept for compatibility (exceptions/type expectations)
import httpx

from adss.exceptions import AuthenticationError
from adss.utils import handle_response_errors
from adss.models.user import User


# --- internal defaults (safe timeouts; env-overridable) ---
_CONNECT_TIMEOUT = float(os.getenv("ADSS_CONNECT_TIMEOUT", "5"))
_READ_TIMEOUT    = float(os.getenv("ADSS_READ_TIMEOUT", "600"))
_DEFAULT_TIMEOUT = (_CONNECT_TIMEOUT, _READ_TIMEOUT)

_TOTAL_RETRIES   = int(os.getenv("ADSS_RETRY_TOTAL", "3"))
_BACKOFF_FACTOR  = float(os.getenv("ADSS_RETRY_BACKOFF", "0.5"))
_TRUST_ENV       = os.getenv("ADSS_TRUST_ENV", "1").lower() not in ("0", "false", "no")
_FORCE_CLOSE_STREAMS = os.getenv("ADSS_FORCE_CLOSE_STREAMS", "0").lower() in ("1", "true", "yes")

def _read_all_bytes(resp: httpx.Response,
                    chunk_size: int = 1024 * 1024,
                    total_timeout: Optional[float] = None) -> bytes:
    """
    Stream the response body to memory and return bytes.
    - Respects httpx read timeout between chunks (via iter_bytes()).
    - Optionally enforces an overall time budget (total_timeout).
    - Validates Content-Length when present.
    - Always closes the response.
    """
    import io, time
    from httpx import ReadTimeout, RemoteProtocolError, TransportError

    # If httpx has already cached content, return it.
    if hasattr(resp, "_content"):
        return resp._content  # type: ignore[attr-defined]

    buf = io.BytesIO()
    bytes_read = 0
    start = time.monotonic()

    expected = None
    cl = resp.headers.get("Content-Length")
    if cl:
        try:
            expected = int(cl)
        except ValueError:
            expected = None

    try:
        for chunk in resp.iter_bytes(chunk_size=chunk_size):
            if not chunk:
                break
            buf.write(chunk)
            bytes_read += len(chunk)
            if total_timeout is not None and (time.monotonic() - start) > total_timeout:
                raise ReadTimeout("overall read timeout exceeded")
    except (ReadTimeout, RemoteProtocolError, TransportError):
        # ensure socket cleanup before propagating
        try:
            resp.close()
        finally:
            raise

    data = buf.getvalue()
    if expected is not None and bytes_read != expected:
        try:
            resp.close()
        finally:
            raise RemoteProtocolError(
                f"Incomplete body: got {bytes_read} bytes, expected {expected}"
            )

    # cache like httpx does; then close
    resp._content = data  # type: ignore[attr-defined]
    resp.close()
    return data

def _to_httpx_timeout(t):
    """Map (connect, read) tuple or scalar into httpx.Timeout."""
    if isinstance(t, tuple) and len(t) == 2:
        connect, read = t
        return httpx.Timeout(connect=connect, read=read, write=read, pool=connect)
    if isinstance(t, (int, float)):
        return httpx.Timeout(t)
    return httpx.Timeout(connect=_CONNECT_TIMEOUT, read=_READ_TIMEOUT, write=_READ_TIMEOUT, pool=_CONNECT_TIMEOUT)


def _attach_requests_compat(resp: httpx.Response):
    """
    Give httpx.Response a requests-like surface and a SAFE .read():
    - resp.iter_content(chunk_size) -> yields bytes
    - resp.raw.read()               -> returns remaining bytes
    - resp.read()                   -> safe, streaming-based, idempotent
    """
    import io, time
    from httpx import ReadTimeout, RemoteProtocolError, TransportError

    # requests-like streaming
    if not hasattr(resp, "iter_content"):
        def iter_content(chunk_size: int = 1024 * 1024):
            return resp.iter_bytes(chunk_size=chunk_size)
        setattr(resp, "iter_content", iter_content)

    # requests-like raw.read()
    if not hasattr(resp, "raw"):
        class _RawAdapter:
            def __init__(self, r: httpx.Response):
                self._r = r
            def read(self, amt: Optional[int] = None) -> bytes:
                # Use the same safe read under the hood
                return getattr(self._r, "read")( )
        setattr(resp, "raw", _RawAdapter(resp))

    # ---- SAFE .read(): stream to memory, cache, and close ----
    # Only replace if httpx hasn't already cached content
    def _safe_read(self, *, chunk_size: int = 1024 * 1024,
                   total_timeout: Optional[float] = None) -> bytes:
        # If httpx already cached, return it (idempotent)
        if hasattr(self, "_content"):
            return self._content

        buf = io.BytesIO()
        bytes_read = 0
        start = time.monotonic()

        # If server provided length, we can validate
        expected = None
        cl = self.headers.get("Content-Length")
        if cl:
            try:
                expected = int(cl)
            except ValueError:
                expected = None

        try:
            for chunk in self.iter_bytes(chunk_size=chunk_size):
                if not chunk:
                    break
                buf.write(chunk)
                bytes_read += len(chunk)
                if total_timeout is not None and (time.monotonic() - start) > total_timeout:
                    raise ReadTimeout("overall read timeout exceeded")
        except (ReadTimeout, RemoteProtocolError, TransportError) as e:
            # Ensure the socket is cleaned up
            try:
                self.close()
            finally:
                raise

        data = buf.getvalue()
        # Validate length if known
        if expected is not None and bytes_read != expected:
            try:
                self.close()
            finally:
                raise RemoteProtocolError(
                    f"Incomplete body: got {bytes_read} bytes, expected {expected}"
                )

        # Cache like httpx normally does, then close the stream
        self._content = data
        self.close()
        return data

    # Bind as a method (so `resp.read()` calls _safe_read)
    import types
    resp.read = types.MethodType(_safe_read, resp)  # type: ignore[attr-defined]

    return resp


class Auth:
    """
    Handles authentication, token management, and HTTP requests for the TAP client.
    """

    def __init__(self, base_url: str, verify_ssl: bool = True):
        self.base_url = base_url.rstrip('/')
        self.token: Optional[str] = None
        self.current_user: Optional[User] = None
        self.verify_ssl = verify_ssl

        # Single keep-alive client; set verify at construction.
        self._client = httpx.Client(
            trust_env=_TRUST_ENV, 
            verify=self.verify_ssl, 
            limits=httpx.Limits(max_keepalive_connections=0, max_connections=10)
        )

    def login(self, username: str, password: str, **kwargs) -> Tuple[str, User]:
        """
        Log in with username and password, obtaining an authentication token.
        """
        login_url = f"{self.base_url}/adss/v1/auth/login"
        data = {"username": username, "password": password}

        try:
            response = self.request(
                method="POST",
                url=login_url,
                auth_required=False,
                data=data,
                **kwargs
            )
            handle_response_errors(response)

            token_data = response.json()
            self.token = token_data.get("access_token")
            if not self.token:
                raise AuthenticationError("Login succeeded but no token returned")

            self.current_user = self._get_current_user(**kwargs)
            return self.token, self.current_user

        except httpx.RequestError as e:
            # preserve existing caller except-blocks that catch requests.RequestException
            raise requests.RequestException(str(e))  # noqa: B904

    def logout(self) -> None:
        self.token = None
        self.current_user = None

    def is_authenticated(self) -> bool:
        return self.token is not None

    def _get_current_user(self, **kwargs) -> User:
        """
        Fetch the current user's information using the stored token.
        """
        if not self.token:
            raise AuthenticationError("Not authenticated")

        me_url = f"{self.base_url}/adss/v1/users/me"
        auth_headers = self._get_auth_headers()

        try:
            response = self.request(
                method="GET",
                url=me_url,
                headers=auth_headers,
                auth_required=True,
                **kwargs
            )
            handle_response_errors(response)

            user_data = response.json()
            return User.from_dict(user_data)

        except httpx.RequestError as e:
            raise requests.RequestException(str(e))  # noqa: B904

    def _get_auth_headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    # ---------------- core helpers ---------------- #

    def _full_url(self, url: str) -> str:
        return url if url.startswith(('http://', 'https://')) else f"{self.base_url}/{url.lstrip('/')}"

    def _request_with_retries_nonstream(
        self,
        *,
        method: str,
        url: str,
        headers: Dict[str, str],
        params=None,
        data=None,
        json=None,
        files=None,
        timeout: httpx.Timeout,
        follow_redirects: bool,
    ) -> httpx.Response:
        last_exc = None
        for attempt in range(_TOTAL_RETRIES + 1):
            try:
                return self._client.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=params,
                    data=data,
                    json=json,
                    files=files,
                    follow_redirects=follow_redirects,
                    timeout=timeout,
                )
            except httpx.RequestError as e:
                last_exc = e
                if attempt >= _TOTAL_RETRIES:
                    break
                time.sleep(_BACKOFF_FACTOR * (2 ** attempt))
        raise requests.RequestException(str(last_exc))  # noqa: B904

    def _request_with_retries_stream(
        self,
        *,
        method: str,
        url: str,
        headers: Dict[str, str],
        params=None,
        data=None,
        json=None,
        files=None,
        timeout: httpx.Timeout,
        follow_redirects: bool,
    ) -> httpx.Response:
        """
        Use client.stream(...) but keep the stream open for the caller.
        We manually __enter__ the context manager and override resp.close()
        to ensure resources are cleaned when caller closes the response.
        """
        last_exc = None
        for attempt in range(_TOTAL_RETRIES + 1):
            try:
                cm = self._client.stream(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=params,
                    data=data,
                    json=json,
                    files=files,
                    follow_redirects=follow_redirects,
                    timeout=timeout,
                )
                resp = cm.__enter__()  # don't exit: let caller iterate/close
                # Make close() also exit the context manager safely
                _orig_close = resp.close
                def _close():
                    try:
                        _orig_close()
                    finally:
                        try:
                            cm.__exit__(None, None, None)
                        except Exception:
                            pass
                resp.close = _close  # type: ignore[attr-defined]
                return resp
            except httpx.RequestError as e:
                last_exc = e
                if attempt >= _TOTAL_RETRIES:
                    break
                time.sleep(_BACKOFF_FACTOR * (2 ** attempt))
        raise requests.RequestException(str(last_exc))  # noqa: B904

    # ---------------- public API (unchanged signatures) ------------------- #

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        auth_required: bool = False,
        **kwargs
    ) -> requests.Response:
        """
        Make an HTTP request with automatic base_url prefix, SSL config, and auth headers.
        """
        if auth_required and not self.is_authenticated():
            raise AuthenticationError("Authentication required for this request")

        url = self._full_url(url)

        # Merge headers
        final_headers = self._get_auth_headers()
        if headers:
            final_headers.update(headers)

        # Map requests-style kwargs to httpx
        timeout   = _to_httpx_timeout(kwargs.pop('timeout', _DEFAULT_TIMEOUT))
        follow_redirects = kwargs.pop('allow_redirects', True)
        stream_flag = bool(kwargs.pop('stream', False))

        # (verify is fixed per-client at __init__; ignore/strip any incoming 'verify' kw)
        kwargs.pop('verify', None)

        # Build payload pieces compatibly
        params = kwargs.pop('params', None)
        data   = kwargs.pop('data', None)
        json_  = kwargs.pop('json', None)
        files  = kwargs.pop('files', None)

        if stream_flag:
            resp = self._request_with_retries_stream(
                method=method,
                url=url,
                headers=final_headers,
                params=params,
                data=data,
                json=json_,
                files=files,
                timeout=timeout,
                follow_redirects=follow_redirects,
            )
        else:
            resp = self._request_with_retries_nonstream(
                method=method,
                url=url,
                headers=final_headers,
                params=params,
                data=data,
                json=json_,
                files=files,
                timeout=timeout,
                follow_redirects=follow_redirects,
            )
        return _attach_requests_compat(resp)

    def refresh_user_info(self, **kwargs) -> User:
        self.current_user = self._get_current_user(**kwargs)
        return self.current_user

    def download(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        auth_required: bool = False,
        timeout: Optional[float] = None,
        **kwargs
    ) -> requests.Response:
        """
        Like request(), but always streams the body.
        Caller can iterate over response.iter_content() or
        call response.raw.read() for large files.

        Signature is identical to request(), so you can just
        swap `request` -> `download` in call sites.
        """
        if auth_required and not self.is_authenticated():
            raise AuthenticationError("Authentication required for this request")

        url = self._full_url(url)

        # Merge headers
        final_headers = self._get_auth_headers()
        if headers:
            final_headers.update(headers)
        if _FORCE_CLOSE_STREAMS:
            final_headers.setdefault("Connection", "close")

        if timeout is None:
            timeout   = _to_httpx_timeout(kwargs.pop('timeout', _DEFAULT_TIMEOUT))
        else:
            timeout = _to_httpx_timeout(timeout)
        
        follow_redirects = kwargs.pop('allow_redirects', True)
        kwargs.pop('verify', None)  # verify is fixed on client

        params = kwargs.pop('params', None)
        data   = kwargs.pop('data', None)
        json_  = kwargs.pop('json', None)
        files  = kwargs.pop('files', None)

        resp = self._request_with_retries_stream(
            method=method,
            url=url,
            headers=final_headers,
            params=params,
            data=data,
            json=json_,
            files=files,
            timeout=timeout,
            follow_redirects=follow_redirects,
        )
        handle_response_errors(resp)  # fail fast on HTTP errors
        return _attach_requests_compat(resp)

    def download_bytes(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        auth_required: bool = False,
        timeout: Optional[float | Tuple[float, float]] = None,
        total_timeout: Optional[float] = None,
        **kwargs
    ) -> bytes:
        """
        Stream a large body and return bytes.
        Safe replacement for patterns that do `resp = download(...); resp.read()`.
        """
        if auth_required and not self.is_authenticated():
            raise AuthenticationError("Authentication required for this request")

        url = self._full_url(url)

        final_headers = self._get_auth_headers()
        if headers:
            final_headers.update(headers)
        # avoid gzip surprises on binaries; optionally force close via env
        final_headers.setdefault("Accept-Encoding", "identity")
        if _FORCE_CLOSE_STREAMS:
            final_headers.setdefault("Connection", "close")

        # timeouts
        if timeout is None:
            timeout = _to_httpx_timeout(_DEFAULT_TIMEOUT)
        else:
            timeout = _to_httpx_timeout(timeout)
        follow_redirects = kwargs.pop('allow_redirects', True)
        kwargs.pop('verify', None)

        params = kwargs.pop('params', None)
        data   = kwargs.pop('data', None)
        json_  = kwargs.pop('json', None)
        files  = kwargs.pop('files', None)

        # open the stream
        resp = self._request_with_retries_stream(
            method=method,
            url=url,
            headers=final_headers,
            params=params,
            data=data,
            json=json_,
            files=files,
            timeout=timeout,
            follow_redirects=follow_redirects,
        )
        handle_response_errors(resp)  # raise for HTTP errors

        # read it all safely and return
        return _read_all_bytes(resp, total_timeout=total_timeout)