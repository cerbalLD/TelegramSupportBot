from dataclasses import dataclass

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import PAGE_SIZE
from store.models import QuestionsTable
from telegram.context import TelegramContext
from telegram.edit_or_send import edit_or_send
from telegram.message_summary import message_content_type, message_history_text
from telegram.states import SupportAnswerState
from telegram.support import keyboard
from telegram.support.utils import author_label, is_support_user, status_label
from telegram.user.utils import RequestStatus


@dataclass
class HistoryPage:
    question: QuestionsTable | None
    answers: list[QuestionsTable]


def setup_router() -> Router:
    router = Router()

    async def _is_allowed(message_or_callback: Message | CallbackQuery, ctx: TelegramContext) -> bool:
        telegram_user = message_or_callback.from_user
        if telegram_user is None:
            return False
        user = ctx.store.user.get_by_user_id(telegram_user.id)
        if is_support_user(user, telegram_user.id):
            return True
        if isinstance(message_or_callback, CallbackQuery):
            await message_or_callback.answer("Нет прав для поддержки", show_alert=True)
        else:
            await message_or_callback.answer("Нет прав для поддержки")
        return False

    @router.message(F.text == "Открытые запросы")
    async def open_requests_button(message: Message, ctx: TelegramContext) -> None:
        if not await _is_allowed(message, ctx):
            return
        await _send_open_requests(message, ctx, page=0)

    @router.callback_query(F.data.startswith("support:list:"))
    async def open_requests_page(callback: CallbackQuery, ctx: TelegramContext) -> None:
        if not await _is_allowed(callback, ctx):
            return
        page = int(callback.data.rsplit(":", 1)[-1])
        await _send_open_requests(callback.message, ctx, page=page)
        await callback.answer()

    @router.callback_query(F.data == "support:noop")
    async def noop(callback: CallbackQuery) -> None:
        await callback.answer()

    @router.callback_query(F.data.startswith("support:view:"))
    async def view_request(callback: CallbackQuery, ctx: TelegramContext, state: FSMContext) -> None:
        if not await _is_allowed(callback, ctx):
            return
        await state.clear()
        request_id = int(callback.data.rsplit(":", 1)[-1])
        await _send_request_history(callback.message, ctx, request_id)
        await callback.answer()

    @router.callback_query(F.data.startswith("support:history:"))
    async def view_request_history_page(callback: CallbackQuery, ctx: TelegramContext, state: FSMContext) -> None:
        if not await _is_allowed(callback, ctx):
            return
        await state.clear()
        _, _, request_id_raw, page_raw = callback.data.split(":", 3)
        await _send_request_history(callback.message, ctx, int(request_id_raw), page=int(page_raw))
        await callback.answer()

    @router.callback_query(F.data.startswith("support:attachments:"))
    async def show_request_attachments(callback: CallbackQuery, ctx: TelegramContext) -> None:
        if not await _is_allowed(callback, ctx):
            return
        _, _, request_id_raw, page_raw = callback.data.split(":", 3)
        request = ctx.store.request.get(int(request_id_raw))
        if request is None:
            await callback.answer("Запрос не найден", show_alert=True)
            return

        pages = _build_history_pages(ctx.store.question.list_by_request(request.id))
        if not pages:
            await callback.answer("Вложений нет", show_alert=True)
            return

        page = min(max(int(page_raw), 0), len(pages) - 1)
        copied_count = 0
        for question in _page_attachments(pages[page]):
            if await _copy_history_message(callback.message, ctx, question):
                copied_count += 1

        if copied_count:
            await callback.answer("Вложения отправлены")
            return
        await callback.answer("Не получилось отправить вложения", show_alert=True)

    @router.callback_query(F.data.startswith("support:answer:"))
    async def answer_request(callback: CallbackQuery, ctx: TelegramContext, state: FSMContext) -> None:
        if not await _is_allowed(callback, ctx):
            return
        request_id = int(callback.data.rsplit(":", 1)[-1])
        request = ctx.store.request.get(request_id)
        if request is None or request.status == RequestStatus.CLOSED:
            await callback.answer("Запрос не найден или уже закрыт", show_alert=True)
            return

        await state.set_state(SupportAnswerState.waiting_answer)
        await state.update_data(request_id=request_id)
        await callback.message.answer(
            f"Введите ответ пользователю для запроса #{request_id}:",
            reply_markup=keyboard.cancel_answer_kb(request_id),
        )
        await callback.answer()

    @router.message(SupportAnswerState.waiting_answer)
    async def send_answer(message: Message, ctx: TelegramContext, state: FSMContext) -> None:
        if not await _is_allowed(message, ctx):
            return
        data = await state.get_data()
        request_id = data.get("request_id")
        request = ctx.store.request.get(request_id)
        if request is None or request.status == RequestStatus.CLOSED:
            await state.clear()
            await message.answer("Запрос не найден или уже закрыт.")
            return

        try:
            await message.copy_to(chat_id=request.user_id)
        except Exception as error:
            ctx.logger.exception(
                "Support answer copy failed request_id=%s user_id=%s",
                request.id,
                request.user_id,
            )
            await message.answer(f"Не получилось отправить это сообщение пользователю: {error}")
            return

        question_id = ctx.store.question.create(
            user_id=None,
            author_type="operator",
            text=message_history_text(message),
            telegram_chat_id=message.chat.id,
            telegram_message_id=message.message_id,
            content_type=message_content_type(message),
            previous_question=request.last_message_id,
            request=request.id,
        )
        ctx.store.request.update(
            request.id,
            status=RequestStatus.OPERATOR,
            last_message_id=question_id,
        )

        await state.clear()
        await message.answer(f"Ответ отправлен пользователю {request.user_id}.")
        ctx.logger.info("Support answered request_id=%s user_id=%s", request.id, request.user_id)

    @router.callback_query(F.data.startswith("support:close:"))
    async def close_request(callback: CallbackQuery, ctx: TelegramContext, state: FSMContext) -> None:
        if not await _is_allowed(callback, ctx):
            return
        await state.clear()
        request_id = int(callback.data.rsplit(":", 1)[-1])
        request = ctx.store.request.get(request_id)
        if request is None:
            await callback.answer("Запрос не найден", show_alert=True)
            return
        ctx.store.request.delete_with_questions(request_id)
        await edit_or_send(callback.message, f"Запрос #{request_id} закрыт.")
        await callback.answer()

    return router


