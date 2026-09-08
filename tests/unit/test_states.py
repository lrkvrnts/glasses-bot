"""Tests for FSM states."""

from bot.bot_app.states.seller import SellerBindFSM


def test_seller_bind_states_defined():
    """Все ожидаемые состояния объявлены."""
    states = {s.state for s in SellerBindFSM.__states__}
    assert "SellerBindFSM:waiting_for_name" in states
    assert "SellerBindFSM:waiting_for_client_id" in states
    assert "SellerBindFSM:waiting_for_api_key" in states
