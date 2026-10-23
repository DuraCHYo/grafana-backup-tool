"""
Modern Grafana API client using httpx with async support.
"""

from typing import Any

import httpx
from loguru import logger
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential


class GrafanaConfig(BaseModel):
    """Grafana connection configuration."""

    url: str
    token: str | None = None
    admin_user: str | None = None
    admin_password: str | None = None
    verify_ssl: bool = False
    timeout: float = 30.0
    max_retries: int = 3


class GrafanaClient:
    """
    Modern async Grafana API client using httpx.
    """

    def __init__(self, config: GrafanaConfig):
        self.config = config
        self._client: httpx.AsyncClient | None = None
        self._sync_client: httpx.Client | None = None

    def _get_headers(self) -> dict[str, str]:
        """Get authentication headers."""
        headers = {
            "Content-Type": "application/json",
        }

        if self.config.token:
            headers["Authorization"] = f"Bearer {self.config.token}"
        elif self.config.admin_user and self.config.admin_password:
            import base64

            credentials = f"{self.config.admin_user}:{self.config.admin_password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"

        return headers

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create async client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.config.url,
                headers=self._get_headers(),
                verify=self.config.verify_ssl,
                timeout=self.config.timeout,
            )
        return self._client

    @property
    def sync_client(self) -> httpx.Client:
        """Get or create sync client."""
        if self._sync_client is None:
            self._sync_client = httpx.Client(
                base_url=self.config.url,
                headers=self._get_headers(),
                verify=self.config.verify_ssl,
                timeout=self.config.timeout,
            )
        return self._sync_client

    async def close(self):
        """Close async client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def close_sync(self):
        """Close sync client."""
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None

    async def get(self, endpoint: str, params: dict | None = None) -> tuple[int, Any]:
        """Async GET request."""
        try:
            response = await self.client.get(endpoint, params=params)
            logger.debug(f"GET {endpoint} - Status: {response.status_code}")

            if response.status_code >= 400:
                logger.error(f"GET {endpoint} failed with status {response.status_code}")
                try:
                    return response.status_code, response.json()
                except (ValueError, UnicodeDecodeError):
                    return response.status_code, response.text

            return response.status_code, response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"GET {endpoint} HTTP error: {e.response.status_code} - {e.response.text}")
            return e.response.status_code, e.response.text
        except httpx.ConnectError as e:
            logger.error(f"GET {endpoint} connection error: {e}")
            return 503, f"Connection error: {e}"
        except Exception as e:
            logger.error(f"GET {endpoint} unexpected error: {e}")
            return 500, str(e)

    async def post(self, endpoint: str, data: dict | None = None, json: dict | None = None) -> tuple[int, Any]:
        """Async POST request.

        Accepts either the positional ``data`` payload or an explicit
        ``json=`` alias (both spellings are used across restore components).
        """
        payload = json if json is not None else data
        try:
            response = await self.client.post(endpoint, json=payload)
            logger.debug(f"POST {endpoint} - Status: {response.status_code}")

            if response.status_code >= 400:
                logger.error(f"POST {endpoint} failed with status {response.status_code}")
                try:
                    return response.status_code, response.json()
                except (ValueError, UnicodeDecodeError):
                    return response.status_code, response.text

            return response.status_code, response.json()

        except httpx.HTTPStatusError as e:
            logger.error(
                f"POST {endpoint} HTTP error: {e.response.status_code} - {e.response.text}"
            )
            return e.response.status_code, e.response.text
        except httpx.ConnectError as e:
            logger.error(f"POST {endpoint} connection error: {e}")
            return 503, f"Connection error: {e}"
        except Exception as e:
            logger.error(f"POST {endpoint} unexpected error: {e}")
            return 500, str(e)

    async def put(self, endpoint: str, data: dict | None = None, json: dict | None = None) -> tuple[int, Any]:
        """Async PUT request.

        Accepts either the positional ``data`` payload or an explicit
        ``json=`` alias (both spellings are used across restore components).
        """
        payload = json if json is not None else data

        @retry(
            stop=stop_after_attempt(self.config.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
        )
        async def _put():
            response = await self.client.put(endpoint, json=payload)
            response.raise_for_status()
            return response.status_code, response.json()

        try:
            return await _put()
        except httpx.HTTPStatusError as e:
            logger.error(f"PUT {endpoint} failed: {e}")
            return e.response.status_code, e.response.json() if e.response else str(e)
        except Exception as e:
            logger.error(f"PUT {endpoint} error: {e}")
            return 500, str(e)

    async def delete(self, endpoint: str) -> tuple[int, Any]:
        """Async DELETE request."""

        @retry(
            stop=stop_after_attempt(self.config.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
        )
        async def _delete():
            response = await self.client.delete(endpoint)
            response.raise_for_status()
            return response.status_code, response.json()

        try:
            return await _delete()
        except httpx.HTTPStatusError as e:
            logger.error(f"DELETE {endpoint} failed: {e}")
            return e.response.status_code, e.response.json() if e.response else str(e)
        except Exception as e:
            logger.error(f"DELETE {endpoint} error: {e}")
            return 500, str(e)

    # Sync methods for compatibility
    def get_sync(self, endpoint: str, params: dict | None = None) -> tuple[int, Any]:
        """Sync GET request."""
        try:
            response = self.sync_client.get(endpoint, params=params)
            response.raise_for_status()
            return response.status_code, response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"GET {endpoint} failed: {e}")
            return e.response.status_code, e.response.json() if e.response else str(e)
        except Exception as e:
            logger.error(f"GET {endpoint} error: {e}")
            return 500, str(e)
