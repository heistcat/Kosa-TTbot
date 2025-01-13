# handlers/admin.py
import os
import time
from aiogram import Router, F, Bot, types
from aiogram.filters import StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.reply import admin_menu_keyboard, skip_photo, executor_menu_keyboard
from keyboards.inline import assign_executor_keyboard, empty_keyboard, role_selection_keyboard, task_admin_keyboard, task_admin_keyboardb, reassign_executor_keyboard, task_admin_redeadline_keyboard, user_list_keyboard
from database import Database
from aiogram.types import CallbackQuery, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from handlers.common import send_menu
from bot import instance as bot, CHANNEL_ID
from utils import send_channel_message
from datetime import datetime

os.environ['TZ'] = 'Etc/GMT-5'
time.tzset() # Обновляем информацию о таймзоне


router = Router()

# Машина состояний для создания задачи
class CreateTaskFSM(StatesGroup):
    title = State()
    description = State()
    deadline = State()
    photo = State()
    assign = State()
    location = State()  # Добавляем состояние для выбора локации
    selected_executors = State()  # Для хранения выбранных исполнителей
    other_location = State() 

#Создаем FSM
class AddCommentFSM(StatesGroup):
    waiting_for_comment = State()
    task_id = State()

    # FSM для изменения дедлайна
class ChangeDeadlineFSM(StatesGroup):
    waiting_for_new_deadline = State()
    task_id = State()

# FSM для управления тарифами
class ManageTariffsFSM(StatesGroup):
    menu = State()
    waiting_for_tariff_name = State()
    waiting_for_time_threshold = State()
    waiting_for_score = State()
    waiting_for_tariff_to_update = State()
    waiting_for_new_time_threshold = State()
    waiting_for_new_score = State()
    waiting_for_tariff_type = State()
    waiting_for_tariff_to_delete = State()


@router.message(F.text, StateFilter(ChangeDeadlineFSM.waiting_for_new_deadline))
async def handle_new_deadline_admin(message: Message, state: FSMContext, db: Database, bot: Bot):
    new_deadline = message.text
    try:
        datetime.strptime(new_deadline, "%d-%m-%Y %H:%M")
        data = await state.get_data()
        task_id = data.get("task_id")
        task = db.get_task_by_id(task_id)
        if task_id and new_deadline:
            db.update_task_deadline(task_id, new_deadline)

            creator = db.get_user_by_id(task['created_by'])['username'] if db.get_user_by_id(task['created_by']) else "Admin"

            
            # Отправка уведомления в общий канал
            task_text = (
                f"⏰ <b>Дедлайн задачи изменен:</b>\n"
                f"🔖 <b>Название:</b> {task['title']}\n"
                f"👤 <b>Изменил:</b> {db.get_user_by_id(message.from_user.id)['username']}( {db.get_user_by_id(message.from_user.id)['role']})\n"
                f"👤 <b>Создатель задачи:</b> {creator}\n"
                f"📅 <b>Новый дедлайн:</b> {new_deadline}\n"
            )
            await send_channel_message(bot, CHANNEL_ID, task_text)

            # Запись в историю
            db.add_task_history_entry(
                task_id=task_id,
                user_id=message.from_user.id,
                action="Дедлайн изменен",
                details=f"Новый дедлайн: {new_deadline}"
            )

            # Удаляем старые уведомления
            db.delete_task_notifications(task_id)

            await message.answer("Дедлайн задачи успешно изменен!")
        else:
            await message.answer("Произошла ошибка при изменении дедлайна.")
        await state.clear()
    except ValueError:
        await message.answer("Неверный формат даты. Пожалуйста, введите дату в формате ДД-ММ-ГГГГ ЧЧ:ММ")
        print(new_deadline)



@router.callback_query(F.data.startswith("approve_redeadline:"))
async def approve_redeadline_handler(callback_query: CallbackQuery, state: FSMContext, db: Database, bot: Bot):
    print(callback_query.data)
    """Обработчик для подтверждения переноса дедлайна."""
    task_id = int(callback_query.data.split(":")[1].split(",")[0])
    new_deadline = callback_query.data.split(",")[1]
    print(new_deadline)
    task = db.get_task_by_id(task_id)
    creator = db.get_user_by_id(task['created_by'])['username'] if db.get_user_by_id(task['created_by']) else "Admin"
    try:
        if task and new_deadline:
            datetime_object = datetime.strptime(new_deadline, "%d-%m-%Y %H:%M")
            new_deadline2 = int(time.mktime(datetime_object.timetuple()))
            print(new_deadline2)
            db.update_task_deadline(task_id, new_deadline2)
            
            # Отправка уведомления в общий канал
            task_text = (
                f"⏰ <b>Дедлайн задачи изменен:</b>\n"
                f"🔖 <b>Название:</b> {task['title']}\n"
                f"👤 <b>Администратор:</b> {db.get_user_by_id(callback_query.from_user.id)['username']}\n"
                f"👤 <b>Создатель задачи:</b> {creator}\n"
                f"📅 <b>Новый дедлайн:</b> {new_deadline}\n"
            )
            
            
            await send_channel_message(bot, CHANNEL_ID, task_text)

                    # Запись в историю
        db.add_task_history_entry(
            task_id=task_id,
            user_id=callback_query.from_user.id,
            action="Запрос на перенос дедлайна подтвержден",
            details=f"Новый дедлайн: {new_deadline}"
        )

            # Отправка уведомления исполнителю
        if task['assigned_to']:
            for user_id in task['assigned_to'].split(','):
                user_id = int(user_id)
                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text=(
                            f"✅ <b>Ваш запрос на перенос дедлайна подтвержден:</b>\n"
                            f"🔖 <b>Название задачи:</b> {task['title']}\n"
                            f"📅 <b>Новый дедлайн:</b> {new_deadline}\n"
                        ),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print(f"Не удалось отправить уведомление пользователю {user_id}: {e}")

        await callback_query.message.answer("Дедлайн задачи успешно изменен!")
    except Exception as e:
        await callback_query.message.answer("Произошла ошибка при изменении дедлайна.")
        print(e.with_traceback())
    await state.clear()

