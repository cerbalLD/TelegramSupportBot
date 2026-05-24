from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from telegram.admin import keyboard
from telegram.admin.utils import is_admin_user
from telegram.context import TelegramContext
from telegram.states import AdminSupportState


def setup_router() -> Router:
    router = Router()

    async def _is_allowed(message_or_callback: Message | CallbackQuery, ctx: TelegramContext) -> bool:
        telegram_user = message_or_callback.from_user
        if telegram_user is None:
            return False
        user = ctx.store.user.get_by_user_id(telegram_user.id)
        if is_admin_user(user, telegram_user.id):
            return True
        if isinstance(message_or_callback, CallbackQuery):
            await message_or_callback.answer("Нет прав администратора", show_alert=True)
        else:
            await message_or_callback.answer("Нет прав администратора")
        return False

    @router.message(Command("admin"))
    async def admin_menu(message: Message, ctx: TelegramContext, state: FSMContext) -> None:
        if not await _is_allowed(message, ctx):
            return
        await state.clear()
        await message.answer("Админ-меню:", reply_markup=keyboard.admin_menu_kb())

    @router.message(F.text == "Добавить support")
    async def add_support_start(message: Message, ctx: TelegramContext, state: FSMContext) -> None:
        if not await _is_allowed(message, ctx):
            return
        await state.set_state(AdminSupportState.waiting_add_user_id)
        await message.answer("Введите Telegram user id пользователя, которого нужно добавить в support:")

    @router.message(F.text == "Удалить support")
    async def remove_support_start(message: Message, ctx: TelegramContext, state: FSMContext) -> None:
        if not await _is_allowed(message, ctx):
            return
        await state.set_state(AdminSupportState.waiting_remove_user_id)
        await message.answer("Введите Telegram user id пользователя, которого нужно удалить из support:")

    @router.message(F.text == "Отмена")
    async def cancel_admin_action(message: Message, ctx: TelegramContext, state: FSMContext) -> None:
        if not await _is_allowed(message, ctx):
            return
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=keyboard.admin_menu_kb())

    @router.message(AdminSupportState.waiting_add_user_id, F.text)
    async def add_support_finish(message: Message, ctx: TelegramContext, state: FSMContext) -> None:
        if not await _is_allowed(message, ctx):
            return
        support_user_id = _parse_user_id(message.text)
        if support_user_id is None:
            await message.answer("Введите корректный числовой Telegram user id.")
            return

        ctx.store.user.set_permissions_by_user_id(support_user_id, permissions=1)
        await state.clear()
        await message.answer(
            f"Пользователь {support_user_id} добавлен в support.",
            reply_markup=keyboard.admin_menu_kb(),
        )
        ctx.logger.info("Admin added support user_id=%s by admin_id=%s", support_user_id, message.from_user.id)

    @router.message(AdminSupportState.waiting_remove_user_id, F.text)
    async def remove_support_finish(message: Message, ctx: TelegramContext, state: FSMContext) -> None:
        if not await _is_allowed(message, ctx):
            return
        support_user_id = _parse_user_id(message.text)
        if support_user_id is None:
            await message.answer("Введите корректный числовой Telegram user id.")
            return
        if is_admin_user(None, support_user_id):
            await message.answer("Нельзя удалить администратора из support через меню.")
            return
        support_user = ctx.store.user.get_by_user_id(support_user_id)
        if support_user is None or not support_user.permissions:
            await state.clear()
            await message.answer(
                f"Пользователь {support_user_id} не был support.",
                reply_markup=keyboard.admin_menu_kb(),
            )
            return

        ctx.store.user.set_permissions_by_user_id(support_user_id, permissions=0)
        await state.clear()
        await message.answer(
            f"Пользователь {support_user_id} удален из support.",
            reply_markup=keyboard.admin_menu_kb(),
        )
        ctx.logger.info("Admin removed support user_id=%s by admin_id=%s", support_user_id, message.from_user.id)

    return router


def _parse_user_id(text: str | None) -> int | None:
    if text is None:
        return None
    text = text.strip()
    if not text.isdigit():
        return None
    return int(text)
