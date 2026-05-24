from config import TELEGRAM_ADMIN_USER_IDS
from store.models import UsersTable


def is_admin_user(user: UsersTable | None, telegram_user_id: int) -> bool:
    return telegram_user_id in TELEGRAM_ADMIN_USER_IDS