@router.callback_query(F.data.startswith("reject_redeadline:"))
async def reject_redeadline_handler(callback_query: CallbackQuery, state: FSMContext, db: Database, bot: Bot):
    """Обработчик для отказа в переносе дедлайна."""
    task_id = int(callback_query.data.split(":")[1])
    data = await state.get_data()
    task = db.get_task_by_id(task_id)
    if task and task['assigned_to']:
        for user_id in task['assigned_to'].split(','):
            user_id = int(user_id)
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"❌ <b>В переносе дедлайна отказано:</b>\n"
                        f"🔖 <b>Название задачи:</b> {task['title']}\n"
                        f"👤 <b>Администратор:</b> {db.get_user_by_id(callback_query.from_user.id)['username']}\n"
                    ),
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
        await callback_query.message.answer("Вы отказали в переносе дедлайна.")
    else:
        await callback_query.message.answer("Произошла ошибка при отказе в переносе дедлайна.")
    await state.clear()

@router.callback_query(F.data.startswith("redeadline:"))
async def redeadline_handler(callback_query: CallbackQuery, state: FSMContext):
    task_id = int(callback_query.data.split(":")[1])
    await state.update_data(task_id=task_id)
    await callback_query.message.answer(
        "Введите новую дату и время дедлайна (в формате ДД-ММ-ГГГГ ЧЧ:ММ):",
    )
    await state.set_state(ChangeDeadlineFSM.waiting_for_new_deadline)

@router.message(F.text, StateFilter(ChangeDeadlineFSM.waiting_for_new_deadline))
async def handle_new_deadline_admin(message: Message, state: FSMContext):
    new_deadline = message.text
    try:
        datetime.strptime(new_deadline, "%d-%m-%Y %H:%M")
        await state.update_data(new_deadline=new_deadline)
    except ValueError:
        await message.answer("Неверный формат даты. Пожалуйста, введите дату в формате ДД-ММ-ГГГГ ЧЧ:ММ")


async def format_task_text(task: dict, db: Database) -> str:
    """Форматирует текст задачи, включая комментарии и исполнителей."""
    if task['assigned_to']:
        assigned_user_ids = [int(user_id) for user_id in task['assigned_to'].split(",")]
        assigned_users = [db.get_user_by_id(user_id)['username'] for user_id in assigned_user_ids if db.get_user_by_id(user_id)]
        assigned_users_str = ", ".join(assigned_users)
    else:
        assigned_users_str = "Не назначено"

    creator = db.get_user_by_id(task['created_by'])['username'] if db.get_user_by_id(task['created_by']) else "Неизвестно"
    deadline = datetime.fromtimestamp(task['deadline']).strftime("%d-%m-%Y %H:%M")

    task_text = (
        f"<b>Детали задачи:</b>\n\n"
        f"<b>📍 Локация:</b> {task['location']}\n"
        f"<b>🏷️ Название:</b> {task['title']}\n"
        f"<b>💰 Стоимость задачи:</b> {task['description']}\n"
        f"<b>⏰ Дедлайн:</b> {deadline}\n"
        f"👤 <b>Создатель задачи:</b> {creator}\n"
        f"<b>📌 Исполнители:</b> {assigned_users_str}\n"
        f"<b>📊 Статус:</b> {task['status']}\n\n"
    )

    if task['comments'] and task['comments'] != '_':
        formatted_comments = ""
        for comment in task['comments'].strip().split('\n'):
            formatted_comments += f"<blockquote>{comment}</blockquote>\n"
        task_text += f"<b>Комментарии:</b>\n{formatted_comments}"

    return task_text

@router.callback_query(F.data.startswith("take_task:"))
async def take_task_handler(callback_query: CallbackQuery, db: Database, bot: Bot):
    user_id = callback_query.from_user.id
    task_id = callback_query.data.split(":")[1]

    tasks = db.get_tasks_by_user(user_id)
    is_working = any(task["status"] == "is_on_work" for task in tasks)

    if is_working:
        await callback_query.answer("Вы уже работаете над задачей, завершите её, чтобы перейти к следующей!", show_alert=True)
    else:
        db.update_task_status(task_id, "is_on_work")
        task = db.get_task_by_id(task_id)
        task_status = task["status"]
        await callback_query.message.edit_reply_markup(reply_markup=task_admin_keyboard(task_id, task_status))

        # Отправка уведомления в общий канал
        task_text = (
            f"🛠️ <b>Задача взята в работу:</b>\n"
            f"🔖 <b>Название:</b> {task['title']}\n"
            f"👤 <b>Исполнитель:</b> {db.get_user_by_id(user_id)['username']}\n"
        )
        await send_channel_message(bot, CHANNEL_ID, task_text)
        # Запись в историю
        db.add_task_history_entry(
            task_id=task_id,
            user_id=callback_query.from_user.id,
            action="Задача взята в работу",
            details=f"Исполнитель: {db.get_user_by_id(user_id)['username']}"
        )

# В admin.py и executor.py (обработчик нажатия на кнопку "Добавить комментарий")
@router.callback_query(F.data.startswith("add_comment:"))
async def add_comment_handler(callback_query: CallbackQuery, state: FSMContext):
    task_id = int(callback_query.data.split(":")[1])
    await state.update_data(task_id=task_id) # сохраняем task_id в FSMContext
    await callback_query.message.answer("Введите текст комментария:")
    await state.set_state(AddCommentFSM.waiting_for_comment)

# Обработчик получения текста комментария (в admin.py и executor.py):
@router.message(F.text, StateFilter(AddCommentFSM.waiting_for_comment))
async def process_comment(message: Message, state: FSMContext, db: Database):
    comment_text = message.text
    data = await state.get_data()
    task_id = data.get("task_id")

    if task_id:
        db.update_task_comments(task_id, comment_text)
        await message.answer("Комментарий добавлен.")
        await state.clear() # очищаем FSM
        # Обновляем сообщение с задачей, чтобы отобразить новый комментарий (нужно получить task и сформировать текст)
        task = db.get_task_by_id(task_id)
    else:
        await message.answer("Произошла ошибка при добавлении комментария.")
        await state.clear()

    if task:
        task_text = await format_task_text(task, db) # Используем функцию форматирования

        if message.photo:
            await message.answer_photo(photo=task['ref_photo'], caption=task_text, reply_markup=task_admin_keyboard(task_id, task['status']), parse_mode="HTML")
        else:
            await message.answer(task_text, reply_markup=task_admin_keyboard(task_id, task['status']), parse_mode="HTML")



