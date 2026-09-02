"""
Alert stream functionality for the Astronomy TAP Client.
"""
import json
from typing import Any, Dict, Iterable, Iterator, List, Optional, Union

from adss.exceptions import AuthenticationError
from adss.utils import handle_response_errors


class AlertsEndpoint:
    """
    Handles alert category discovery and live alert streaming.
    """

    def __init__(self, base_url: str, auth_manager):
        self.base_url = base_url.rstrip('/')
        self.auth_manager = auth_manager

    def get_categories(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Get the registered alert categories.

        Args:
            **kwargs: Additional keyword arguments to pass to the request.

        Returns:
            List of category dictionaries returned by the API.
        """
        response = self.auth_manager.request(
            method="GET",
            url="/adss/v1/alerts/categories",
            **kwargs
        )
        handle_response_errors(response)
        return response.json()

    def listen(
        self,
        categories: Union[str, Iterable[str]] = "all",
        replay: Optional[str] = None,
        limit: Optional[int] = None,
        follow: bool = True,
        include_control_events: bool = False,
        **kwargs
    ) -> Iterator[Dict[str, Any]]:
        """
        Listen to alert events over Server-Sent Events (SSE).

        Args:
            categories: Category name, comma-separated category names, "all",
                "*", or an iterable of category names. "*" is expanded by
                fetching registered categories first.
            replay: Optional replay point, usually "earliest" or "latest".
            limit: Optional maximum number of replayed alerts.
            follow: Continue streaming live alerts after replay completes.
            include_control_events: If True, also yield stream lifecycle events
                such as connected, replay_started, replay_complete, and keepalive.
            **kwargs: Additional keyword arguments to pass to the request.

        Yields:
            Alert dictionaries. Replayed alerts are unwrapped from their payload.

        Raises:
            AuthenticationError: If the client is not authenticated.
        """
        if not self.auth_manager.is_authenticated():
            raise AuthenticationError("Authentication required to listen for alerts")

        params = {
            "categories": self._format_categories(categories),
            "token": self.auth_manager.token,
        }
        if replay:
            params["replay_from"] = replay
            params["follow"] = "true" if follow else "false"
        if limit is not None:
            params["replay_limit"] = str(limit)

        headers = {"Accept": "text/event-stream"}
        response = self.auth_manager.request(
            method="GET",
            url="/adss/v1/alerts/stream",
            headers=headers,
            params=params,
            auth_required=True,
            stream=True,
            **kwargs
        )
        handle_response_errors(response)

        try:
            for line in response.iter_lines():
                if not line:
                    continue
                if isinstance(line, bytes):
                    line = line.decode("utf-8")
                if not line.startswith("data:"):
                    continue

                event = json.loads(line[len("data:"):].strip())
                event_type = event.get("type")

                if event_type in {"connected", "replay_started", "replay_complete", "keepalive"}:
                    if include_control_events:
                        yield event
                    if event_type == "replay_complete" and not follow:
                        return
                    continue

                if event_type == "replay":
                    yield event.get("payload", {})
                else:
                    yield event
        finally:
            response.close()

    def _format_categories(self, categories: Union[str, Iterable[str]]) -> str:
        if isinstance(categories, str):
            value = categories.strip()
            if value == "*":
                names = [category["name"] for category in self.get_categories()]
                if not names:
                    raise ValueError("No alert categories are registered")
                return ",".join(names)
            if not value:
                raise ValueError("At least one alert category is required")
            return value

        names = [str(category).strip() for category in categories if str(category).strip()]
        if not names:
            raise ValueError("At least one alert category is required")
        return ",".join(names)
