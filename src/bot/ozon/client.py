"""Ozon Seller API client."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx
from loguru import logger
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from bot.core.exceptions import OzonAuthError, OzonError, OzonRateLimitError


@dataclass
class OzonCredentials:
    """Client ID + API key для Ozon Seller API."""

    client_id: str
    api_key: str


class OzonAPIClient:
    """Async HTTP client for Ozon Seller API."""

    def __init__(
        self,
        credentials: OzonCredentials,
        base_url: str = "https://api-seller.ozon.ru",
        timeout: int = 30,
        rate_limit_rps: float = 5.0,
    ) -> None:
        self._credentials = credentials
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._rate_limit_rps = rate_limit_rps
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            headers={
                "Client-Id": credentials.client_id,
                "Api-Key": credentials.api_key,
                "Content-Type": "application/json",
            },
        )
        # Per-instance semaphore for rate limiting
        self._semaphore = asyncio.Semaphore(max(1, int(rate_limit_rps)))

    @property
    def credentials(self) -> OzonCredentials:
        return self._credentials

    async def request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Делает запрос к Ozon API с retry и rate-limit."""
        async with self._semaphore:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                retry=retry_if_exception_type((httpx.TransportError, OzonRateLimitError)),
                reraise=True,
            ):
                with attempt:
                    response = await self._client.request(
                        method=method,
                        url=path,
                        json=json,
                        params=params,
                    )
                    return self._handle_response(response, method, path)

        # Unreachable, but mypy needs it
        raise OzonError("retry exhausted")

    def _handle_response(self, response: httpx.Response, method: str, path: str) -> dict[str, Any]:
        """Парсит ответ и бросает доменные исключения."""
        if response.status_code == 401:
            logger.warning("Ozon auth failed", path=path)
            raise OzonAuthError()
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "60"))
            raise OzonRateLimitError(retry_after=retry_after)
        if response.status_code >= 500:
            raise OzonError(f"Ozon server error {response.status_code}: {response.text}")
        if response.status_code >= 400:
            try:
                data = response.json()
                msg = data.get("message", response.text)
            except Exception:
                msg = response.text
            logger.warning("Ozon API error", status=response.status_code, body=msg)
            raise OzonError(f"Ozon error {response.status_code}: {msg}")

        if not response.content:
            return {}
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> OzonAPIClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