async def notify_executors(bot: Bot, executors: list[int], task_title: str, task_deadline: str):
    for executor_id in executors:
        try:
            # Отправляем уведомление
            await bot.send_message(
                chat_id=executor_id,
                text=(
                    f"📌 <b>Вам назначена новая задача:</b>\n"
                    f"🔖 <b>Название:</b> {task_title}\n"
                    f"⏰ <b>Дедлайн:</b> {task_deadline}\n"
                    # f"🆔 <b>ID:</b> {task_id}\n\n"
                    "Пожалуйста, выполните её вовремя. Она уже в списке доступных вам задач."
                ),
                parse_mode="HTML",
                # reply_markup=keyboard
            )
        except Exception as e:
            # Обработка ошибок отправки (например, если пользователь заблокировал бота)
            print(f"Не удалось отправить уведомление пользователю {executor_id}: {e}")
    


# Начало создания задачи
@router.message(F.text == "Создать задачу")
async def start_create_task(message: Message, state: FSMContext):
    # await message.delete()  # Удаляем сообщение с выбором
    await show_location_selection(message, state) # Сначала показываем выбор локации


# Ввод названия задачи
@router.message(F.text, StateFilter(CreateTaskFSM.title))
async def handle_task_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Введите стоимость задачи:")
    # await message.delete()  # Удаляем сообщение с выбором
    await state.set_state(CreateTaskFSM.description)


# Ввод описания задачи
@router.message(F.text, StateFilter(CreateTaskFSM.description))
async def handle_task_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите дедлайн задачи (ДД-ММ-ГГГГ ЧЧ:ММ):")
    # await message.delete()  # Удаляем сообщение с выбором
    await state.set_state(CreateTaskFSM.deadline)
    
# Ввод дедлайна задачи
@router.message(F.text, StateFilter(CreateTaskFSM.deadline))
async def handle_task_deadline(message: Message, state: FSMContext):
    deadline_str = message.text
    try:
        datetime.strptime(deadline_str, "%d-%m-%Y %H:%M")
        await state.update_data(deadline=deadline_str)
        await message.answer("Загрузите фото-референс задачи:", reply_markup=skip_photo)
        # await message.delete()  # Удаляем сообщение с выбором
        await state.set_state(CreateTaskFSM.photo)
    except ValueError:
        await message.answer("Неверный формат даты. Пожалуйста, введите дату в формате ДД-ММ-ГГГГ ЧЧ:ММ")


# Загрузка фото-референса (изменено)
@router.message(F.photo, StateFilter(CreateTaskFSM.photo))
async def handle_task_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo=photo_id)
    db = Database()
    executors = db.get_all_users()
    if not executors:
        await message.answer("Нет доступных исполнителей.")
        await state.clear()
        return

    await message.answer("Выберите исполнителей для задачи (нажимайте на имена). Когда закончите, нажмите 'Завершить выбор'.",
        reply_markup=assign_executor_keyboard(executors, multiple=True)
    )
    await state.set_state(CreateTaskFSM.selected_executors)

# Обновление обработчика пропуска фото (изменено)
@router.message(F.text == "Пропустить", StateFilter(CreateTaskFSM.photo))
async def skip_task_photo(message: Message, state: FSMContext):
    await state.update_data(photo=None)
    db = Database()
    executors = db.get_all_users()
    if not executors:
        await message.answer("Нет доступных исполнителей.")
        await state.clear()
        return

    await message.answer("Выберите исполнителей для задачи (нажимайте на имена). Когда закончите, нажмите 'Завершить выбор'.",
        reply_markup=assign_executor_keyboard(executors, multiple=True)
    )
    await state.set_state(CreateTaskFSM.selected_executors)


# Функция для отображения выбора локации (ОСТАЕТСЯ БЕЗ ИЗМЕНЕНИЙ)
async def show_location_selection(message: Message, state: FSMContext):
    locations = ["кухня", "бар", "зал", "маркетинг", "музыка", "прочее (укажите вручную)"]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
        [
            InlineKeyboardButton(text=locations[i], callback_data=f"location:{locations[i]}"),
            InlineKeyboardButton(text=locations[i+1], callback_data=f"location:{locations[i+1]}") if i + 1 < len(locations) else None
        ]for i in range(0, len(locations), 2)])
    await message.answer("Выберите местоположение задачи:", reply_markup=keyboard)
    await state.set_state(CreateTaskFSM.location)

