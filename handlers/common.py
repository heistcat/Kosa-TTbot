from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
# import bot
from keyboards.reply import admin_menu_keyboard, executor_menu_keyboard, su_menu_keyboard

from database import Database

router = Router()

# Машина состояний для авторизации
class AuthFSM(StatesGroup):
    waiting_for_phone = State()

async def send_menu(message: Message, db: Database):
    """Отправляет пользователю меню в зависимости от его роли."""
    user = db.get_user_by_id(message.from_user.id)
    if user:
        if user['role'] == 'Админ':
            await message.answer("Админ-меню:", reply_markup=admin_menu_keyboard)
        elif user['role'] == 'Исполнитель':
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
    su = db.get_su_by_id(user_id=user_id)
    if user:
        # Пользователь уже зарегистрирован, переходим к его меню по роли
        role = user["role"]
        if role == "Админ":
            await message.answer("Добро пожаловать обратно, "+user['name']+"!", reply_markup=admin_menu_keyboard)
        elif role == "Исполнитель":
            await message.answer("Добро пожаловать обратно, "+user['name']+"!", reply_markup=executor_menu_keyboard)
        
        return
    
    if phone_number == "998938869216":
        db.register_user(user_id=user_id, username=username, name=name, phone_number=phone_number, birth_date=None, role="Админ")
        await message.answer(f"Добро пожаловать в Admin-меню!", 
                         reply_markup=admin_menu_keyboard)
    elif phone_number == "998998666975":
        db.register_user(user_id=user_id, username=username, name=name, phone_number=phone_number, birth_date=None, role="Админ")
        await message.answer(f"Добро пожаловать в Admin-меню!", 
                         reply_markup=admin_menu_keyboard)
    else:
        db.register_user(user_id=user_id, username=username, name=name, phone_number=phone_number, birth_date=None, role="Исполнитель")
        await message.answer(f"Добро пожаловать в меню исполнителя!\n\n(если вы админ, то свяжитесь с текущим админом что бы вас назначили админом)\n\n", 
                         reply_markup=executor_menu_keyboard)

    await state.clear()

@router.message(F.text == "/su")
async def su_handler(message: Message, db: Database):
    su = db.get_su_by_id(user_id=message.from_user.id)
    if su:
        await message.answer("ROOT: Welcome back, buddy!", reply_markup=su_menu_keyboard)
    else:
        user_id = message.from_user.id
        db.register_su(user_id=user_id)
        await message.answer(f"ROOT: Welcome to the club, buddy!\n\n", 
                         reply_markup=su_menu_keyboard)

@router.message(F.text == "/sus")
async def su_handler(message: Message, db: Database):
    sus = db.get_su_by_id(user_id=message.from_user.id)
    if sus:
        db.remove_su(user_id=message.from_user.id)
        
    await message.answer(f"SUS: YOU ARE SUS NOW!\n\n",
                         reply_markup=su_menu_keyboard)


@router.message(F.text.startswith("/su give"))
async def su_give_handler(message: Message, state: FSMContext):
    await message.answer(
        "enter the phone number of the user you want to make",
    )
    await state.set_state(AuthFSM.waiting_for_phone)


@router.message(F.text.startswith("su998"))
async def su_give_handle_phone_number(message: Message, db: Database, state: AuthFSM):
    phone_number = message.text
    user = db.get_user_by_phone_number(phone_number=phone_number)['user_id']

    su = db.get_su_by_id(user_id=user)
    if user == su:
        # bot.send_message(user, "You are already a super user", reply_markup=su_menu_keyboard)
        await message.answer("ROOT: user is SU already!", reply_markup=su_menu_keyboard)
    else :
        db.register_su(user_id=phone_number)
        # bot.send_message(user, "ROOT: Welcome to the club, buddy!", reply_markup=su_menu_keyboard)
        await message.answer(f"ROOT: user is SU now!\n\n",
                        reply_markup=su_menu_keyboard)
        return
    await state.clear()

@router.message(F.text.startswith("/su all"))
async def su_all_handler(message: Message, db: Database):
    sus = db.get_all_sus()
    
    if sus:
        for su in sus:
            user = db.get_user_by_id(user_id=su['user_id'])
            await message.answer(f"ROOT: {su['user_id']} - {user['username']} ({user['name']})")
    else:
        await message.answer("ROOT: No super users found.")

@router.message(F.text.startswith("/su remove"))
async def su_remove_handler(message: Message, state: FSMContext):
    await message.answer(
        "enter the phone number of the user you want to remove",
    )
    await state.set_state(AuthFSM.waiting_for_phone)

@router.message(F.text.startswith("re998"))
async def su_remove_handle_phone_number(message: Message, db: Database, state: AuthFSM):
    phone_number = message.text

    user = db.get_user_by_phone_number(phone_number=phone_number)['user_id']
    su = db.get_su_by_id(user_id=user)
    if user:
        if user == su:
            db.remove_su(user_id=user)
            await message.answer("ROOT: user is not SU anymore!", reply_markup=admin_menu_keyboard if user['role'] == 'Админ' else executor_menu_keyboard)
        else:
            await message.answer("ROOT: user is not SU already!", reply_markup=admin_menu_keyboard if user['role'] == 'Админ' else executor_menu_keyboard)
        return
    await state.clear()