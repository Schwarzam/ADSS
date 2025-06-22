import requests
from typing import Dict, Optional, Tuple

from adss.exceptions import AuthenticationError
from adss.utils import handle_response_errors
from adss.models.user import User


class Auth:
    """
    Handles authentication, token management, and HTTP requests for the TAP client.
    """

    def __init__(self, base_url: str, verify_ssl: bool = True):
        self.base_url = base_url.rstrip('/')
        self.token: Optional[str] = None
        self.current_user: Optional[User] = None
        self.verify_ssl = verify_ssl

    def login(self, username: str, password: str, **kwargs) -> Tuple[str, User]:
        """
        Log in with username and password, obtaining an authentication token.
        """
        login_url = f"{self.base_url}/adss/v1/auth/login"
        data = {"username": username, "password": password}

        try:
            # Use our own request() method here
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

            # Now fetch user info (this will use auth_required=True internally)
            self.current_user = self._get_current_user(**kwargs)
            return self.token, self.current_user

        except requests.RequestException as e:
            raise AuthenticationError(f"Login failed: {e}")

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
            # Again, use request() so SSL and auth headers are applied consistently
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

        except requests.RequestException as e:
            raise AuthenticationError(f"Failed to get user info: {e}")

    def _get_auth_headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

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

        # Prepend base_url if needed
        if not url.startswith(('http://', 'https://')):
            url = f"{self.base_url}/{url.lstrip('/')}"

        # Merge headers
        final_headers = self._get_auth_headers()
        if headers:
            final_headers.update(headers)

        # Apply verify_ssl unless overridden
        if 'verify' not in kwargs:
            kwargs['verify'] = self.verify_ssl

        return requests.request(method, url, headers=final_headers, **kwargs)

    def refresh_user_info(self, **kwargs) -> User:
        self.current_user = self._get_current_user(**kwargs)
        return self.current_user