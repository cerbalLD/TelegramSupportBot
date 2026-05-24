from config import TELEGRAM_ADMIN_USER_IDS
from store.models import UsersTable


def is_support_user(user: UsersTable | None, telegram_user_id: int) -> bool:
    if telegram_user_id in TELEGRAM_ADMIN_USER_IDS:
        return True
    if user is None:
        return False
    return bool(user.permissions > 0)


def status_label(status: int) -> str:
    return {
        0: "Открыт",
        1: "Отвечал бот",
        2: "Ждет оператора",
        3: "Закрыт",
    }.get(status, f"Статус {status}")


def author_label(author_type: str) -> str:
    return {
        "user": "Пользователь",
        "ai": "Бот",
        "operator": "Оператор",
    }.get(author_type, author_type)