# Обработка выбора локации (ИЗМЕНЕНО)
@router.callback_query(F.data.startswith("location:"), StateFilter(CreateTaskFSM.location))
async def handle_task_location(callback_query: CallbackQuery, state: FSMContext):
    selected_location = callback_query.data.split(":")[1]
    await state.update_data(location=selected_location)
    # await callback_query.message.delete()

    if selected_location == "прочее (укажите вручную)":
        await callback_query.message.answer("Введите ваше местоположение:")
        await state.set_state(CreateTaskFSM.other_location) # Переходим в новое состояние
    else:
        await state.update_data(location=selected_location)
        await callback_query.message.answer("Введите название задачи:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(CreateTaskFSM.title)

@router.message(F.text, StateFilter(CreateTaskFSM.other_location))
async def handle_other_location(message: Message, state: FSMContext):
    other_location = message.text
    await state.update_data(location=other_location)
    # await message.delete()
    await message.answer("Введите название задачи:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(CreateTaskFSM.title)


# Назначение исполнителя
@router.callback_query(F.data.startswith("assign_"), StateFilter(CreateTaskFSM.selected_executors))
async def select_executor(callback_query: CallbackQuery, state: FSMContext):
    executor_id = int(callback_query.data.split("_")[1])
    data = await state.get_data()
    selected_executors = data.get("selected_executors", [])
    
    if executor_id not in selected_executors:
        selected_executors.append(executor_id)  # Добавляем исполнителя
        await callback_query.answer("Исполнитель добавлен!")
    else:
        selected_executors.remove(executor_id)  # Убираем исполнителя
        await callback_query.answer("Исполнитель удален!")
    
    await state.update_data(selected_executors=selected_executors)




@router.callback_query(F.data == "finish_selection", StateFilter(CreateTaskFSM.selected_executors))
async def finish_executor_selection(callback_query: CallbackQuery, state: FSMContext, db: Database, bot: Bot):
    data = await state.get_data()
    executors = data.get("selected_executors", [])
    if not executors:
        await callback_query.message.answer("Вы не выбрали ни одного исполнителя.")
        return

    # Сохраняем задачу в базу данных
    db.create_task(
        title=data["title"],
        description=data["description"],
        deadline=data["deadline"],
        deadline_formatted=data["deadline"],
        ref_photo=data["photo"] or None,
        assigned_to=",".join(map(str, executors)),  # Храним как строку с ID через запятую
        report_text="#",
        report_photo="#",
        location=data.get("location"), # Добавляем location
        created_by=callback_query.from_user.id # Сохраняем ID создателя
    )

    await notify_executors(bot, executors, data["title"], data['deadline'])

    execs = ",".join(db.get_user_by_id(executor_id)['username'] for executor_id in executors)
    creator = db.get_user_by_id(callback_query.from_user.id)['username'] if db.get_user_by_id(callback_query.from_user.id) else "Неизвестно"

    # Отправка уведомления в общий канал
    task_text = (
        f"📌 <b>Новая задача создана:</b>\n"
        f"🔖 <b>Название:</b> {data['title']}\n"
        f"📍 <b>Локация:</b> {data.get('location')}\n"  # Добавляем локацию в уведомление
        f"⏰ <b>Дедлайн:</b> {data['deadline']}\n"
        f"👤 <b>Создатель:</b> {creator}\n"
        f"👤 <b>Исполнители:</b> {execs}\n"
    )
    await send_channel_message(bot, CHANNEL_ID, task_text)

        # Запись в историю


    await callback_query.message.answer("Задача успешно создана!", reply_markup=admin_menu_keyboard)
    # await callback_query.message.delete()  # Удаляем сообщение с выбором
    await state.clear()

        # Получаем task_id созданной задачи
    task = db.get_task_by_title(data["title"])
    if task:
        task_id = task['id']
    else:
        await callback_query.message.answer("Произошла ошибка при получении ID задачи.")
        await state.clear()
        return

    db.add_task_history_entry(
        task_id=task_id or 0,
        user_id=callback_query.from_user.id,
        action="Задача создана",
        details=f"Cоздатель: {creator}, \nИсполнители: {execs}"
    )



@router.message(F.text == "Просмотр задач")
async def view_tasks(message: Message, db: Database):
    """
    Отображение задач с возможностью фильтрации через инлайн-кнопки.
    """
    tasks = db.get_all_tasks()

    if not tasks:
        await message.answer("Нет задач.")
        return
    
    keyboard = create_task_list_keyboard(tasks)
    # Отправляем сообщение с задачами
    await message.answer("📋 Все задачи:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("view_task:"))
async def view_task(callback_query: CallbackQuery, db: Database):
    task_id = int(callback_query.data.split(":")[1])
    task = db.get_task_by_id(task_id)

    if not task:
        await callback_query.message.edit_text("Задача не найдена.")
        return

    task_text = await format_task_text(task, db) # Используем функцию форматирования

    if task["ref_photo"]:
        await callback_query.message.answer_photo(photo=task["ref_photo"], caption=task_text, reply_markup=task_admin_keyboard(task_id, task['status']), parse_mode="HTML")
    else:
        await callback_query.message.answer(task_text, reply_markup=task_admin_keyboard(task_id, task['status']), parse_mode="HTML")
    # await callback_query.message.delete()
    task_id = int(callback_query.data.split(":")[1])
    task = db.get_task_by_id(task_id)

    if not task:
        await callback_query.message.edit_text("Задача не найдена.")
        return

    

def create_task_list_keyboard(tasks):    
    # Создаем инлайн-клавиатуру с задачами
    task_buttons = [
        InlineKeyboardButton(
            text=f"{task['title'][:25]}...",  # Укороченное название задачи
            callback_data=f"view_task:{task['id']}"
        )
        for task in tasks if not task['status'] == 'completed' and not task['status'] == 'done'
    ]

    # Добавляем кнопки фильтрации
    filter_buttons = [
        InlineKeyboardButton(text="✅ Выполненные задачи", callback_data="filter:done"),
        InlineKeyboardButton(text="🛑 Завершенные задачи", callback_data="filter:completed")
    ]

    # Генерируем клавиатуру
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [button] for button in task_buttons  # Каждая задача на отдельной строке
        ] + [filter_buttons]  # Кнопки фильтра добавляем отдельной строкой
    )

    return keyboard



@router.callback_query(F.data == "back_to_task_list")
async def back_to_task_list(callback_query: CallbackQuery, db: Database):
    tasks = db.get_all_tasks()
    if not tasks:
        await callback_query.message.edit_text("Нет задач.")
        return
    keyboard = create_task_list_keyboard(tasks)
    # await callback_query.message.delete()
    await callback_query.message.answer(" Все задачи:", reply_markup=keyboard)



@router.callback_query(F.data.startswith("back_to_filter_list:"))
async def back_to_filter_list(callback_query: CallbackQuery, db: Database):
    status = callback_query.data.split(":")[1]
    tasks = db.get_all_tasks()
    filtered_tasks = [task for task in tasks if task['status'] == status]
    if not filtered_tasks:
        await callback_query.message.edit_text("Нет задач с выбранным статусом.")
        return
    keyboard = create_task_list_keyboard(filtered_tasks)
    await callback_query.message.edit_text(f" Задачи со статусом '{status}':", reply_markup=keyboard)

@router.callback_query(F.data.startswith("filter:"))
async def filter_tasks(callback_query: CallbackQuery, db: Database):
    status = callback_query.data.split(":")[1]
    tasks = db.get_all_tasks()
    filtered_tasks = [task for task in tasks if task['status'] == status]
    if not filtered_tasks:
        await callback_query.message.edit_text("Нет задач с выбранным статусом.")
        return
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{task['title'][:25]}...",  # Укороченное название задачи
            callback_data=f"view_task:{task['id']}"
        )]for task in tasks if not task['status'] == 'pending' and not task['status'] == 'is_on_work'
    ] )
    back_button = [InlineKeyboardButton(text="Назад к списку", callback_data="back_to_task_list")]
    keyboard.inline_keyboard.append(back_button)
    await callback_query.message.edit_text(f" Задачи со статусом '{status}':", reply_markup=keyboard)
        

