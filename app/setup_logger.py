import logging
import os
import sys
from logging import Logger


_CONSOLE_HANDLER_NAME = "autoshorts_console"
_FILE_HANDLER_PREFIX = "autoshorts_file:"


def setup_logger(
    name: str,
    save_path: str,
    console: bool = True,
    file_handler: bool = True,
    propagate: bool = True,
    level: int = logging.INFO,
) -> Logger:
    """Создает лог сервер

    Args:
        name (str): имя сервиса пишущего лог
        save_path (str, optional): путь к папке куда сихранять логи.
        console (bool, optional): Писать ли в консоль.
        file_handler (bool, optional): Писать ли в файл.
        propagate (bool, optional): Передавать ли логи к родителю.
        level (int, optional): Уровень логирования.

    Returns:
        Logger: Готовый логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = propagate

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if console and not _has_named_handler(logger, _CONSOLE_HANDLER_NAME):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.name = _CONSOLE_HANDLER_NAME
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if file_handler:
        os.makedirs(save_path, exist_ok=True)
        file_path = os.path.join(save_path, f"{name}.log")
        handler_name = f"{_FILE_HANDLER_PREFIX}{file_path}"

        if not _has_named_handler(logger, handler_name):
            log_file_handler = logging.FileHandler(file_path, mode="a", encoding="utf-8")
            log_file_handler.name = handler_name
            log_file_handler.setLevel(level)
            log_file_handler.setFormatter(formatter)
            logger.addHandler(log_file_handler)

    return logger


def _has_named_handler(logger: Logger, handler_name: str) -> bool:
    """Проверяет существует ли в логгере хендлер с заданным именем"""
    return any(handler.get_name() == handler_name for handler in logger.handlers)