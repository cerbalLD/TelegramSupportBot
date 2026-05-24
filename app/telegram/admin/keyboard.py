from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def admin_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Открытые запросы")],
            [
                KeyboardButton(text="Добавить support"),
                KeyboardButton(text="Удалить support"),
            ],
            [KeyboardButton(text="Отмена")],
        ],
        resize_keyboard=True,
    )
