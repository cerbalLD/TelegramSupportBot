from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import PAGE_SIZE


def list_menu(elements: list[str], preffix: str, page: int = 0, limit: int = PAGE_SIZE) -> InlineKeyboardMarkup:
    keyboard = []
    for element in elements[limit*page:limit*(page+1)]:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=element,
                    callback_data=f"{preffix}_show_{str(element)}",
                )
            ]
        )
    keyboard.append(
        [
            InlineKeyboardButton(
                text="<",
                callback_data=f"{preffix}_page_{max(page - 1, 0)}",
            ),
            InlineKeyboardButton(text=str(page), callback_data="pass"),
            InlineKeyboardButton(
                text=">", callback_data=f"{preffix}_page_{page + 1}"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
