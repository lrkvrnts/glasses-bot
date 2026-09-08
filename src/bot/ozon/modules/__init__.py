"""Ozon API modules."""

from bot.ozon.modules.base import BaseOzonModule
from bot.ozon.modules.prices import PricesModule
from bot.ozon.modules.products import ProductsModule
from bot.ozon.modules.stocks import StocksModule

__all__ = [
    "BaseOzonModule",
    "ProductsModule",
    "StocksModule",
    "PricesModule",
]
