from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from store.models import RequestTable
from telegram.support.utils import status_label


def open_requests_kb(requests: list[RequestTable], page: int, page_size: int) -> InlineKeyboardMarkup:
    keyboard: list[list[InlineKeyboardButton]] = []
    for request in requests:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"#{request.id} | {request.user_id} | {status_label(request.status)}",
                    callback_data=f"support:view:{request.id}",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(text="Назад", callback_data=f"support:list:{max(page - 1, 0)}"),
            InlineKeyboardButton(text=f"Стр. {page + 1}", callback_data="support:noop"),
            InlineKeyboardButton(text="Вперед", callback_data=f"support:list:{page + 1}"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def request_actions_kb(request_id: int, page: int, total_pages: int) -> InlineKeyboardMarkup:
    keyboard: list[list[InlineKeyboardButton]] = []
    if total_pages > 1:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="Назад",
                    callback_data=f"support:history:{request_id}:{page - 1}" if page > 0 else "support:noop",
                ),
                InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="support:noop"),
                InlineKeyboardButton(
                    text="Вперед",
                    callback_data=(
                        f"support:history:{request_id}:{page + 1}"
                        if page < total_pages - 1
                        else "support:noop"
                    ),
                ),
            ]
        )

    keyboard.extend(
        [
            [
                InlineKeyboardButton(text="Ответить", callback_data=f"support:answer:{request_id}"),
                InlineKeyboardButton(text="Закрыть", callback_data=f"support:close:{request_id}"),
            ],
            [InlineKeyboardButton(text="К списку", callback_data="support:list:0")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def cancel_answer_kb(request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отменить", callback_data=f"support:view:{request_id}")],
        ]
    )
