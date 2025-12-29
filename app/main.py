import json, os, asyncio
from setup_logger import setup_logger

CONFIG_PATH = os.environ.get("CONFIG_PATH", "./app/config.json")

async def main():
    # запуск логов
    logger = setup_logger("main")

    logger.info("[main] Initialization started...")
    
    # загруска настроек
    if not os.path.isfile(CONFIG_PATH): 
        raise FileNotFoundError("[main] File config.json not found")

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            config = json.load(file)  
            
        # telegram
        bot_token = config['bot_token']
        list_admin_user_id = config['list_admin_user_id']
        user_token = config['user_token']
        
    except Exception as e:
        raise ValueError(f"[main] Invalid config.json file format: {str(e)}") from e
    finally:
        logger.info("[main] Reading settings completed")
        
    # store
    try:
        logger.info("[main] Initializing the database...")
        from store.store import Store
        dp_path = os.environ.get("DB_PATH", "./app/store/db.sqlite")
        store = Store(logger=logger, db_path=dp_path)
        store.init_db()
    except Exception as e:
        raise Exception(f"[main] Error initializing the database: {str(e)}") from e
    finally:
        logger.info("[main] Database initialization completed")
        
    # ai
    try:
        logger.info("[main] Initializing the AI...")
        from ai.DeepSeek import DeepSeek
        ai = DeepSeek(logger=logger, userToken=user_token)
    except Exception as e:
        raise Exception(f"[main] Error initializing the AI: {str(e)}") from e
    finally:
        logger.info("[main] AI initialization completed")
    
    # bot
    try:
        logger.info("[main] bot start...")
        from telegram.bot import TelegramBot
        bot = TelegramBot(
            logger=logger,
            token=bot_token,
            store=store,
            ai=ai,
            list_admin_user_id=list_admin_user_id
            )
    except Exception as e:
        raise Exception(f"[main] Error initializing bot: {str(e)}") from e
    finally:
        logger.info("[main] bot initializing completed")
        
    logger.info("[main] Initialization completed")
    
    await bot.start()
    
    logger.info("[main] END")
    
if __name__ == "__main__":
    asyncio.run(main())