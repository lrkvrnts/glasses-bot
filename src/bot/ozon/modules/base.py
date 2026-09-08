"""Base for Ozon API modules."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bot.ozon.client import OzonAPIClient


class BaseOzonModule:
    """Базовый класс для модулей Ozon API."""

    base_path: str = "/"

    def __init__(self, client: OzonAPIClient) -> None:
        self._client = client

    async def _get(self, path: str = "", **params: Any) -> dict[str, Any]:
        return await self._client.request("GET", self.base_path + path, params=params or None)

    async def _post(self, path: str = "", json: dict | None = None) -> dict[str, Any]:
        return await self._client.request("POST", self.base_path + path, json=json or {})
