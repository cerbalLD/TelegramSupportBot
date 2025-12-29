import asyncio
import sys

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery

import core
import markup

# ----------------- FSM состояния -----------------

class AgentStates(StatesGroup):
    waiting_for_password = State()
    waiting_for_agent_id = State()


class RequestStates(StatesGroup):
    waiting_for_new_request = State()
    waiting_for_additional_message = State()


router = Router()


# ----------------- /agent -----------------

@router.message(Command("agent"), StateFilter(None))
async def cmd_agent(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if core.check_agent_status(user_id) is True:
        await message.answer(
            "🔑 Вы авторизованы как Агент поддержки",
            parse_mode="HTML",
            reply_markup=markup.markup_agent()
        )
    else:
        await message.answer(
            "⚠️ Тебя нет в базе. Отправь одноразовый пароль доступа.",
            reply_markup=markup.markup_cancel()
        )
        await state.set_state(AgentStates.waiting_for_password)


# ожидание пароля агента
@router.message(AgentStates.waiting_for_password)
async def get_password_message(message: Message, state: FSMContext):
    password = message.text
    user_id = message.from_user.id

    # не текст
    if password is None:
        await message.answer(
            "⚠️ Вы отправляете не текст. Попробуйте еще раз.",
            reply_markup=markup.markup_cancel()
        )
        return

    # отмена
    if password.lower() == "отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=markup.markup_main())
        return

    # корректный пароль
    if core.valid_password(password) is True:
        core.delete_password(password)
        core.add_agent(user_id)

        await state.clear()
        await message.answer(
            "🔑 Вы авторизованы как Агент поддержки",
            parse_mode="HTML",
            reply_markup=markup.markup_main()
        )
        await message.answer(
            "Выберите раздел технической панели:",
            parse_mode="HTML",
            reply_markup=markup.markup_agent()
        )
    else:
        await message.answer(
            "⚠️ Неверный пароль. Попробуй ещё раз.",
            reply_markup=markup.markup_cancel()
        )


# ----------------- /admin -----------------

@router.message(Command("admin"), StateFilter(None))
async def cmd_admin(message: Message):
    user_id = message.from_user.id

    # как в старом боте: один главный админ
    if str(user_id) == str(config.ADMIN_ID):
        await message.answer(
            "🔑 Вы авторизованы как Админ",
            reply_markup=markup.markup_admin()
        )
    else:
        await message.answer("🚫 Эта команда доступна только администратору.")


# ----------------- Главное меню: текстовые кнопки -----------------

# ✏️ Написать запрос
@router.message(StateFilter(None), F.text == "✏️ Написать запрос")
async def menu_new_request(message: Message, state: FSMContext):
    await message.answer(
        "Введите свой запрос и наши сотрудники скоро с вами свяжутся.",
        reply_markup=markup.markup_cancel()
    )
    await state.set_state(RequestStates.waiting_for_new_request)


# ✉️ Мои запросы
@router.message(StateFilter(None), F.text == "✉️ Мои запросы")
async def menu_my_requests(message: Message):
    user_id = message.from_user.id

    markup_req, value = markup.markup_reqs(user_id, "my_reqs", "1")

    if value == 0:
        await message.answer(
            "У вас пока ещё нет запросов.",
            reply_markup=markup.markup_main()
        )
    else:
        await message.answer(
            "Ваши запросы:",
            reply_markup=markup_req
        )


# Любой другой текст вне FSM — просто вернуть в главное меню
@router.message(StateFilter(None), F.text)
async def fallback_to_main_menu(message: Message):
    await message.answer(
        "Вы возвращены в главное меню.",
        parse_mode="HTML",
        reply_markup=markup.markup_main()
    )


# ----------------- Создание нового запроса -----------------

@router.message(RequestStates.waiting_for_new_request)
async def get_new_request(message: Message, state: FSMContext):
    user_id = message.from_user.id
    request_text = message.text

    check_file = core.get_file(message)  # твоя функция: file_id, file_name, type, text

    # ----- Если пользователь отправляет файл -----
    if check_file is not None:
        file_id = check_file["file_id"]
        file_name = check_file["file_name"]
        file_type = check_file["type"]
        request_text = check_file["text"]

        if str(request_text) == "None":
            await message.answer(
                "⚠️ Вы не ввели ваш запрос. Попробуйте ещё раз, отправив текст вместе с файлом.",
                reply_markup=markup.markup_cancel()
            )
            return

        # создаём запрос
        req_id = core.new_req(user_id, request_text)
        core.add_file(req_id, file_id, file_name, file_type)

        await state.clear()
        await message.answer(
            f"✅ Ваш запрос под ID {req_id} создан. "
            f"Посмотреть текущие запросы можно нажав кнопку <b>Мои текущие запросы</b>",
            parse_mode="HTML",
            reply_markup=markup.markup_main()
        )
        return

    # ----- Если только текст -----
    if request_text is None:
        await message.answer(
            "⚠️ Отправляемый вами тип данных не поддерживается в боте. "
            "Попробуйте еще раз отправить ваш запрос, использовав один из доступных типов данных "
            "(текст, файлы, фото, видео, аудио, голосовые сообщения)",
            reply_markup=markup.markup_cancel()
        )
        return

    if request_text.lower() == "отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=markup.markup_main())
        return

    req_id = core.new_req(user_id, request_text)
    await state.clear()
    await message.answer(
        f"✅ Ваш запрос под ID {req_id} создан. "
        f"Посмотреть текущие запросы можно нажав кнопку <b>Мои текущие запросы</b>",
        parse_mode="HTML",
        reply_markup=markup.markup_main()
    )


# ----------------- Дополнительное сообщение в запрос -----------------

@router.message(RequestStates.waiting_for_additional_message)
async def get_additional_message(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    req_id: str = data["req_id"]
    status: str = data["status"]

    additional_message = message.text
    check_file = core.get_file(message)

    file_id = None
    file_type = None

    # Если есть файл
    if check_file is not None:
        file_id = check_file["file_id"]
        file_name = check_file["file_name"]
        file_type = check_file["type"]
        additional_message = check_file["text"]

        core.add_file(req_id, file_id, file_name, file_type)

    # Неподдерживаемый тип
    if additional_message is None:
        await message.answer(
            "⚠️ Отправляемый вами тип данных не поддерживается в боте. "
            "Попробуйте еще раз отправить ваше сообщение, использовав один из доступных типов данных "
            "(текст, файлы, фото, видео, аудио, голосовые сообщения).",
            reply_markup=markup.markup_cancel()
        )
        return

    # отмена
    if additional_message.lower() == "отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=markup.markup_main())
        return

    # сохраняем сообщение в истории
    if additional_message != "None":
        core.add_message(req_id, additional_message, status)

    # текст пользователю
    if check_file is not None:
        if additional_message != "None":
            text = "✅ Ваш файл и сообщение успешно отправлены!"
        else:
            text = "✅ Ваш файл успешно отправлен!"
    else:
        text = "✅ Ваше сообщение успешно отправлено!"

    await state.clear()
    await message.answer(text, reply_markup=markup.markup_main())

    # если отвечает агент — уведомляем пользователя
    if status == "agent":
        user_id = core.get_user_id_of_req(req_id)
        try:
            notify_text = additional_message
            if notify_text == "None":
                notify_text = ""

            await bot.send_message(
                user_id,
                f"⚠️ Получен новый ответ на ваш запрос ID {req_id}!\n\n"
                f"🧑‍💻 Ответ агента поддержки:\n{notify_text}",
                reply_markup=markup.markup_main()
            )

            if check_file is not None and file_id is not None:
                if file_type == "photo":
                    await bot.send_photo(user_id, photo=file_id, reply_markup=markup.markup_main())
                elif file_type == "document":
                    await bot.send_document(user_id, document=file_id, reply_markup=markup.markup_main())
                elif file_type == "video":
                    await bot.send_video(user_id, video=file_id, reply_markup=markup.markup_main())
                elif file_type == "audio":
                    await bot.send_audio(user_id, audio=file_id, reply_markup=markup.markup_main())
                elif file_type == "voice":
                    await bot.send_voice(user_id, voice=file_id, reply_markup=markup.markup_main())
        except Exception:
            # глушим все, как в старой версии
            pass


# ----------------- CallbackQuery (inline-кнопки) -----------------

@router.callback_query()
async def callback_inline(call: CallbackQuery, state: FSMContext, bot: Bot):
    if call.message is None or call.data is None:
        await call.answer()
        return

    user_id = call.message.chat.id
    data = call.data

    # --- списки запросов (мои / ожидают и т.п.) ---
    if (
        "my_reqs:" in data
        or "waiting_reqs:" in data
        or "answered_reqs:" in data
        or "confirm_reqs:" in data
    ):
        parts = data.split(":")
        callback_key = parts[0]
        number = parts[1]

        markup_req, value = markup.markup_reqs(user_id, callback_key, number)

        if value == 0:
            await call.message.answer(
                "⚠️ Запросы не обнаружены.",
                reply_markup=markup.markup_main()
            )
            await call.answer()
            return

        try:
            await call.message.edit_text(
                "Нажмите на запрос, чтобы посмотреть историю переписки, либо добавить сообщение:",
                reply_markup=markup_req
            )
        except Exception:
            await call.message.answer(
                "Ваши запросы:",
                reply_markup=markup_req
            )

        await call.answer()
        return

    # --- открыть запрос ---
    if data.startswith("open_req:"):
        parts = data.split(":")
        req_id = parts[1]
        callback_key = parts[2]

        req_status = core.get_req_status(req_id)
        request_data = core.get_request_data(req_id, callback_key)
        len_req_data = len(request_data)

        i = 1
        for block in request_data:
            if i == len_req_data:
                markup_req = markup.markup_request_action(req_id, req_status, callback_key)
            else:
                markup_req = None

            await call.message.answer(
                block,
                parse_mode="HTML",
                reply_markup=markup_req
            )
            i += 1

        await call.answer()
        return

    # --- добавить сообщение в запрос ---
    if data.startswith("add_message:"):
        parts = data.split(":")
        req_id = parts[1]
        status_user = parts[2]

        await call.message.answer(
            "Отправьте ваше сообщение, использовав один из доступных типов данных "
            "(текст, файлы, фото, видео, аудио, голосовые сообщения)",
            reply_markup=markup.markup_cancel()
        )

        await state.set_state(RequestStates.waiting_for_additional_message)
        await state.update_data(req_id=req_id, status=status_user)

        await call.answer()
        return

    # --- завершить запрос ---
    if data.startswith("confirm_req:"):
        parts = data.split(":")
        confirm_status = parts[1]
        req_id = parts[2]

        if core.get_req_status(req_id) == "confirm":
            await call.message.answer(
                "⚠️ Этот запрос уже завершен.",
                reply_markup=markup.markup_main()
            )
            await call.answer()
            return

        if confirm_status == "wait":
            await call.message.answer(
                "Для завершения запроса - нажмите кнопку <b>Подтвердить</b>",
                parse_mode="HTML",
                reply_markup=markup.markup_confirm_req(req_id)
            )
        elif confirm_status == "true":
            core.confirm_req(req_id)
            try:
                await call.message.edit_text(
                    "✅ Запрос успешно завершён.",
                    reply_markup=markup.markup_main()
                )
            except Exception:
                await call.message.answer(
                    "✅ Запрос успешно завершён.",
                    reply_markup=markup.markup_main()
                )

        await call.answer()
        return

    # --- файлы запроса ---
    if data.startswith("req_files:"):
        parts = data.split(":")
        req_id = parts[1]
        callback_key = parts[2]
        number = parts[3]

        markup_files, value = markup.markup_files(number, req_id, callback_key)

        if value == 0:
            await call.message.answer(
                "⚠️ Файлы не обнаружены.",
                reply_markup=markup.markup_main()
            )
            await call.answer()
            return

        try:
            await call.message.edit_text(
                "Нажмите на файл, чтобы получить его.",
                reply_markup=markup_files
            )
        except Exception:
            await call.message.answer(
                "Нажмите на файл, чтобы получить его.",
                reply_markup=markup_files
            )

        await call.answer()
        return

    # --- отправить файл ---
    if data.startswith("send_file:"):
        parts = data.split(":")
        file_row_id = parts[1]
        file_type = parts[2]

        file_id = core.get_file_id(file_row_id)

        if file_type == "photo":
            await bot.send_photo(call.message.chat.id, photo=file_id, reply_markup=markup.markup_main())
        elif file_type == "document":
            await bot.send_document(call.message.chat.id, document=file_id, reply_markup=markup.markup_main())
        elif file_type == "video":
            await bot.send_video(call.message.chat.id, video=file_id, reply_markup=markup.markup_main())
        elif file_type == "audio":
            await bot.send_audio(call.message.chat.id, audio=file_id, reply_markup=markup.markup_main())
        elif file_type == "voice":
            await bot.send_voice(call.message.chat.id, voice=file_id, reply_markup=markup.markup_main())

        await call.answer()
        return

    # --- назад в панель агента ---
    if data == "back_agent":
        try:
            await call.message.edit_text(
                "🔑 Вы авторизованы как Агент поддержки",
                parse_mode="HTML",
                reply_markup=markup.markup_agent()
            )
        except Exception:
            await call.message.answer(
                "🔑 Вы авторизованы как Агент поддержки",
                parse_mode="HTML",
                reply_markup=markup.markup_agent()
            )
        await call.answer()
        return

    # --- назад в панель админа ---
    if data == "back_admin":
        try:
            await call.message.edit_text(
                "🔑 Вы авторизованы как Админ",
                parse_mode="HTML",
                reply_markup=markup.markup_admin()
            )
        except Exception:
            await call.message.answer(
                "🔑 Вы авторизованы как Админ",
                parse_mode="HTML",
                reply_markup=markup.markup_admin()
            )
        await call.answer()
        return

    # --- добавить агента ---
    if data == "add_agent":
        await call.message.answer(
            "Чтобы добавить агента поддержки - введите его ID Telegram.",
            reply_markup=markup.markup_cancel()
        )
        await state.set_state(AgentStates.waiting_for_agent_id)
        await call.answer()
        return

    # --- все агенты ---
    if data.startswith("all_agents:"):
        number = data.split(":")[1]
        markup_agents, len_agents = markup.markup_agents(number)

        if len_agents == 0:
            await call.message.answer(
                "⚠️ Агенты не обнаружены.",
                reply_markup=markup.markup_main()
            )
            await call.answer()
            return

        try:
            await call.message.edit_text(
                "Нажмите на агента поддержки, чтобы удалить его",
                parse_mode="HTML",
                reply_markup=markup_agents
            )
        except Exception:
            await call.message.answer(
                "Нажмите на агента поддержки, чтобы удалить его",
                parse_mode="HTML",
                reply_markup=markup_agents
            )

        await call.answer()
        return

    # --- удалить агента ---
    if data.startswith("delete_agent:"):
        agent_id = data.split(":")[1]
        core.delete_agent(agent_id)

        try:
            await call.message.edit_text(
                "Нажмите на агента поддержки, чтобы удалить его",
                parse_mode="HTML",
                reply_markup=markup.markup_agents("1")[0]
            )
        except Exception:
            await call.message.answer(
                "Нажмите на агента поддержки, чтобы удалить его",
                parse_mode="HTML",
                reply_markup=markup.markup_agents("1")[0]
            )

        await call.answer()
        return

    # --- все пароли ---
    if data.startswith("all_passwords:"):
        number = data.split(":")[1]
        markup_passwords, len_passwords = markup.markup_passwords(number)

        if len_passwords == 0:
            await call.message.answer(
                "⚠️ Пароли не обнаружены.",
                reply_markup=markup.markup_main()
            )
            await call.answer()
            return

        try:
            await call.message.edit_text(
                "Нажмите на пароль, чтобы удалить его",
                parse_mode="HTML",
                reply_markup=markup_passwords
            )
        except Exception:
            await call.message.answer(
                "Нажмите на пароль, чтобы удалить его",
                parse_mode="HTML",
                reply_markup=markup_passwords
            )

        await call.answer()
        return

    # --- удалить пароль ---
    if data.startswith("delete_password:"):
        password = data.split(":")[1]
        core.delete_password(password)

        try:
            await call.message.edit_text(
                "Нажмите на пароль, чтобы удалить его",
                parse_mode="HTML",
                reply_markup=markup.markup_passwords("1")[0]
            )
        except Exception:
            await call.message.answer(
                "Нажмите на пароль, чтобы удалить его",
                parse_mode="HTML",
                reply_markup=markup.markup_passwords("1")[0]
            )

        await call.answer()
        return

    # --- сгенерировать пароли ---
    if data == "generate_passwords":
        passwords = core.generate_passwords(10, 16)
        core.add_passwords(passwords)

        text_passwords = ""
        i = 1
        for p in passwords:
            text_passwords += f"{i}. {p}\n"
            i += 1

        await call.message.answer(
            f"✅ Сгенерировано {i-1} паролей:\n\n{text_passwords}",
            parse_mode="HTML",
            reply_markup=markup.markup_main()
        )
        await call.message.answer(
            "Нажмите на пароль, чтобы удалить его",
            parse_mode="HTML",
            reply_markup=markup.markup_passwords("1")[0]
        )

        await call.answer()
        return

    # --- остановить бота ---
    if data.startswith("stop_bot:"):
        status = data.split(":")[1]

        if status == "wait":
            try:
                await call.message.edit_text(
                    "Вы точно хотите отключить бота?",
                    parse_mode="HTML",
                    reply_markup=markup.markup_confirm_stop()
                )
            except Exception:
                await call.message.answer(
                    "Вы точно хотите отключить бота?",
                    parse_mode="HTML",
                    reply_markup=markup.markup_confirm_stop()
                )
            await call.answer()
            return

        elif status == "confirm":
            try:
                await call.message.edit_text("✅ Бот отключен.")
            except Exception:
                await call.message.answer("✅ Бот отключен.")

            await call.answer()
            # аккуратное завершение
            await bot.session.close()
            raise SystemExit


# ----------------- Запуск бота -----------------

async def main():
    bot = Bot(config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
