from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.reply import admin_menu_keyboard, executor_menu_keyboard

from database import Database

router = Router()

# Машина состояний для авторизации
class AuthFSM(StatesGroup):
    waiting_for_phone = State()

async def send_menu(message: Message, db: Database):
    """Отправляет пользователю меню в зависимости от его роли."""
    user = db.get_user_by_id(message.from_user.id)
    if user:
        if user['role'] == 'admin':
            await message.answer("Админ-меню:", reply_markup=admin_menu_keyboard)
        elif user['role'] == 'executor':
            await message.answer("Меню исполнителя:", reply_markup=executor_menu_keyboard)
        else:
            await message.answer("Неизвестная роль.", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer("Пользователь не найден.", reply_markup=ReplyKeyboardRemove())

# Кнопка для запроса номера телефона
request_phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]
    ],
    resize_keyboard=True
)

# Обработчик команды /start
@router.message(F.text == "/start")
async def start_handler(message: Message, state: FSMContext):
    await message.answer(
        "Добро пожаловать! Пожалуйста, отправьте ваш номер телефона для авторизации.",
        reply_markup=request_phone_keyboard
    )
    await state.set_state(AuthFSM.waiting_for_phone)

@router.message(F.contact)
async def handle_phone_number(message: Message, db: Database, state: AuthFSM):
    """
    Обработчик получения номера телефона. Проверяет, зарегистрирован ли пользователь.
    Если зарегистрирован, открывает меню в зависимости от роли.
    Если не зарегистрирован, предлагает выбрать роль.
    """
    user_id = message.from_user.id
    username = f'@{message.from_user.username}' or "Не указано"
    name = message.from_user.full_name
    phone_number = message.contact.phone_number

    # Проверяем, зарегистрирован ли пользователь
    user = db.get_user_by_id(user_id=user_id)
    if user:
        # Пользователь уже зарегистрирован, переходим к его меню по роли
        role = user["role"]
        if role == "admin":
            await message.answer("Добро пожаловать обратно, "+user['name']+"!", reply_markup=admin_menu_keyboard)
        elif role == "executor":
            await message.answer("Добро пожаловать обратно, "+user['name']+"!", reply_markup=executor_menu_keyboard)
        return
    
    # if phone_number == "998998666975":
    if phone_number == "998938869216":
        db.register_user(user_id=user_id, username=username, name=name, phone_number=phone_number, birth_date=None, role="admin")
        await message.answer(f"Добро пожаловать в Admin-меню!", 
                         reply_markup=admin_menu_keyboard)
    else:
        db.register_user(user_id=user_id, username=username, name=name, phone_number=phone_number, birth_date=None, role="executor")
        await message.answer(f"Добро пожаловать в меню исполнителя!\n\n(если вы админ, то свяжитесь с текущим админом что бы вас назначили админом)\n\n", 
                         reply_markup=executor_menu_keyboard)

    # await message.answer(
    #     "Спасибо! Пожалуйста, выберите вашу роль:", 
    #     reply_markup=role_selection_keyboard
    # )
    
    # await state.set_state(AuthFSM.waiting_for_role)
    await state.clear()

 