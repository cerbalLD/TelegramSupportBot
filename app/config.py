import os
import os.path as path
import json
from loggers import get_logger

BASE_PATH = os.getenv("BASE_PATH", "./app/")

main_logger = get_logger("main")

config_path = path.join(BASE_PATH, "config.json")
if not path.isfile(config_path):
    raise FileNotFoundError(f"File config.json not found in {config_path}")
try:
    with open(config_path, "r", encoding="utf-8") as file:
        config: dict = json.load(file)

    deepseek = config["deepseek"]
    USER_TOKEN = deepseek["user_token"]

    telegram = config.get("telegram", {})
    TELEGRAM_ADMIN_USER_IDS = telegram["admins_user_id"]
    BOT_TOKEN = telegram["bot_token"]
    PAGE_SIZE = 10

    main_logger.info("Reading settings completed")
except Exception as e:
    raise ValueError(f"Invalid config.json file format: {str(e)}") from e
