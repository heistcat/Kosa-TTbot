from database import Database
import os
from aiogram import Bot
from dotenv import load_dotenv
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

load_dotenv()


async def send_channel_message(bot: Bot, channel_id: int, text: str):
    """Отправляет сообщение в общий канал."""
    if not channel_id:
        print("Ошибка: CHANNEL_ID не задан.")
        return
    try:
        await bot.send_message(chat_id=channel_id, text=text, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка при отправке сообщения в канал: {e}")
