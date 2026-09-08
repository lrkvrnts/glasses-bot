"""Application exception hierarchy."""

from __future__ import annotations


class AppError(Exception):
    """Base application error."""

    user_message: str = "Произошла ошибка. Попробуй ещё раз."
    hint: str | None = None

    def __init__(self, message: str = "", *args: object) -> None:
        super().__init__(message or self.user_message)
        if message:
            self.user_message = message


# --- Ozon API ---


class OzonError(AppError):
    """Base Ozon API error."""

    user_message = "Ошибка при обращении к Ozon."


class OzonAuthError(OzonError):
    user_message = "Неверный Client ID или API-ключ."
    hint = "Перепривяжи кабинет: /bind"


class OzonRateLimitError(OzonError):
    def __init__(self, message: str = "", retry_after: int = 60) -> None:
        super().__init__(message)
        self.retry_after = retry_after
        self.user_message = f"Ozon ограничивает запросы. Повторю через {retry_after} сек."


class OzonValidationError(OzonError):
    def __init__(self, message: str = "", field: str | None = None) -> None:
        super().__init__(message)
        self.field = field
        if field:
            self.user_message = f"Ошибка валидации Ozon в поле «{field}»."


class OzonNotFoundError(OzonError):
    user_message = "Объект не найден в Ozon."


# --- Domain ---


class XLSXFormatError(AppError):
    user_message = "Файл повреждён или неверный формат."
    hint = "Скачай шаблон: /template"


class XLSXValidationError(AppError):
    def __init__(self, message: str, row: int | None = None, column: str | None = None) -> None:
        super().__init__(message)
        self.row = row
        self.column = column
        loc = f" (строка {row}" + (f", колонка «{column}»" if column else "") + ")" if row else ""
        self.user_message = f"Ошибка в файле{loc}: {message}"


class SellerNotBoundError(AppError):
    user_message = "Сначала привяжи кабинет Ozon."
    hint = "Команда: /bind"