async def _send_open_requests(message: Message, ctx: TelegramContext, page: int) -> None:
    page = max(page, 0)
    requests = ctx.store.request.list_open(limit=PAGE_SIZE, offset=page * PAGE_SIZE)
    if not requests:
        await edit_or_send(message, "Открытых запросов нет.")
        return
    await edit_or_send(
        message,
        "Открытые запросы:",
        reply_markup=keyboard.open_requests_kb(requests, page=page, page_size=PAGE_SIZE),
    )


async def _send_request_history(message: Message, ctx: TelegramContext, request_id: int, page: int | None = None) -> None:
    request = ctx.store.request.get(request_id)
    if request is None:
        await edit_or_send(message, "Запрос не найден.")
        return

    questions = ctx.store.question.list_by_request(request.id)
    pages = _build_history_pages(questions)
    total_pages = max(len(pages), 1)
    page = total_pages - 1 if page is None else min(max(page, 0), total_pages - 1)
    lines = [
        f"Запрос #{request.id}",
        f"Пользователь: {request.user_id}",
        f"Статус: {status_label(request.status)}",
        f"Страница: {page + 1}/{total_pages}",
        "",
    ]

    if not pages:
        lines.append("Сообщений пока нет.")
    else:
        history_page = pages[page]
        question_text = (
            _question_text(history_page.question)
            if history_page.question is not None
            else "Нет вопроса пользователя."
        )
        lines.extend(
            [
                "Вопрос пользователя:",
                question_text,
                "",
                "Ответ:",
            ]
        )
        if not history_page.answers:
            lines.append("Ответа пока нет.")
        else:
            for answer in history_page.answers:
                lines.extend([f"{author_label(answer.author_type)}:", _question_text(answer)])

    await edit_or_send(
        message,
        "\n".join(lines),
        reply_markup=keyboard.request_actions_kb(
            request.id,
            page=page,
            total_pages=total_pages,
            has_attachments=bool(pages and _page_attachments(pages[page])),
        ),
    )


def _build_history_pages(questions: list[QuestionsTable]) -> list[HistoryPage]:
    pages: list[HistoryPage] = []
    current_page: HistoryPage | None = None
    for question in questions:
        if question.author_type == "user":
            current_page = HistoryPage(question=question, answers=[])
            pages.append(current_page)
            continue

        if current_page is None:
            current_page = HistoryPage(question=None, answers=[])
            pages.append(current_page)
        current_page.answers.append(question)
    return pages


def _page_attachments(page: HistoryPage) -> list[QuestionsTable]:
    messages = [page.question, *page.answers]
    return [message for message in messages if message is not None and _has_attachment(message)]


def _has_attachment(question: QuestionsTable) -> bool:
    return bool(
        question.telegram_chat_id
        and question.telegram_message_id
        and question.content_type
        and question.content_type != "text"
    )


async def _copy_history_message(message: Message, ctx: TelegramContext, question: QuestionsTable) -> bool:
    if not question.telegram_chat_id or not question.telegram_message_id:
        return False
    try:
        await message.bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=question.telegram_chat_id,
            message_id=question.telegram_message_id,
        )
    except Exception:
        ctx.logger.exception(
            "Failed to copy history message question_id=%s chat_id=%s message_id=%s",
            question.id,
            question.telegram_chat_id,
            question.telegram_message_id,
        )
        return False
    return True


def _question_text(question: QuestionsTable) -> str:
    return question.text or "[Пустое сообщение]"
