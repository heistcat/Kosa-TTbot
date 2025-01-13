# bot.py
import asyncio
from datetime import datetime, timedelta
import os
import time
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from database import Database
from handlers import common, admin, executor
from dotenv import load_dotenv

from utils import send_channel_message
os.environ['TZ'] = 'Etc/GMT-5'
time.tzset() # Обновляем информацию о таймзоне



load_dotenv()

API_TOKEN_TEST = os.getenv("API_TOKEN_TEST")  # Get your token from .env
API_TOKEN_PROD = os.getenv("API_TOKEN_PROD")
DB_PATH = "database/database.db"
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
                print(f"{deadline} - {now} = {time_left} for task: {task['title']}")

                if time_left <= timedelta(hours=24) and time_left > timedelta(hours=2):
                    notification_type = "1day"
                    if task['assigned_to']:
                        for user_id in task['assigned_to'].split(','):
                            user_id = int(user_id)
                            if not db.check_task_notification(task['id'], user_id, task['deadline'], notification_type):
                                try:
                                    await bot.send_message(
                                        chat_id=user_id,
                                        text=(
                                            f"⏰ <b>Напоминание:</b>\n"
                                            f"У вас осталось меньше <b>1 дня</b> до дедлайна задачи:\n"
                                            f"🔖 <b>Название:</b> {task['title']}\n"
                                        ),
                                        parse_mode="HTML"
                                    )
                                    print(f"Отправлено уведомление пользователю {user_id} по задаче {task['title']} за 1 день")
                                    db.add_task_notification(task['id'], user_id, task['deadline'], notification_type)

                                except Exception as e:
                                    print(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
                elif time_left <= timedelta(hours=2) and time_left > timedelta(minutes=30):
                    notification_type = "2hours"
                    if task['assigned_to']:
                        for user_id in task['assigned_to'].split(','):
                            user_id = int(user_id)
                            if not db.check_task_notification(task['id'], user_id, task['deadline'], notification_type):
                                try:
                                    await bot.send_message(
                                        chat_id=user_id,
                                        text=(
                                            f"⏰ <b>Напоминание:</b>\n"
                                            f"У вас осталось меньше <b>2 часов</b> до дедлайна задачи:\n"
                                            f"🔖 <b>Название:</b> {task['title']}\n"
                                        ),
                                        parse_mode="HTML"
                                    )
                                    print(f"Отправлено уведомление пользователю {user_id} по задаче {task['title']} за 2 часа")
                                    db.add_task_notification(task['id'], user_id, task['deadline'], notification_type)

                                except Exception as e:
                                    print(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
                elif time_left <= timedelta(minutes=30) and time_left > timedelta(minutes=0):
                    notification_type = "30min"
                    if task['assigned_to']:
                        for user_id in task['assigned_to'].split(','):
                            user_id = int(user_id)
                            if not db.check_task_notification(task['id'], user_id, task['deadline'], notification_type):
                                try:
                                    await bot.send_message(
                                        chat_id=user_id,
                                        text=(
                                            f"⏰ <b>Напоминание:</b>\n"
                                            f"У вас осталось меньше <b>30 минут</b> до дедлайна задачи:\n"
                                            f"🔖 <b>Название:</b> {task['title']}\n"
                                        ),
                                        parse_mode="HTML"
                                    )
                                    print(f"Отправлено уведомление пользователю {user_id} по задаче {task['title']} за 30 минут")
                                    db.add_task_notification(task['id'], user_id, task['deadline'], notification_type)
                                except Exception as e:
                                    print(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
        await asyncio.sleep(90)  # Проверяем каждую минуту
        print("Проверка дедлайнов...")

async def reset_scores_yearly(bot: Bot, db: Database):
    """Обнуляет баллы всех пользователей в начале каждого года."""
    while True:
        now = datetime.now()
        if now.month <= 2 and now.day == 1 and now.hour == 0 and now.minute == 0:
            db.reset_all_scores()
            print("Баллы всех пользователей обнулены!")
            
            admin_users = db.get_all_users()
            if admin_users:
                for user in admin_users:
                    if user['role'] == 'Админ':
                        try:
                            await bot.send_message(
                                chat_id=user['user_id'],
                                text="🎉 <b>Баллы всех пользователей обнулены!</b>\n\nНачинаем новый год с новыми баллами!",
                                parse_mode="HTML"
                            )
                        except Exception as e:
                            print(f"Не удалось отправить уведомление админу {user['user_id']}: {e}")
                        break
            
            # Отправка уведомления в общий канал
            task_text = "🎉 <b>Баллы всех пользователей обнулены!</b>\n\nНачинаем новый год с новыми баллами!"
            await send_channel_message(bot, CHANNEL_ID, task_text)

            await asyncio.sleep(60)  # Ждем 1 минуту, чтобы не обнулять баллы несколько раз
        await asyncio.sleep(86400)  # Проверяем каждую минуту

async def create_default_tariffs(db: Database):
    """Создает дефолтные тарифы, если их нет."""
    default_tariffs = [
        {"tariff_name": "day_early", "time_threshold": 86400, "score": 50},
        {"tariff_name": "6hours_early", "time_threshold": 21600, "score": 15},
        {"tariff_name": "hour_early", "time_threshold": 3600, "score": 10},
        {"tariff_name": "15min_late", "time_threshold": 900, "score": 0},
        {"tariff_name": "30min_late", "time_threshold": 1800, "score": 10},
        {"tariff_name": "hour_late", "time_threshold": 3600, "score": 30},
    ]
    for tariff in default_tariffs:
        if not db.get_tariff(tariff['tariff_name']):
            db.create_tariff(tariff['tariff_name'], tariff['time_threshold'], tariff['score'])
            print(f"Создан тариф: {tariff['tariff_name']}")


async def main():
    dp = Dispatcher(storage=MemoryStorage())
    db = Database(DB_PATH)
    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(executor.router)
    dp["db"] = db

    # Создаем дефолтные тарифы
    await create_default_tariffs(db)


    # Запускаем функцию обнуления баллов в фоновом режиме
    asyncio.create_task(reset_scores_yearly(instance, db))


    try:
        print("Бот запущен!")
        asyncio.create_task(check_deadlines(instance, db)) # Запускаем проверку дедлайнов
        await dp.start_polling(instance)
    finally:
        await instance.session.close()

if __name__ == "__main__":
    asyncio.run(main())
