from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.reply import role_selection_keyboard, admin_menu_keyboard, executor_menu_keyboard


from database import Database

router = Router()

# Машина состояний для авторизации
class AuthFSM(StatesGroup):
    waiting_for_phone = State()
    waiting_for_role = State()

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

    # Если пользователь не зарегистрирован, добавляем его в базу
    db.register_user(user_id=user_id, username=username, name=name, phone_number=phone_number, birth_date=None, role=None)
    await message.answer(
        "Спасибо! Пожалуйста, выберите вашу роль:", 
        reply_markup=role_selection_keyboard
    )
    await state.set_state(AuthFSM.waiting_for_role)

 

# Обработчик выбора роли
@router.message(F.text.in_(["Админ", "Исполнитель"]), AuthFSM.waiting_for_role)
async def handle_role_selection(message: Message, state: FSMContext, db: Database):
    user_id = message.from_user.id
    role = "admin" if message.text == "Админ" else "executor"

    # Обновление роли в базе данных
    db.update_user_role(user_id, role)

    await state.clear()

    # Перенаправляем на соответствующее меню
    if role == "admin":
        await message.answer("Добро пожаловать в админ-меню!", reply_markup=admin_menu_keyboard)
    else:
        await message.answer("Добро пожаловать в меню исполнителя!", reply_markup=executor_menu_keyboard)

