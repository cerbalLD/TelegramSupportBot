from collections.abc import Sequence

from aiogram import types


PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


async def edit_or_send(
    message: types.Message,
    text: str,
    reply_markup: types.InlineKeyboardMarkup | types.ReplyKeyboardMarkup | None = None,
) -> types.Message:
    try:
        return await message.edit_text(text, reply_markup=reply_markup)
    except Exception:
        return await message.answer(text, reply_markup=reply_markup)


async def edit_or_send_media(
    message: types.Message,
    file_path: str,
    caption: str | None = None,
    reply_markup: types.InlineKeyboardMarkup | None = None,
) -> types.Message:
    try:
        await message.delete()
    except Exception:
        pass

    file = types.FSInputFile(file_path)
    file_type = _get_file_type(file_path)
    if file_type == "photo":
        return await message.answer_photo(file, caption=caption, reply_markup=reply_markup)
    if file_type == "video":
        return await message.answer_video(file, caption=caption, reply_markup=reply_markup)
    return await message.answer_document(file, caption=caption, reply_markup=reply_markup)


async def send_media_group_or_documents(
    message: types.Message,
    file_paths: Sequence[str],
    caption: str | None = None,
) -> None:
    media: list[types.InputMediaPhoto | types.InputMediaVideo] = []
    documents: list[str] = []

    for index, file_path in enumerate(file_paths):
        file = types.FSInputFile(file_path)
        file_type = _get_file_type(file_path)
        item_caption = caption if index == 0 else None
        if file_type == "photo":
            media.append(types.InputMediaPhoto(media=file, caption=item_caption))
        elif file_type == "video":
            media.append(types.InputMediaVideo(media=file, caption=item_caption))
        else:
            documents.append(file_path)

    if media:
        await message.answer_media_group(media)
    for file_path in documents:
        await message.answer_document(types.FSInputFile(file_path))


def _get_file_type(file_path: str) -> str:
    ext = "." + file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
    if ext in PHOTO_EXTS:
        return "photo"
    if ext in VIDEO_EXTS:
        return "video"
    return "document"
