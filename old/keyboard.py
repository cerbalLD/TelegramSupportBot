# telegram/keyboard.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from store.models import UsersTable, QuestionsTable, PassTable
from typing import Optional
    
def kb_in():
    return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📝 Создать промокоды", callback_data="create_pass"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🖼️ Создать qr code", callback_data="create_qr"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⚙️ Изменить информацию", callback_data="update_event"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="💬 Стартовое сообщение", callback_data="update_start_message"
                    )
                ]
            ]
        )
    
def kb_rp():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Ввести промокод")
            ],
            [
                KeyboardButton(text="Мой билет")
            ]
        ],
        resize_keyboard=True
    )
    
def mainmenu(user: Optional[UsersTable] = None, force: bool = False):
    if (user and (user.is_agent or user.is_admin)) or force:
        keyboard=[
                [
                    InlineKeyboardButton(
                        text="Очередь вопросов", callback_data="queue_questions"
                    )
                ],
        ]
        if force or user.is_admin:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text="Создать агента", callback_data="create_passes"
                    )
                ],
            )
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text="Список агентов", callback_data="list_passes"
                    )
                ],
            )
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
        
    return None
    
def call_operator():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Позвать оператора", callback_data="call_operator"
                )
            ]
        ]
    )
    
def queue_questions(question: list[QuestionsTable], page: int = 0, length: int = 10):
    keyboard=[]
    for i in range(0, min(len(question), length)):
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=question[i].id,
                    callback_data=f"question_{question[i].id}"
                )
            ]
        )
    max_page = len(question)//length+1
    keyboard.append(
        [
            InlineKeyboardButton(
                text="Назад", callback_data=f"queue_questions_page_{max(page-1, 0)}"
            ),
            InlineKeyboardButton(
                text=f"{page}/{max_page}"
            ),
            InlineKeyboardButton(
                text="Вперед", callback_data=f"queue_questions_page_{min(page+1, max_page)}"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def question_menu(question_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Ответить", callback_data=f"answer_question_{question_id}"
                ),
            ]
        ]
    )
    
def cancel():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Отменить", callback_data="cancel"
                )
            ]
        ]
    )
    
def list_passes(passes: list[PassTable], page: int = 0, length: int = 10):
    keyboard=[]
    for i in range(0, min(len(passes), length)):
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=str(passes[i].name),
                    callback_data=f"pass_{passes[i].id}"
                )
            ]
        )
    max_page = len(passes)//length+1
    keyboard.append(
        [
            InlineKeyboardButton(
                text="Назад", callback_data=f"list_passes_page_{max(page-1, 0)}"
            ),
            InlineKeyboardButton(
                text=f"{page+1}/{max_page}", callback_data="None"
            ),
            InlineKeyboardButton(
                text="Вперед", callback_data=f"list_passes_page_{min(page+1, max_page)}"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def pass_menu(pass_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Удалить", callback_data=f"delete_pass_{pass_id}"
                ),
            ]
        ]
    )