from collections.abc import Awaitable, Callable
from logging import Logger
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

class TelegramWhitelistMiddleware(BaseMiddleware):
    def __init__(self, logger: Logger) -> None:
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

        self.logger.info("Accepted Telegram update: user_id=%s event_type=%s", user_id, type(event).__name__)
        return await handler(event, data)


def _event_user_id(event: TelegramObject) -> int | None:
    if isinstance(event, Message) and event.from_user:
        return event.from_user.id
    if isinstance(event, CallbackQuery) and event.from_user:
        return event.from_user.id
    return None


def _is_support_user(user_id: int, data: dict[str, Any]) -> bool:
    ctx = data.get("ctx")
    if ctx is None:
        return False
    user = ctx.store.user.get_by_user_id(user_id)
    return user is not None and bool(user.permissions > 0)


async def _answer_denied(event: TelegramObject) -> None:
    return
    if isinstance(event, Message):
        await event.answer("Доступ запрещен.")
        return
    if isinstance(event, CallbackQuery):
        await event.answer("Доступ запрещен.", show_alert=True)
