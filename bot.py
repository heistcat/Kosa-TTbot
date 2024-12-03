import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from database import Database
from handlers import common, admin, executor

API_TOKEN = "7300885902:AAHp99Wki_VnVmKco65G4uj7DUyXm2h880A"  # Замените на токен вашего бота
DB_PATH = "database.db"  # Путь к базе данных

async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Подключение базы данных
    db = Database(DB_PATH)

    # Регистрация обработчиков
    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(executor.router)

    # Передача базы данных в хендлеры
    dp["db"] = db

    # Запуск бота
    try:
        print("Бот запущен!")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
