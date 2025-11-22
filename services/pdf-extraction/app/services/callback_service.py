"""Callback service to send extraction results to Django backend."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class CallbackError(Exception):
    """Error during callback execution."""


class CallbackService:
    """Service for sending extraction results back to Django backend."""

    def __init__(self, callback_url: str, callback_token: str, timeout: int = 30):
        """Initialize callback service.

        Args:
            callback_url: URL of the Django callback endpoint
            callback_token: Bearer token for authentication
            timeout: Request timeout in seconds
        """
        self.callback_url = callback_url
        self.callback_token = callback_token
        self.timeout = timeout

    async def send_callback(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Send callback to Django backend with extraction results.

        Args:
            payload: Extraction results in Django format

        Returns:
            Response from Django backend

        Raises:
            CallbackError: If callback fails
        """
        try:
            logger.info(f"Sending callback to {self.callback_url}")
            logger.debug(f"Callback payload keys: {list(payload.keys())}")

            headers = {
                "Authorization": f"Bearer {self.callback_token}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.callback_url,
                    json=payload,
                    headers=headers,
                )

                # Log response for debugging
                logger.info(f"Callback response status: {response.status_code}")
                logger.debug(f"Callback response: {response.text[:500]}")

                response.raise_for_status()

                result = response.json()
                logger.info(f"Callback successful: {result.get('id', 'unknown')}")
                return result

        except httpx.HTTPStatusError as e:
            logger.error(f"Callback failed with status {e.response.status_code}: {e.response.text}")
            raise CallbackError(
                f"Callback failed with status {e.response.status_code}: {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            logger.error(f"Callback request failed: {e}", exc_info=True)
            raise CallbackError(f"Callback request failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during callback: {e}", exc_info=True)
            raise CallbackError(f"Unexpected callback error: {e}") from e
