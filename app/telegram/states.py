from aiogram.fsm.state import State, StatesGroup

class SupportAnswerState(StatesGroup):
    waiting_answer = State()


class AdminSupportState(StatesGroup):
    waiting_add_user_id = State()
    waiting_remove_user_id = State()
