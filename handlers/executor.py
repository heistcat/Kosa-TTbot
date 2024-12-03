from aiogram import Router, F, types
from database import Database
from keyboards.inline import task_executor_keyboard, task_executor_keyboarda
from aiogram.types import CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup



router = Router()

class ReportTaskFSM(StatesGroup):
    task_id = State()
    photo = State()
    report_text = State()

@router.message(F.text == "Мои задачи")
async def my_tasks_handler(message: Message, db: Database):
    """
    Отображение списка задач для исполнителя.
    """
    user_id = message.from_user.id
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

# @router.message(F.text == "Моя статистика")
# async def statistics_task_handler(message: types.Message, db: Database):
#     """Завершение задачи исполнителем."""
#     user_id = message.from_user.id
#     tasks = db.get_my_statistics(user_id)
#     all_tasks =db.get_tasks_by_user(user_id)

#     if tasks:
#         await message.answer(
#             f"Все: {all_tasks}\n"
#             f"Завершено: {tasks['tasks_done']}\n"
#             f"Просрочено: {tasks['tasks_overdue']}\n"     
#         )


@router.callback_query(F.data.startswith("view_my_task:"))
async def view_my_task(callback_query: CallbackQuery, db: Database):
    """
    Отображение деталей задачи для исполнителя.
    """
    task_id = int(callback_query.data.split(":")[1])  # Получаем ID задачи
    task = db.get_task_by_id(task_id)

    if not task:
        await callback_query.message.edit_text("Задача не найдена.")
        return

    # Формируем текст задачи
    task_text = (
        f"📋 <b>Детали задачи:</b>\n\n"
        f"🔹 <b>Название:</b> {task['title']}\n"
        f"🔹 <b>Описание:</b> {task['description']}\n"
        f"🔹 <b>Дедлайн:</b> {task['deadline']}\n"
        f"🔹 <b>Статус:</b> {task['status']}"
    )

    # # Инлайн-кнопки для управления задачей
    # task_keyboard = InlineKeyboardMarkup(
    #     inline_keyboard=[
    #         [InlineKeyboardButton(text="Завершить задачу", callback_data=f"complete_task:{task_id}")],
    #         [InlineKeyboardButton(text="Назад к списку", callback_data="back_to_my_tasks")]
    #     ]
    # )

    # Удаляем старое сообщение (список задач) и отправляем новое с задачей
    await callback_query.message.delete()

    # Отправляем сообщение с задачей и фото (если есть)
    if task["ref_photo"]:
        await callback_query.message.answer_photo(
            photo=task["ref_photo"],  # Идентификатор файла фотографии
            caption=task_text,
            reply_markup=task_executor_keyboard(task_id) if task['status'] == 'pending' else task_executor_keyboarda(task_id),
            parse_mode="HTML"
        )
    else:
        await callback_query.message.answer(
            task_text,
            reply_markup=task_executor_keyboard(task_id) if task['status'] == 'pending' else task_executor_keyboarda(task_id),
            parse_mode="HTML"
        )


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
    await callback_query.message.answer("📋 Ваши задачи:", reply_markup=keyboard)

    
@router.callback_query(F.data.startswith("take_task:"))
async def take_task_handler(callback_query: CallbackQuery):
    db = Database()
    user_id = callback_query.message.from_user.id
    task_id = callback_query.data.split(":")[1]
    
    # Проверяем, есть ли у пользователя задачи со статусом "is_on_work"
    tasks = db.get_tasks_by_user(user_id)
    is_busy = any(task["status"] == "is_on_work" for task in tasks)
    is_done = any(task["status"] == "done" for task in tasks)
    
    if is_busy:
        # Если пользователь уже работает над задачей
        await callback_query.message.answer(
            "Вы уже работаете над задачей, завершите её, чтобы перейти к следующей!",
            reply_markup=task_executor_keyboard(task_id)
        )
    elif is_done:
        return
    else:
        # Если пользователь свободен, обновляем статус задачи
        db.update_task_status(task_id, "is_on_work")
        await callback_query.message.edit_reply_markup(
            reply_markup=task_executor_keyboarda(task_id)
        )
        await callback_query.message.answer("Вы взялись за задачу!")

@router.callback_query(F.data == "add_comment")
async def add_comment_handler(callback_query: CallbackQuery):
    db = Database()
    # task_id = callback_query.data.split(":")[1]
    # oldDesc = db.get_task_by_id(task_id)['description']
    await callback_query.message.answer("В разработке.")
    # updateDesc = f'{oldDesc}\n\n{newDesc}'
    # await callback_query.message.answer("Добавьте комментарий.")

# @router.callback_query(F.data.startswith("complete_task:"), StateFilter(ReportTaskFSM.task_id))
@router.callback_query(F.data.startswith("complete_task:"))
async def complete_task_handler(callback_query: CallbackQuery, state: FSMContext):
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
async def handle_report_text(message: Message, state: FSMContext, db: Database):
    # Получаем текст отчета
    report_text = message.text

    # Получаем сохраненные данные из состояния
    data = await state.get_data()
    task_id = data["task_id"]
    photo_id = data["photo"]

    # Обновляем задачу в базе данных
    db.update_task_report(task_id, report_text, photo_id)
    
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
    
@router.callback_query(F.data.startswith("view_my_done_task:"))
async def view_my_done_task(callback_query: CallbackQuery, db: Database):
    """
    Отображение деталей задачи для исполнителя.
    """
    task_id = int(callback_query.data.split(":")[1])  # Получаем ID задачи
    task = db.get_task_by_id(task_id)

    if not task:
        await callback_query.message.edit_text("Задача не найдена.")
        return

    # Формируем текст задачи
    task_text = (
        f"📋 <b>Детали задачи:</b>\n\n"
        f"🔹 <b>Название:</b> {task['title']}\n"
        f"🔹 <b>Описание:</b> {task['description']}\n"
        f"🔹 <b>Дедлайн:</b> {task['deadline']}\n"
        f"🔹 <b>Статус:</b> {task['status']}"
    )

    # # Инлайн-кнопки для управления задачей
    # task_keyboard = InlineKeyboardMarkup(
    #     inline_keyboard=[
    #         [InlineKeyboardButton(text="Завершить задачу", callback_data=f"complete_task:{task_id}")],
    #         [InlineKeyboardButton(text="Назад к списку", callback_data="back_to_my_tasks")]
    #     ]
    # )

    # Удаляем старое сообщение (список задач) и отправляем новое с задачей
    await callback_query.message.delete()

    # Отправляем сообщение с задачей и фото (если есть)
    if task["ref_photo"]:
        await callback_query.message.answer_photo(
            photo=task["ref_photo"],  # Идентификатор файла фотографии
            caption=task_text,
            # reply_markup=None,
            parse_mode="HTML"
        )
    else:
        await callback_query.message.answer(
            task_text,
            # reply_markup=None,
            parse_mode="HTML"
        )
