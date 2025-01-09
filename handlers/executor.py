# handlers/executor.py
import os
from aiogram import Bot, Router, F, types
from database import Database
from keyboards.inline import task_executor_keyboard, task_executor_keyboarda
from aiogram.types import CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from utils import send_channel_message
from dotenv import load_dotenv


router = Router()
load_dotenv()
CHANNEL_ID = os.getenv("CHANNEL_ID")

class ReportTaskFSM(StatesGroup):
    task_id = State()
    photo = State()
    report_text = State()

#Создаем FSM
class AddCommentEFSM(StatesGroup):
    waiting_for_comment = State()
    task_id = State()

# В admin.py и executor.py (обработчик нажатия на кнопку "Добавить комментарий")
@router.callback_query(F.data.startswith("add_comment_exec:"))
async def add_comment_handler(callback_query: CallbackQuery, state: FSMContext):
    task_id = int(callback_query.data.split(":")[1])
    await state.update_data(task_id=task_id) # сохраняем task_id в FSMContext
    await callback_query.message.answer("Введите текст комментария:")
    await state.set_state(AddCommentEFSM.waiting_for_comment)

# Обработчик получения текста комментария (в admin.py и executor.py):
@router.message(F.text, StateFilter(AddCommentEFSM.waiting_for_comment))
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
        if task:
            if task['assigned_to']: # Проверяем, есть ли вообще назначенные исполнители
                assigned_users_list = task['assigned_to'].split(",")
                valid_assigned_users = []
                for user_id_str in assigned_users_list:
                    try:
                        user_id = int(user_id_str)
                        user = db.get_user_by_id(user_id)
                        if user:  # Проверяем, существует ли пользователь в базе
                            valid_assigned_users.append(user['username'])
                    except ValueError:
                        pass

                assigned_users = ", ".join(valid_assigned_users)
            else:
                assigned_users = "Не назначено"
            task_text = (
                f" <b>Детали задачи:</b>\n\n"
                f"<b>Локация:</b> {task['location']}\n"
                f" <b>Название:</b> {task['title']}\n"
                f" <b>Стоимость задачи:</b> {task['description']}\n"
                f" <b>Дедлайн:</b> {task['deadline_formatted']}\n"
                f" <b>Исполнители:</b> {assigned_users}\n"
                f" <b>Статус:</b> {task['status']}\n\n"
                
            )
            if task['comments'] and task['comments'] != '_': # Проверяем, есть ли комментарии
                formatted_comments = ""
                for comment in task['comments'].strip().split('\n'):  # Разделяем комментарии по строкам
                    formatted_comments += f"<blockquote>{comment}</blockquote>\n" # Оборачиваем каждый комментарий в <blockquote>

                task_text += f"<b>Комментарии:</b>\n{formatted_comments}"
                
            if message.photo:
                await message.answer_photo(
                    photo=message.photo[-1].file_id,
                    caption=task_text,
                    reply_markup=task_executor_keyboarda(task_id) if task['status'] == 'done' else task_executor_keyboard(task_id),
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    task_text,
                    reply_markup=task_executor_keyboarda(task_id) if task['status'] == 'done' else task_executor_keyboard(task_id),
                    parse_mode="HTML"
                )
    else:
        await message.answer("Произошла ошибка при добавлении комментария.")
        await state.clear()

@router.message(F.text == "Мои задачи")
async def my_tasks_handler(message: Message, db: Database):
    """
    Отображение списка задач для исполнителя.
    """
    user_id = str(message.from_user.id).lower()
    # print(user_id)
    tasks = db.get_tasks_by_user(user_id)

    if not tasks:
        await message.answer("У вас пока нет задач.")
        return

    # Создаем кнопки для задач
    task_buttons = [
        InlineKeyboardButton(
            text=f"{task['title'][:25]}...",  # Укороченное название задачи
            callback_data=f"view_my_task:{task['id']}"
        )
        for task in tasks if not task['status'] == 'completed' and not task['status'] == 'done'
    ]

    # Формируем клавиатуру
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[button] for button in task_buttons]  # Кнопки задач
    )

    # Отправляем список задач
    await message.answer("📋 Ваши задачи:", reply_markup=keyboard)

