from aiogram.types import Message


def message_content_type(message: Message) -> str:
    content_type = message.content_type
    return content_type.value if hasattr(content_type, "value") else str(content_type)


def message_history_text(message: Message) -> str:
    if message.text:
        return message.text
    label = message_type_label(message_content_type(message))
    if message.caption:
        return f"[{label}]\n{message.caption}"
    return f"[{label}]"


def message_type_label(content_type: str) -> str:
    return {
        "audio": "Аудио",
        "animation": "Анимация",
        "document": "Документ",
        "photo": "Фото",
        "sticker": "Стикер",
        "video": "Видео",
        "video_note": "Видеосообщение",
        "voice": "Голосовое сообщение",
        "contact": "Контакт",
        "venue": "Место",
        "location": "Геопозиция",
        "poll": "Опрос",
        "dice": "Кубик",
    }.get(content_type, content_type)