@router.callback_query(F.data.startswith("reassign_task:"))
async def reassign_task_handler(callback_query: CallbackQuery, state: FSMContext, db: Database):
    """
    Обработчик переназначения исполнителей для задачи.
    """
    task_id = int(callback_query.data.split(":")[1])  # Получаем ID задачи
    executors = db.get_all_users()  # Получаем список всех исполнителей

    if not executors:
        await callback_query.message.answer("Нет доступных исполнителей.")
        return

    # Сохраняем ID задачи и инициализируем пустой список выбранных исполнителей
    await state.update_data(task_id=task_id, selected_executors=[])

    # Отправляем сообщение с инлайн-кнопками исполнителей
    if callback_query.message.text:
        await callback_query.message.edit_text(
            "Выберите исполнителей для задачи (нажимайте на имена). Когда закончите, нажмите 'Завершить выбор'.",
            reply_markup=reassign_executor_keyboard(executors, task_id, allow_finish=True)
        )
    elif callback_query.message.caption:  # Если сообщение — фото
        await callback_query.message.edit_caption(
            "Выберите исполнителей для задачи (нажимайте на имена). Когда закончите, нажмите 'Завершить выбор'.",
            reply_markup=reassign_executor_keyboard(executors, task_id, allow_finish=True)
        )
    else:
        # Если сообщение не поддерживает редактирование, отправляем новое
        await callback_query.message.answer(
            "Выберите исполнителей для задачи (нажимайте на имена). Когда закончите, нажмите 'Завершить выбор'.",
            reply_markup=reassign_executor_keyboard(executors, task_id, allow_finish=True)
        )


@router.callback_query(F.data.startswith("toggle_executor:"))
async def toggle_executor(callback_query: CallbackQuery, state: FSMContext):
    """
    Добавление или удаление исполнителя из списка.
    """
    executor_id = int(callback_query.data.split(":")[1])  # ID исполнителя
    data = await state.get_data()
    selected_executors = data.get("selected_executors", [])

    # Добавляем или удаляем исполнителя из списка
    if executor_id in selected_executors:
        selected_executors.remove(executor_id)
        await callback_query.answer("Исполнитель удален из списка.")
    else:
        selected_executors.append(executor_id)
        await callback_query.answer("Исполнитель добавлен в список.")

    # Сохраняем обновленный список
    await state.update_data(selected_executors=selected_executors)


@router.callback_query(F.data == "finish_selectionw")
async def finish_executor_selection(callback_query: CallbackQuery, state: FSMContext, db: Database, bot: Bot):
    """
    Завершение выбора исполнителей.
    """
    data = await state.get_data()
    task_id = data.get("task_id")
    task = db.get_task_by_id(task_id)
    selected_executors = data.get("selected_executors", [])

    if not selected_executors:
        await callback_query.answer("Вы не выбрали ни одного исполнителя.", show_alert=True)
        return

    # Обновляем задачу в базе данных (сохраняем ID исполнителей через запятую)
    db.update_task_assigned_to(",".join(map(str, selected_executors)), task_id)

    await notify_executors(bot, selected_executors, task['title'], task['deadline'])

    execs = ",".join(db.get_user_by_id(executor_id)['username'] for executor_id in selected_executors)

    # Отправка уведомления в общий канал
    task_text = (
        f"🔄 <b>Исполнители задачи переназначены:</b>\n"
        f"🔖 <b>Название:</b> {task['title']}\n"
        f"👤 <b>Новые исполнители:</b> {execs}\n"
    )
    await send_channel_message(bot, CHANNEL_ID, task_text)

        # Запись в историю
    db.add_task_history_entry(
        task_id=task_id,
        user_id=callback_query.from_user.id,
        action="Исполнители задачи переназначены",
        details=f"Новые исполнители: {execs}"
    )

    await callback_query.message.answer("Исполнители успешно назначены!")
    # await callback_query.message.delete()  # Удаляем сообщение с выбором
    await state.clear()


@router.callback_query(F.data.startswith("checktask:"))
async def checktask_executor(callback_query, state: FSMContext, db: Database):
    task_id = callback_query.data.split(":")[1]
    task = db.get_task_by_id(task_id)
    if task['report_photo']:
        await callback_query.message.answer_photo(
            photo=task['report_photo'],
            caption=(task['report_text']),
            reply_markup=task_admin_keyboardb(task_id)
        )
    else:
        await callback_query.message.answer(
            task['report_text'],
            reply_markup=task_admin_keyboardb(task_id)
        )
    await state.clear()
    # await callback_query.message.delete()  # Удаляем сообщение с выбором

