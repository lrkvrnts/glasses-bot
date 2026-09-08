from bot.bot_app.handlers.products.list import router as list_router
from bot.bot_app.handlers.products.status import router as status_router
from bot.bot_app.handlers.products.upload import router as upload_router

__all__ = ["list_router", "status_router", "upload_router"]
