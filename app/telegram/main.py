# -*- coding: utf-8 -*-
from logging import Logger

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

from config import TELEGRAM_ALLOWED_USER_IDS
from telegram.access import TelegramWhitelistMiddleware
from telegram import keyboard
from telegram.context import TelegramContext
from telegram.edit_or_send import edit_or_send


def setup_root_router() -> Router:
    router = Router()

    @router.message(CommandStart())
    async def start_handler(message: Message, ctx: TelegramContext) -> None:
        ctx.logger.info(
            "Telegram /start: user_id=%s chat_id=%s",
            message.from_user.id if message.from_user else None,
            message.chat.id,
        )
        await edit_or_send(message, "Главное меню:", reply_markup=keyboard.main_menu_kb())

    return router


class TelegramBot:
    def __init__(
        self,
        token: str,
        store,
        scraper,
        ai,
        logger: Logger,
    ) -> None:
        self.logger = logger
        self.ctx = TelegramContext(store=store, scraper=scraper, ai=ai, logger=logger)

        self.bot = Bot(token=token)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.dp["ctx"] = self.ctx
        self.logger.info("Telegram bot dispatcher created")
        self._setup_access_control()
        self._include_routers()

    def _setup_access_control(self) -> None:
        middleware = TelegramWhitelistMiddleware(TELEGRAM_ALLOWED_USER_IDS, logger=self.logger)
        self.dp.message.middleware(middleware)
        self.dp.callback_query.middleware(middleware)
        self.logger.info("Telegram access middleware enabled: allowed_users_count=%s", len(TELEGRAM_ALLOWED_USER_IDS))

    def _include_routers(self) -> None:
        self.dp.include_router(setup_root_router())
        self.dp.include_router(setup_video_router())
        self.dp.include_router(setup_sourse_router())
        self.dp.include_router(setup_background_router())
        self.dp.include_router(setup_youtube_router())
        self.logger.info("Telegram routers included")

    async def run(self) -> None:
        self.logger.info("Telegram polling started")
        await self.dp.start_polling(self.bot)

    async def stop(self) -> None:
        self.logger.info("Telegram polling stopping")
        await self.dp.stop_polling()
        await self.bot.session.close()
        self.logger.info("Telegram bot session closed")
