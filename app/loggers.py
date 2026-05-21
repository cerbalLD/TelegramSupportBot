import os
import os.path as path
from logging import Logger

from setup_logger import setup_logger


BASE_PATH = os.getenv("BASE_PATH", "./app/")
LOG_PATH = path.join(BASE_PATH, "log")


def get_logger(name: str) -> Logger:
    return setup_logger(
        name=name,
        save_path=LOG_PATH,
    )
