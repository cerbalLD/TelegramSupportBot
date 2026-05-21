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

    store = config["store"]
    DB_PATH = path.join(BASE_PATH, store["db_name"])

    telegram = config.get("telegram", {})
    PAGE_SIZE = telegram["page_size"]
    BOT_TOKEN = telegram["bot_token"]
    TELEGRAM_ALLOWED_USER_IDS = {
        int(user_id)
        for user_id in telegram.get("allowed_user_ids", [])
    }

    main_logger.info("Reading settings completed")
except Exception as e:
    raise ValueError(f"Invalid config.json file format: {str(e)}") from e
