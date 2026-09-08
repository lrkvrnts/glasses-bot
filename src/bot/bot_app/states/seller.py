"""FSM states for seller binding."""

from aiogram.fsm.state import State, StatesGroup


class SellerBindFSM(StatesGroup):
    """Пошаговый wizard привязки кабинета Ozon."""

    waiting_for_name = State()  # 1. Введите название магазина
    waiting_for_client_id = State()  # 2. Введите Client ID
    waiting_for_api_key = State()  # 3. Введите API key
