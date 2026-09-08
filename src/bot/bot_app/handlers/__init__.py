from bot.bot_app.handlers.errors import router as errors_router
from bot.bot_app.handlers.help import router as help_router
from bot.bot_app.handlers.prices import router as prices_router
from bot.bot_app.handlers.products import (
    list_router as products_list_router,
)
from bot.bot_app.handlers.products import (
    status_router,
)
from bot.bot_app.handlers.products import (
    upload_router as products_upload_router,
)
from bot.bot_app.handlers.seller import (
    bind_router,
)
from bot.bot_app.handlers.seller import (
    list_router as seller_list_router,
)
from bot.bot_app.handlers.start import router as start_router
from bot.bot_app.handlers.stocks import router as stocks_router
from bot.bot_app.handlers.uploads import router as uploads_router

__all__ = [
    "start_router",
    "help_router",
    "bind_router",
    "seller_list_router",
    "products_list_router",
    "products_upload_router",
    "status_router",
    "stocks_router",
    "prices_router",
    "uploads_router",
    "errors_router",
]
