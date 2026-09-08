"""Ozon-клиент для активного кабинета пользователя."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.exceptions import SellerNotBoundError
from bot.db.models import SellerAccount, TelegramUser
from bot.ozon.client import OzonAPIClient, OzonCredentials
from bot.repositories.seller import SellerRepository
from bot.services.seller_service import SellerService


async def ozon_client_for_active(
    session: AsyncSession,
    user: TelegramUser,
) -> tuple[SellerAccount, OzonAPIClient]:
    seller = await SellerService(session).get_active(user.id)
    if seller is None:
        raise SellerNotBoundError()
    api_key = SellerRepository(session).decrypt_api_key(seller)
    client = OzonAPIClient(
        credentials=OzonCredentials(client_id=seller.ozon_client_id, api_key=api_key)
    )
    return seller, client
