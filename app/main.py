import asyncio
import inspect

from config import (
    BOT_TOKEN,
    USER_TOKEN,
    main_logger,
)
from loggers import get_logger


def try_log(name: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                main_logger.info(f"Initializing the {name}...")
                result = func(*args, **kwargs)
                if inspect.isawaitable(result):
                    result = await result
            except Exception as e:
                raise Exception(
                    f"Error initializing the {name}: {str(e)}"
                ) from e
            else:
                return result
            finally:
                main_logger.info(f"{name} initialization completed")

        return wrapper

    return decorator


@try_log("AI")
def setup_ai():
    from ai.DeepSeek import DeepSeek
    return DeepSeek(logger=main_logger, userToken=USER_TOKEN)


@try_log("Store")
def setup_store():
    from store.store import Store
    store = Store(db_path=r"./store/database.db", logger=main_logger)
    store.init_db()
    return store


def setup_bot(store, ai):
    from telegram.main import TelegramBot
    return TelegramBot(token=BOT_TOKEN, store=store, ai=ai, logger=get_logger("telegram"))


async def start(bot):
    main_logger.info("Running the bot...")
    try:
        await bot.run()
    except Exception as e:
        raise Exception(f"Error running the bot: {str(e)}") from e
    finally:
        main_logger.info("END")


async def main() -> None:
    main_logger.info("Initialization started...")

    ai = await setup_ai()
    store = await setup_store()
    bot = setup_bot(store=store, ai=ai)

    await start(bot)


if __name__ == "__main__":
    asyncio.run(main())