@router.callback_query(F.data.startswith("approved:"))
async def complete_task_executor(callback_query: CallbackQuery, db: Database, bot: Bot):
    task_id = callback_query.data.split(":")[1]
    db.update_task_status(task_id, 'completed')
    task = db.get_task_by_id(task_id)
    # Отправка уведомления в общий канал
    task_text = (
        f"🎉 <b>Задача подтверждена админом и завершена:</b>\n"
        f"🔖 <b>Название:</b> {task['title']}\n"
        f"👤 <b>Исполнитель:</b> {db.get_user_by_id(int(task['assigned_to']))['username']}\n"
    )
    await send_channel_message(bot, CHANNEL_ID, task_text)

    # Запись в историю
    db.add_task_history_entry(
        task_id=task_id,
        user_id=callback_query.from_user.id,
        action="Задача завершена",
        details=f"Задача подтверждена админом и завершена"
    )

   # Логика начисления/снятия баллов
    current_time = int(time.time())
    time_diff = task['deadline'] - current_time
    if task['assigned_to']:
        tariffs = db.get_all_tariffs()
        for user_id in task['assigned_to'].split(','):
            user_id = int(user_id)
            if time_diff > 0:  # Задача выполнена раньше срока
                for tariff in tariffs:
                    if tariff['tariff_name'].endswith("_early") and time_diff >= tariff['time_threshold']:
                        score = tariff['score']
                        db.add_user_score(user_id, score)
                        try:
                            await bot.send_message(
                                chat_id=user_id,
                                text=(
                                    f"✅ <b>Задача выполнена раньше срока. Начислено {score} баллов.</b>\n"
                                    f"🔖 <b>Название задачи:</b> {task['title']}\n"
                                ),
                                parse_mode="HTML"
                            )
                        except Exception as e:
                            print(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
                        break
            elif time_diff < 0:  # Задача просрочена
                time_diff = abs(time_diff)
                for tariff in tariffs:
                    if tariff['tariff_name'].endswith("_late") and time_diff <= tariff['time_threshold']:
                        score = tariff['score']
                        db.remove_user_score(user_id, score)
                        try:
                            await bot.send_message(
                                chat_id=user_id,
                                text=(
                                    f"❌ <b>Задача просрочена. Списано {abs(score)} баллов.</b>\n"
                                    f"🔖 <b>Название задачи:</b> {task['title']}\n"
                                ),
                                parse_mode="HTML"
                            )
                        except Exception as e:
                            print(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
    await callback_query.message.answer("Задача подтверждена")

@router.callback_query(F.data.startswith("rejected:"))
async def rejected_task_executor(callback_query: CallbackQuery, db: Database, bot: Bot):
    task_id = callback_query.data.split(":")[1]
    task = db.get_task_by_id(task_id)
    if task and task['assigned_to']:
        for user_id in task['assigned_to'].split(','):
            user_id = int(user_id)
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"❌ <b>Задача отправлена на доработку:</b>\n"
                        f"🔖 <b>Название:</b> {task['title']}\n"
                        # f"👤 <b>Администратор:</b> {db.get_user_by_id(callback_query.from_user.id)['username'] or "Admin"}\n"
                        f"👤 <b>Администратор:</b> {task['created_by']}\n"
                    ),
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
        db.update_task_status(task_id, 'pending')
        await callback_query.message.answer("Задача отправлена на доработку.")
    else:
        await callback_query.message.answer("Произошла ошибка при отправке задачи на доработку.")
    

@router.callback_query(F.data.startswith("add_comment:"))
async def add_comment_handler(callback_query: CallbackQuery):
    db = Database()
    task_id = callback_query.data.split(":")[1]
    oldDesc = db.get_task_by_id(task_id)['description']
    await callback_query.message.answer("В разработке.")


@router.callback_query(F.data.startswith("delete_task:"))
async def delete_task_handler(callback_query: CallbackQuery, db: Database):
    task_id = int(callback_query.data.split(":")[1])
    try:
        db.delete_task(task_id=task_id)
        await callback_query.message.answer("Задача удалена!", show_alert=True)

        # Запись в историю
        db.add_task_history_entry(
            task_id=task_id,
            user_id=callback_query.from_user.id,
            action="Задача удалена",
            details=f"ID задачи: {task_id}"
        )
    except Exception as e:
        await callback_query.message.answer(f"Ошибка при удалении: {e}", show_alert=True)
    # await callback_query.message.delete()


@router.message(F.text == "Пользователи")
async def view_users_handler(message: Message, db: Database):
    users = db.get_all_users()
    if users:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{user['username']} : {user['role']}", callback_data=f"user_info:{user['user_id']}")] for user in users
        ])
        await message.answer("<b>Список пользователей</b>", parse_mode="HTML" , reply_markup=keyboard)
    else:
        await message.answer("Пользователи не найдены.", parse_mode="HTML")

# @router.callback_query(F.data.startswith("user_info:"))
# async def user_info_handler(callback_query: CallbackQuery, db: Database):
#     user_id = int(callback_query.data.split(":")[1])
#     user = db.get_user_by_id(user_id)
#     if user:
#         await callback_query.message.edit_text(f"Информация о пользователе:\nUsername: {user['username']}\nRole: {user['role']}", reply_markup=role_selection_keyboard(user_id))
#     else:
#         await callback_query.message.edit_text("Пользователь не найден.")


@router.callback_query(F.data.startswith("set_role:"))
async def set_user_role_handler(callback_query: CallbackQuery, db: Database):
    """Обработчик для установки роли пользователя."""
    _, new_role, user_id = callback_query.data.split(":")
    user_id = int(user_id)
    db.update_user_role(user_id, new_role)

    # Получаем информацию о пользователе, которому изменили роль
    user = db.get_user_by_id(user_id)

    if user:
        try:
            # Отправляем сообщение непосредственно пользователю с новой клавиатурой
            await bot.send_message(user_id, f"Ваша роль изменена на {new_role}.", reply_markup=admin_menu_keyboard if new_role == 'Админ' else executor_menu_keyboard)
            await send_menu(types.Message(message_id=callback_query.message.message_id, from_user=types.User(id=user_id), chat=types.Chat(id=user_id)), db)
        except Exception as e:
            await callback_query.message.edit_text(f"Произошла ошибка: {e}")

        await callback_query.message.edit_text(f"Роль пользователя с ID {user_id} успешно изменена на {new_role}.")
    else:
        await callback_query.message.edit_text("Пользователь не найден.")

@router.callback_query(F.data == "back_to_users")
async def back_to_users_handler(callback_query: CallbackQuery, db: Database):
    """Обработчик для возврата к списку пользователей."""
    users = db.get_all_users()
    if users:
        await callback_query.message.edit_text("Список пользователей:", reply_markup=user_list_keyboard(users))
    else:
        await callback_query.message.edit_text("Пользователи не найдены.")

@router.callback_query(F.data.startswith("delete_user:"))
async def delete_user_handler(callback_query: CallbackQuery, db: Database):
    """Обработчик для удаления пользователя."""
    user_id = int(callback_query.data.split(":")[1])

    # Проверяем, не пытается ли админ удалить самого себя
    if user_id == callback_query.from_user.id:
        await callback_query.answer("Вы не можете удалить самого себя.", show_alert=True)
        return

    user = db.get_user_by_id(user_id) #получаем пользователя перед удалением для вывода сообщения
    if user:
        db.delete_user(user_id)
        await callback_query.message.edit_text(f"Пользователь {user['username']} (ID: {user_id}) успешно удален.")
    else:
        await callback_query.message.edit_text("Пользователь не найден.")


