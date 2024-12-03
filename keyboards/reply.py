from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Клавиатура для выбора роли
role_selection_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Админ")],
        [KeyboardButton(text="Исполнитель")]
    ],
    resize_keyboard=True
)

# Меню админа
admin_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Создать задачу")],
        [KeyboardButton(text="Просмотр задач")],
        [KeyboardButton(text="Статистика")]
    ],
    resize_keyboard=True
)

skip_photo = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Пропустить")]
    ],
    resize_keyboard=True
)

# Меню исполнителя
executor_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Мои задачи")],
        [KeyboardButton(text="Завершенные задачи")],
        [KeyboardButton(text="Моя статистика")]
    ],
    resize_keyboard=True
)