async def show_task_details(callback_query: CallbackQuery, db: Database, task_id: int):
    """Общая функция для отображения деталей задачи."""
    task = db.get_task_by_id(task_id)

    if not task:
        await callback_query.message.edit_text("Задача не найдена.")
        return

    task_text = (
        f" <b>Детали задачи:</b>\n\n"
        f"<b>Локация:</b> {task['location']}\n"
        f" <b>Название:</b> {task['title']}\n"
        f" <b>Стоимость задачи:</b> {task['description']}\n"
        f" <b>Дедлайн:</b> {task['deadline_formatted']}\n"
        f" <b>Статус:</b> {task['status']}\n\n"
    )

    if task['comments'] and task['comments'] != '_':
        formatted_comments = ""
        for comment in task['comments'].strip().split('\n'):
            formatted_comments += f"<blockquote>{comment}</blockquote>\n"
        task_text += f"<b>Комментарии:</b>\n{formatted_comments}"

    await callback_query.message.delete()

    reply_markup = task_executor_keyboard(task_id) if task['status'] == 'pending' else task_executor_keyboarda(task_id)

    if task["ref_photo"]:
        await callback_query.message.answer_photo(
            photo=task["ref_photo"],
            caption=task_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        await callback_query.message.answer(
            task_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

@router.callback_query(F.data.startswith("view_my_task:"))
async def view_my_task(callback_query: CallbackQuery, db: Database):
    task_id = int(callback_query.data.split(":")[1])
    await show_task_details(callback_query, db, task_id)

@router.callback_query(F.data.startswith("view_my_done_task:"))
async def view_my_done_task(callback_query: CallbackQuery, db: Database):
    task_id = int(callback_query.data.split(":")[1])
    await show_task_details(callback_query, db, task_id)


@router.callback_query(F.data == "back_to_my_tasks")
async def back_to_my_tasks(callback_query: CallbackQuery, db: Database):
    """
    Возвращение к списку задач исполнителя.
    """
    user_id = callback_query.from_user.id
    tasks = db.get_tasks_by_user(user_id)

    if not tasks:
        await callback_query.message.edit_text("У вас пока нет задач.")
        return

    # Создаем кнопки для задач
    task_buttons = [
        InlineKeyboardButton(
            text=f"{task['title'][:25]}...",  # Укороченное название задачи
            callback_data=f"view_my_task:{task['id']}"
        )
        for task in tasks if not task['status'] == 'completed' and not task['status'] == 'done'
    ]

    # Формируем клавиатуру
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[button] for button in task_buttons]  # Кнопки задач
    )

    # Удаляем старое сообщение и отправляем список задач
    await callback_query.message.delete()
    await callback_query.message.answer("📋 Ваши задачи:", reply_markup=keyboard) # Используем edit_text

    
@router.callback_query(F.data.startswith("take_task:"))
async def take_task_handler(callback_query: CallbackQuery, db: Database, bot: Bot):
    user_id = callback_query.from_user.id
    task_id = callback_query.data.split(":")[1]

    tasks = db.get_tasks_by_user(user_id)
    # Используем any и более явные условия
    is_working = any(task["status"] == "is_on_work" for task in tasks)
    is_completed = any(task["status"] in ("done", "completed") for task in tasks)

    if is_working:
        await callback_query.message.answer(
            "Вы уже работаете над задачей, завершите её, чтобы перейти к следующей!",
            reply_markup=task_executor_keyboard(task_id)
        )
    elif is_completed:
        return  # Ничего не делаем, если задача уже завершена
    else:
        db.update_task_status(task_id, "is_on_work")
        task = db.get_task_by_id(task_id)
        await callback_query.message.edit_reply_markup(reply_markup=task_executor_keyboarda(task_id))
        await callback_query.message.answer("Вы взялись за задачу!")
    
        # Отправка уведомления в общий канал
        task_text = (
           f"🛠️ <b>Задача взята в работу:</b>\n"
            f"🔖 <b>Название:</b> {task['title']}\n"
            f"👤 <b>Исполнитель:</b> {db.get_user_by_id(user_id)['username']}\n"
        )
        await send_channel_message(bot, CHANNEL_ID, task_text)


