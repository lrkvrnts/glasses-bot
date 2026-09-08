"""Healthcheck endpoint."""

from aiohttp import web


async def healthz(request: web.Request) -> web.Response:
    return web.Response(text="ok")