@router.message(F.text == "Статистика")
async def admin_statistics(message: types.Message, db: Database):
    """Отображение статистики (общей и по пользователям)."""
    total_tasks = db.get_total_tasks_count()
    pending_tasks = db.get_tasks_count_by_status("pending")
    is_on_work_tasks = db.get_tasks_count_by_status("is_on_work")
    done_tasks = db.get_tasks_count_by_status("done")
    completed_tasks = db.get_tasks_count_by_status("completed")
    total_users = db.get_all_users_count()
    admin_users = db.get_users_count_by_role("Админ")
    executor_users = db.get_users_count_by_role("Исполнитель")

    response = (
        " <b>Общая статистика:</b>\n\n"
        f"<b>Задачи:</b>\n"
        f"📊 Всего: {total_tasks}\n"
        f"⏳ Ожидают выполнения: {pending_tasks}\n"
        f"🛠️ В работе: {is_on_work_tasks}\n"
        f"✅ Выполнены: {done_tasks}\n"
        f"🎉 Завершены: {completed_tasks}\n\n"
        f"<b>Пользователи:</b>\n"
        f"👥 Всего: {total_users}\n"
        f"👑 Администраторы: {admin_users}\n"
        f"👨‍🔧 Исполнители: {executor_users}\n\n"
        f"Статистика по пользователям доступна в разделе:\n<b>Пользователи</b>" # Заголовок для выбора пользователя
    )
    users = db.get_all_users()
    if users:
        await message.answer(response, parse_mode="HTML")
    else:
        await message.answer(response + "\nПользователи не найдены.", parse_mode="HTML")

#Добавим кнопку для просмотра статистики пользователя в user_info_handler
@router.callback_query(F.data.startswith("user_info:")) # Обработчик для информации о пользователе
async def user_info_handler(callback_query: CallbackQuery, db: Database):
    user_id = callback_query.data.split(":")[1]
    user = db.get_user_by_id(user_id)

    total_user_tasks = db.get_user_tasks_count(user_id)
    pending_user_tasks = db.get_user_tasks_count_by_status(user_id, "pending")
    is_on_work_user_tasks = db.get_user_tasks_count_by_status(user_id, "is_on_work")
    done_user_tasks = db.get_user_tasks_count_by_status(user_id, "done")
    completed_user_tasks = db.get_user_tasks_count_by_status(user_id, "completed")
    user_score = db.get_user_score(user_id)

    response = (
        f" <b>Информация о пользователе:\n{user['username']} : {user['role']} ({db.get_user_score(user['user_id'])} Б):</b>\n\n"
        f"<b>Задачи:</b>\n"
        f"📊 Всего: {total_user_tasks}\n"
        f"⏳ Ожидают выполнения: {pending_user_tasks}\n"
        f"🛠️ В работе: {is_on_work_user_tasks}\n"
        f"✅ Выполнены: {done_user_tasks}\n"
        f"🎉 Завершены: {completed_user_tasks}\n"
        f"<b>Баллы:</b> {user_score}\n"

    )

    if user:
        keyboard = role_selection_keyboard(user_id)
        # keyboard.inline_keyboard.append([InlineKeyboardButton(text="Статистика пользователя", callback_data=f"user_stats:{user_id}")])
        await callback_query.message.edit_text(response, parse_mode="HTML", reply_markup=keyboard)
    else:
        await callback_query.message.edit_text("Пользователь не найден.")

@router.callback_query(F.data.startswith("view_task_history:"))
async def view_task_history(callback_query: CallbackQuery, db: Database):
    """Отображает историю изменений задачи."""
    task_id = int(callback_query.data.split(":")[1])
    history = db.get_task_history(task_id)

    if not history:
        await callback_query.message.answer("История изменений для данной задачи не найдена.")
        return

    history_text = f"<b>История изменений задачи (ID: {task_id}):</b>\n\n"
    for entry in history:
        timestamp = datetime.fromtimestamp(entry['timestamp']).strftime("%d-%m-%Y %H:%M")
        history_text += (
            f"""<b>{timestamp}</b>
<blockquote>
<b>Действие:</b> {entry['action']}
<b>Пользователь:</b> {db.get_user_by_id(entry['user_id'])['username'] if db.get_user_by_id(entry['user_id']) else 'Неизвестно'}
<b>Детали:</b> {entry['details']}
</blockquote>\n
"""
        )

    await callback_query.message.answer(history_text, parse_mode="HTML")

@router.message(F.text == "Тарифы")
async def manage_tariffs_handler(message: Message, state: FSMContext):
    """Обработчик для управления тарифами."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Просмотр тарифов", callback_data="view_tariffs")],
        [InlineKeyboardButton(text="➕ Создать тариф", callback_data="create_tariff")],
        [InlineKeyboardButton(text="✏️ Изменить тариф", callback_data="update_tariff")],
        [InlineKeyboardButton(text="🗑️ Удалить тариф", callback_data="delete_tariff")],
        # [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin_menu")]
    ])
    await message.answer("Выберите действие:", reply_markup=keyboard)
    await state.set_state(ManageTariffsFSM.menu)

@router.callback_query(F.data == "view_tariffs", StateFilter(ManageTariffsFSM.menu))
async def view_tariffs_handler(callback_query: CallbackQuery, db: Database, state: FSMContext):
    """Обработчик для просмотра тарифов."""
    tariffs = db.get_all_tariffs()
    if tariffs:
        tariff_text = "<b>Список тарифов:</b>\n\n"
        for tariff in tariffs:
            tariff_text += (
                f"<b>Название:</b> {tariff['tariff_name']}\n"
                f"<b>Порог времени:</b> {int(tariff['time_threshold']) / 60} минут\n"
                f"<b>Баллы:</b> {tariff['score'] if tariff['tariff_name'].endswith('early') else abs(tariff['score'])}\n\n"
            )
        await callback_query.message.edit_text(tariff_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_tariffs_menu")]]))
    else:
        await callback_query.message.answer("Тарифы не найдены.")
    await state.set_state(ManageTariffsFSM.menu)

@router.callback_query(F.data == "back_to_tariffs_menu", StateFilter(ManageTariffsFSM.menu))
async def back_to_tariffs_menu_handler(callback_query: CallbackQuery, state: FSMContext):
    """Обработчик для возврата к меню тарифов."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Просмотр тарифов", callback_data="view_tariffs")],
        [InlineKeyboardButton(text="➕ Создать тариф", callback_data="create_tariff")],
        [InlineKeyboardButton(text="✏️ Изменить тариф", callback_data="update_tariff")],
        [InlineKeyboardButton(text="🗑️ Удалить тариф", callback_data="delete_tariff")],
        # [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin_menu")]
    ])
    await callback_query.message.edit_text("Выберите действие:", reply_markup=keyboard)
    await state.set_state(ManageTariffsFSM.menu)

@router.callback_query(F.data == "create_tariff", StateFilter(ManageTariffsFSM.menu))
async def create_tariff_handler(callback_query: CallbackQuery, state: FSMContext):
    """Обработчик для создания тарифа."""
    await callback_query.message.answer("Введите название нового тарифа:")
    await state.set_state(ManageTariffsFSM.waiting_for_tariff_name)