@router.callback_query(F.data.startswith("complete_task:"))
async def complete_task_handler(callback_query: CallbackQuery, state: FSMContext, db: Database, bot: Bot):
    task_id = callback_query.data.split(":")[1]
    await state.update_data(task_id=task_id)  # Сохраняем task_id в состояние
    print(f"Task ID: {task_id}")
    await callback_query.message.answer("Отправьте фото выполненной работы:")
    await state.set_state(ReportTaskFSM.photo)

@router.message(F.photo, StateFilter(ReportTaskFSM.photo))
async def handle_report_photo(message: Message, state: FSMContext):
    # Получаем фото
    photo_id = message.photo[-1].file_id  # Берем наибольший размер фото
    await state.update_data(photo=photo_id)  # Сохраняем фото в состояние
    
    # Переход на следующий шаг
    await message.answer("Фото принято. Теперь отправьте текстовый отчет:")
    await state.set_state(ReportTaskFSM.report_text)

@router.message(F.text, StateFilter(ReportTaskFSM.report_text))
async def handle_report_text(message: Message, state: FSMContext, db: Database, bot: Bot):
    # Получаем текст отчета
    report_text = message.text

    # Получаем сохраненные данные из состояния
    data = await state.get_data()
    task_id = data["task_id"]
    photo_id = data["photo"]

    # Обновляем задачу в базе данных
    db.update_task_report(task_id, report_text, photo_id)
    task = db.get_task_by_id(task_id)

    # Отправка уведомления в общий канал
    user_id = message.from_user.id
    task_text = (
        f"✅ <b>Задача завершена:</b>\n"
        f"🔖 <b>Название:</b> {task['title']}\n"
        f"👤 <b>Исполнитель:</b> {db.get_user_by_id(user_id)['username']}\n"
    )
    await send_channel_message(bot, CHANNEL_ID, task_text)


    
    # Завершаем FSM
    await state.clear()
    await message.answer("Отчет отправлен администратору. Спасибо!")

@router.message(F.text == "Завершенные задачи")
async def done_tasks(message: Message, db: Database):

    user_id = message.from_user.id
    tasks = db.get_tasks_by_user(user_id)

    if not tasks:
        await message.answer("У вас пока нет завершенных задач.")
        return
    
    # Создаем кнопки для задач
    task_buttons = [
        InlineKeyboardButton(
            text=f"{task['title'][:25]}...",  # Укороченное название задачи
            callback_data=f"view_my_done_task:{task['id']}"
        )
        for task in tasks if task['status'] == 'done' or task['status'] == 'completed'
    ]

    # Формируем клавиатуру
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[button] for button in task_buttons]  # Кнопки задач
    )

    # Отправляем список задач
    await message.answer("📋 Ваши завершенные задачи:", reply_markup=keyboard)

@router.message(F.text == "Моя статистика")
async def executor_statistics(message: types.Message, db: Database):
    """Отображение статистики для исполнителя."""
    user_id = message.from_user.id

    total_user_tasks = db.get_user_tasks_count(user_id)
    pending_user_tasks = db.get_user_tasks_count_by_status(user_id, "pending")
    is_on_work_user_tasks = db.get_user_tasks_count_by_status(user_id, "is_on_work")
    done_user_tasks = db.get_user_tasks_count_by_status(user_id, "done")
    completed_user_tasks = db.get_user_tasks_count_by_status(user_id, "completed")

    response = (
        " <b>Ваша статистика:</b>\n\n"
        f"<b>Задачи:</b>\n"
        f"Всего: {total_user_tasks}\n"
        f"Ожидают выполнения: {pending_user_tasks}\n"
        f"В работе: {is_on_work_user_tasks}\n"
        f"Выполнены: {done_user_tasks}\n"
        f"Завершены: {completed_user_tasks}\n"
    )

    await message.answer(response, parse_mode="HTML")
    await message.delete()