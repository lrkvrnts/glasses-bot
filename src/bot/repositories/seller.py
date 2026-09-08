"""SellerRepository."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from bot.db.models import SellerAccount
from bot.repositories.base import BaseRepository
from bot.services.encryption import EncryptionService


class SellerRepository(BaseRepository[SellerAccount]):
    model = SellerAccount

    def __init__(self, session, encryption: EncryptionService | None = None) -> None:
        super().__init__(session)
        self._enc = encryption or EncryptionService()

    async def list_for_user(self, user_id: int) -> Sequence[SellerAccount]:
        result = await self._session.execute(
            select(SellerAccount)
            .where(SellerAccount.user_id == user_id)
            .order_by(SellerAccount.created_at.desc())
        )
        return result.scalars().all()

    async def get_active_for_user(self, user_id: int) -> SellerAccount | None:
        result = await self._session.execute(
            select(SellerAccount)
            .where(SellerAccount.user_id == user_id, SellerAccount.is_active.is_(True))
            .order_by(SellerAccount.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def create(
        self,
        user_id: int,
        name: str,
        ozon_client_id: str,
        ozon_api_key: str,
    ) -> SellerAccount:
        """Создаёт SellerAccount с зашифрованным API-ключом."""
        seller = SellerAccount(
            user_id=user_id,
            name=name,
            ozon_client_id=ozon_client_id,
            ozon_api_key_encrypted=self._enc.encrypt(ozon_api_key),
        )
        self._session.add(seller)
        await self._session.flush()
        return seller

    def decrypt_api_key(self, seller: SellerAccount) -> str:
        """Расшифровывает API-ключ продавца."""
        return self._enc.decrypt(seller.ozon_api_key_encrypted)
