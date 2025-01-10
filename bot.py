# bot.py
import asyncio
from datetime import datetime, timedelta
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
instance = Bot(token=API_TOKEN_PROD)  # Create an instance of the Bot class
CHANNEL_ID = os.getenv("CHANNEL_ID")


async def check_deadlines(bot: Bot, db: Database):
    """Проверяет дедлайны задач и отправляет уведомления."""
    while True:
        tasks = db.get_all_tasks()
        for task in tasks:
            if task['status'] == 'pending' or task['status'] == 'is_on_work':
                deadline = datetime.fromtimestamp(task['deadline'])
                now = datetime.now()
                time_left = deadline - now

                if time_left <= timedelta(days=1) and time_left > timedelta(hours=24-2):
                    # Уведомление за 1 день
                    if task['assigned_to']:
                        for user_id in task['assigned_to'].split(','):
                            user_id = int(user_id)
                            try:
                                await bot.send_message(
                                    chat_id=user_id,
                                    text=(
                                        f"⏰ <b>Напоминание:</b>\n"
                                        f"У вас остался <b>1 день</b> до дедлайна задачи:\n"
                                        f"🔖 <b>Название:</b> {task['title']}\n"
                                    ),
                                    parse_mode="HTML"
                                )
                            except Exception as e:
                                print(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
                elif time_left <= timedelta(hours=2) and time_left > timedelta(minutes=30):
                     # Уведомление за 2 часа
                    if task['assigned_to']:
                        for user_id in task['assigned_to'].split(','):
                            user_id = int(user_id)
                            try:
                                await bot.send_message(
                                    chat_id=user_id,
                                    text=(
                                        f"⏰ <b>Напоминание:</b>\n"
                                        f"У вас осталось <b>2 часа</b> до дедлайна задачи:\n"
                                        f"🔖 <b>Название:</b> {task['title']}\n"
                                    ),
                                    parse_mode="HTML"
                                )
                            except Exception as e:
                                print(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
                elif time_left <= timedelta(minutes=30) and time_left > timedelta(minutes=0):
                    # Уведомление за 30 минут
                    if task['assigned_to']:
                        for user_id in task['assigned_to'].split(','):
                            user_id = int(user_id)
                            try:
                                await bot.send_message(
                                    chat_id=user_id,
                                    text=(
                                        f"⏰ <b>Напоминание:</b>\n"
                                        f"У вас осталось <b>30 минут</b> до дедлайна задачи:\n"
                                        f"🔖 <b>Название:</b> {task['title']}\n"
                                    ),
                                    parse_mode="HTML"
                                )
                            except Exception as e:
                                print(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
        await asyncio.sleep(1800)  # Проверяем каждую минуту



async def main():
    dp = Dispatcher(storage=MemoryStorage())
    db = Database(DB_PATH)
    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(executor.router)
    dp["db"] = db


    try:
        print("Бот запущен!")
        asyncio.create_task(check_deadlines(instance, db)) # Запускаем проверку дедлайнов
        await dp.start_polling(instance)
    finally:
        await instance.session.close()

if __name__ == "__main__":
    asyncio.run(main())