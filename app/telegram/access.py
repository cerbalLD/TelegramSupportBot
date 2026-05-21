from collections.abc import Awaitable, Callable
from logging import Logger
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

class TelegramWhitelistMiddleware(BaseMiddleware):
    def __init__(self, allowed_user_ids: set[int], logger: Logger) -> None:
        self.allowed_user_ids = allowed_user_ids
        self.logger = logger

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_id = _event_user_id(event)
        if user_id is None:
            self.logger.info("Telegram update without user id: event_type=%s", type(event).__name__)
            return await handler(event, data)

        if user_id not in self.allowed_user_ids:
            self.logger.warning("Blocked Telegram user: user_id=%s event_type=%s", user_id, type(event).__name__)
            await _answer_denied(event)
            return None

        self.logger.info("Accepted Telegram update: user_id=%s event_type=%s", user_id, type(event).__name__)
        return await handler(event, data)


def _event_user_id(event: TelegramObject) -> int | None:
    if isinstance(event, Message) and event.from_user:
        return event.from_user.id
    if isinstance(event, CallbackQuery) and event.from_user:
        return event.from_user.id
    return None


async def _answer_denied(event: TelegramObject) -> None:
    return
    if isinstance(event, Message):
        await event.answer("Доступ запрещен.")
        return
    if isinstance(event, CallbackQuery):
        await event.answer("Доступ запрещен.", show_alert=True)
