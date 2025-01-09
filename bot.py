# bot.py
import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from database import Database
from handlers import common, admin, executor
from dotenv import load_dotenv


load_dotenv()

API_TOKEN_TEST = os.getenv("API_TOKEN_TEST")  # Get your token from .env
API_TOKEN_PROD = os.getenv("API_TOKEN_PROD")
DB_PATH = "database.db"
instance = Bot(token=API_TOKEN_TEST)  # Create an instance of the Bot class
CHANNEL_ID = os.getenv("CHANNEL_ID")


async def main():
    dp = Dispatcher(storage=MemoryStorage())
    db = Database(DB_PATH)
    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(executor.router)
    dp["db"] = db


    try:
        print("Бот запущен!")
        await dp.start_polling(instance)
    finally:
        await instance.session.close()

if __name__ == "__main__":
    asyncio.run(main())