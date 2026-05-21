from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def main_menu_kb(permision) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Создать видео")],
            [KeyboardButton(text="Источники")],
            [KeyboardButton(text="Фон")],
            [KeyboardButton(text="YouTube")],
        ],
        resize_keyboard=True,
    )