@router.message(F.text, StateFilter(ManageTariffsFSM.waiting_for_tariff_name))
async def handle_tariff_name(message: Message, state: FSMContext):
    """Обработчик для получения названия тарифа."""
    await state.update_data(tariff_name=message.text)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ начисление", callback_data="tariff_type:early"),
         InlineKeyboardButton(text="➖ списание", callback_data="tariff_type:late")]
    ])
    await message.answer("Выберите тип тарифа:", reply_markup=keyboard)
    await state.set_state(ManageTariffsFSM.waiting_for_tariff_type)

@router.callback_query(F.data.startswith("tariff_type:"), StateFilter(ManageTariffsFSM.waiting_for_tariff_type))
async def handle_tariff_type_callback(callback_query: CallbackQuery, state: FSMContext):
    """Обработчик для получения типа тарифа."""
    tariff_type = callback_query.data.split(":")[1]
    await state.update_data(tariff_type=tariff_type)
    await callback_query.message.answer("Введите временной порог (в минутах):")
    await state.set_state(ManageTariffsFSM.waiting_for_time_threshold)

@router.message(F.text, StateFilter(ManageTariffsFSM.waiting_for_time_threshold))
async def handle_time_threshold(message: Message, state: FSMContext):
    """Обработчик для получения временного порога."""
    await state.update_data(time_threshold=message.text)
    await message.answer("Введите количество баллов:")
    await state.set_state(ManageTariffsFSM.waiting_for_score)

@router.message(F.text, StateFilter(ManageTariffsFSM.waiting_for_score))
async def handle_score(message: Message, state: FSMContext, db: Database):
    """Обработчик для получения количества баллов."""
    data = await state.get_data()
    tariff_name = data.get("tariff_name")
    time_threshold = data.get("time_threshold")
    score = message.text
    tariff_type = data.get("tariff_type")
    try:
        time_threshold = int(time_threshold) * 60
        score = int(score)
        db.create_tariff(f"{tariff_name}_{tariff_type}", time_threshold, score)
        await message.answer("Тариф успешно создан!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_tariffs_menu")]]))
    except ValueError:
        await message.answer("Неверный формат данных. Пожалуйста, введите целые числа для времени и баллов.")
    await state.set_state(ManageTariffsFSM.menu)

@router.callback_query(F.data == "update_tariff", StateFilter(ManageTariffsFSM.menu))
async def update_tariff_handler(callback_query: CallbackQuery, state: FSMContext, db: Database):
    """Обработчик для изменения тарифа."""
    tariffs = db.get_all_tariffs()
    if tariffs:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=tariff['tariff_name'], callback_data=f"select_tariff:{tariff['tariff_name']}")]
            for tariff in tariffs
        ])
        await callback_query.message.answer("Выберите тариф для изменения:", reply_markup=keyboard)
        await state.set_state(ManageTariffsFSM.waiting_for_tariff_to_update)
    else:
        await callback_query.message.answer("Тарифы не найдены.")
        await state.set_state(ManageTariffsFSM.menu)

@router.callback_query(F.data.startswith("select_tariff:"), StateFilter(ManageTariffsFSM.waiting_for_tariff_to_update))
async def handle_select_tariff(callback_query: CallbackQuery, state: FSMContext):
    """Обработчик для выбора тарифа."""
    tariff_name = callback_query.data.split(":")[1]
    await state.update_data(tariff_name=tariff_name)
    await callback_query.message.answer("Введите новый временной порог (в минутах):")
    await state.set_state(ManageTariffsFSM.waiting_for_new_time_threshold)

@router.message(F.text, StateFilter(ManageTariffsFSM.waiting_for_new_time_threshold))
async def handle_new_time_threshold(message: Message, state: FSMContext):
    """Обработчик для получения нового временного порога."""
    await state.update_data(new_time_threshold=message.text)
    await message.answer("Введите новое количество баллов:")
    await state.set_state(ManageTariffsFSM.waiting_for_new_score)

@router.message(F.text, StateFilter(ManageTariffsFSM.waiting_for_new_score))
async def handle_new_score(message: Message, state: FSMContext, db: Database):
    """Обработчик для получения нового количества баллов."""
    data = await state.get_data()
    tariff_name = data.get("tariff_name")
    new_time_threshold = data.get("new_time_threshold")
    new_score = message.text
    try:
        new_time_threshold = int(new_time_threshold) * 60
        new_score = int(new_score)
        db.update_tariff(tariff_name, new_time_threshold, new_score)
        await message.answer("Тариф успешно обновлен!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_tariffs_menu")]]))
    except ValueError:
        await message.answer("Неверный формат данных. Пожалуйста, введите целые числа для времени и баллов.")
    await state.set_state(ManageTariffsFSM.menu)

@router.callback_query(F.data == "delete_tariff", StateFilter(ManageTariffsFSM.menu))
async def delete_tariff_handler(callback_query: CallbackQuery, state: FSMContext, db: Database):
    """Обработчик для выбора тарифа для удаления."""
    tariffs = db.get_all_tariffs()
    if tariffs:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=tariff['tariff_name'], callback_data=f"select_tariff_to_delete:{tariff['tariff_name']}")]
            for tariff in tariffs
        ])
        await callback_query.message.answer("Выберите тариф для удаления:", reply_markup=keyboard)
        await state.set_state(ManageTariffsFSM.waiting_for_tariff_to_delete)
    else:
        await callback_query.message.answer("Тарифы не найдены.")
        await state.set_state(ManageTariffsFSM.menu)

@router.callback_query(F.data.startswith("select_tariff_to_delete:"), StateFilter(ManageTariffsFSM.waiting_for_tariff_to_delete))
async def handle_select_tariff_to_delete(callback_query: CallbackQuery, state: FSMContext, db: Database):
    """Обработчик для удаления тарифа."""
    tariff_name = callback_query.data.split(":")[1]
    try:
        db.delete_tariff(tariff_name)
        await callback_query.message.answer(f"Тариф '{tariff_name}' успешно удален.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_tariffs_menu")]]))
    except Exception as e:
        await callback_query.message.answer(f"Ошибка при удалении тарифа: {e}")
    await state.set_state(ManageTariffsFSM.menu)


