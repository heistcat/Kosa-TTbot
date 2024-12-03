from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.reply import admin_menu_keyboard, skip_photo
from keyboards.inline import assign_executor_keyboard, task_admin_keyboard, task_admin_keyboarda, task_admin_keyboardb, reassign_executor_keyboard
from database import Database
from aiogram.types import CallbackQuery, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton


router = Router()

# Машина состояний для создания задачи
class CreateTaskFSM(StatesGroup):
    title = State()
    description = State()
    deadline = State()
    photo = State()
    assign = State()
    selected_executors = State()  # Для хранения выбранных исполнителей


async def notify_executors(bot: Bot, executors: list[int], task_title: str, task_deadline: str):
    """
    Отправка уведомлений исполнителям о новой задаче или переназначении.
    
    :param bot: Экземпляр бота.
    :param executors: Список Telegram ID исполнителей.
    :param task_id: ID задачи.
    :param task_title: Название задачи.
    :param task_deadline: Дедлайн задачи.
    """
    for executor_id in executors:
        try:
            # Создаем инлайн-кнопку для быстрого перехода к задаче
            # keyboard = InlineKeyboardMarkup(inline_keyboard=[
            #     [InlineKeyboardButton(text="Посмотреть задачу", callback_data=f"view_task:{task_id}")]
            # ])
            
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
    await message.answer("Введите название задачи:", reply_markup=ReplyKeyboardRemove())
    await message.delete()  # Удаляем сообщение с выбором
    await state.set_state(CreateTaskFSM.title)

# Ввод названия задачи
@router.message(F.text, StateFilter(CreateTaskFSM.title))
async def handle_task_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Введите описание задачи:")
    await message.delete()  # Удаляем сообщение с выбором
    await state.set_state(CreateTaskFSM.description)

# Ввод описания задачи
@router.message(F.text, StateFilter(CreateTaskFSM.description))
async def handle_task_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите дедлайн задачи (в формате ДД-ММ):")
    await message.delete()  # Удаляем сообщение с выбором
    await state.set_state(CreateTaskFSM.deadline)

# Ввод дедлайна задачи
@router.message(F.text, StateFilter(CreateTaskFSM.deadline))
async def handle_task_deadline(message: Message, state: FSMContext):
    await state.update_data(deadline=message.text)
    await message.answer("Загрузите фото-референс задачи:", reply_markup=skip_photo)
    await message.delete()  # Удаляем сообщение с выбором
    await state.set_state(CreateTaskFSM.photo)

# Загрузка фото-референса
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
    
    # await state.update_data(selected_executors=[])
    await message.answer(
        "Выберите исполнителей для задачи (нажимайте на имена). Когда закончите, нажмите 'Завершить выбор'.",
        # reply_markup=assign_executor_keyboard(executors, multiple=True)
        reply_markup=assign_executor_keyboard(executors, multiple=True)
    )
    await message.delete()  # Удаляем сообщение с выбором
    await message.answer("⬆️⬆️⬆️", reply_markup=ReplyKeyboardRemove())
    # await message.delete()  # Удаляем сообщение с выбором
    await state.set_state(CreateTaskFSM.selected_executors)


# Обновление обработчика пропуска фото
@router.message(F.text == "Пропустить", StateFilter(CreateTaskFSM.photo))
async def skip_task_photo(message: Message, state: FSMContext):
    # Если администратор нажал "Пропустить", продолжаем без фото
    await state.update_data(photo=None)  # Фото отсутствует

    db = Database()
    executors = db.get_all_users()
    if not executors:
        await message.answer("Нет доступных исполнителей.")
        await state.clear()
        return

    # Переход к этапу выбора исполнителей
    await message.answer(
        "Выберите исполнителей для задачи (нажимайте на имена). Когда закончите, нажмите 'Завершить выбор'.",
        reply_markup=assign_executor_keyboard(executors, multiple=True)
    )
    await message.delete()  # Удаляем сообщение с выбором
    await message.answer("⬆️⬆️⬆️", reply_markup=ReplyKeyboardRemove())
    await message.delete()  # Удаляем сообщение с выбором
    await state.set_state(CreateTaskFSM.selected_executors)


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
        ref_photo=data["photo"] or None,
        assigned_to=",".join(map(str, executors)),  # Храним как строку с ID через запятую
        report_text="#",
        report_photo="#"
    )

    await notify_executors(bot, executors, data["title"], data['deadline'])

    await callback_query.message.answer("Задача успешно создана!", reply_markup=admin_menu_keyboard)
    await callback_query.message.delete()  # Удаляем сообщение с выбором
    await state.clear()

# Просмотр статистики
@router.message(F.text == "Статистика")
async def admin_statistics(message: Message, db: Database):
    stats = db.get_all_tasks().count # Предполагаемая функция получения статистики
    # done_tasks = [stat for stat in stats if stat['status'] == 'done']
    # completed_tasks = [stat for stat in stats if stat['status'] == 'completed']
    overdue_tasks = 'under development'

    response = (
        f'в зарзарботке'
        # f"Всего задач: {stats}\n"
        # f"Завершено: {[completed for completed in completed_tasks]}\n"
        # f"Выполнено: {[done for done in done_tasks]}\n"
        # f"Просрочено: {overdue_tasks}"
    )
    await message.answer(response)
    await message.delete()  # Удаляем сообщение с выбором



@router.message(F.text == "Просмотр задач")
async def view_tasks(message: Message, db: Database):
    """
    Отображение задач с возможностью фильтрации через инлайн-кнопки.
    """
    tasks = db.get_all_tasks()

    if not tasks:
        await message.answer("Нет задач.")
        return

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

    # Отправляем сообщение с задачами
    await message.answer("📋 Все задачи:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("view_task:"))
async def view_task(callback_query: CallbackQuery, db: Database):
    """
    Отображение деталей задачи с инлайн-кнопками и кнопкой "Назад к списку".
    """
    task_id = int(callback_query.data.split(":")[1])  # Получаем ID задачи
    task = db.get_task_by_id(task_id)

    if not task:
        await callback_query.message.edit_text("Задача не найдена.")
        return

    # Формируем текст задачи
    assigned_users = ", ".join([
        f"@{db.get_user_by_id(int(user))['username']}"
        for user in task['assigned_to'].split(",")
    ])
    task_text = (
        f"📋 <b>Детали задачи:</b>\n\n"
        f"🔹 <b>Название:</b> {task['title']}\n"
        f"🔹 <b>Описание:</b> {task['description']}\n"
        f"🔹 <b>Дедлайн:</b> {task['deadline']}\n"
        f"🔹 <b>Исполнители:</b> {assigned_users}\n"
        f"🔹 <b>Статус:</b> {task['status']}"
    )

   
    # Удаляем старое сообщение (список задач) и отправляем новое с задачей
    # await callback_query.message.delete()

    # Отправляем сообщение с задачей и фото (если есть)
    if task["ref_photo"]:
        await callback_query.message.answer_photo(
            photo=task["ref_photo"],  # Идентификатор файла фотографии
            caption=task_text,
            reply_markup=task_admin_keyboarda(task_id, task['status']) if task['status'] == 'done' else task_admin_keyboard(task_id, task['status']),
            parse_mode="HTML"
        )
    else:
        await callback_query.message.answer(
            task_text,
            reply_markup=task_admin_keyboarda(task_id, task['status']) if task['status'] == 'done' else task_admin_keyboard(task_id, task['status']),
            parse_mode="HTML"
        )
    
    # Удаляем старое сообщение (список задач) и отправляем новое с задачей
    await callback_query.message.delete()



@router.callback_query(F.data == "back_to_task_list")
async def back_to_task_list(callback_query: CallbackQuery, db: Database):
    """
    Возвращение к списку задач.
    """
    tasks = db.get_all_tasks()

    if not tasks:
        await callback_query.message.edit_text("Нет задач.")
        return

    # Создаем кнопки для задач
    task_buttons = [
        InlineKeyboardButton(
            text=f"{task['title'][:25]}...",  # Укороченное название задачи
            callback_data=f"view_task:{task['id']}"
        )
        for task in tasks if not task['status'] == 'completed' and not task['status']=='done'
    ]

    # Кнопки фильтрации
    filter_buttons = [
        InlineKeyboardButton(text="✅ Выполненные задачи", callback_data="filter:done"),
        InlineKeyboardButton(text="🛑 Завершенные задачи", callback_data="filter:completed")
    ]

    # Формируем клавиатуру
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [button] for button in task_buttons
        ] + [filter_buttons]  # Добавляем фильтры отдельной строкой
    )

    # Удаляем старое сообщение и отправляем список задач
    await callback_query.message.delete()
    await callback_query.message.answer("📋 Все задачи:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("back_to_filter_list:"))
async def back_to_filter_list(callback_query: CallbackQuery, db: Database):
    status = callback_query.data.split(":")[1]  # Получаем статус из callback_data
    tasks = db.get_all_tasks()

    # Фильтруем задачи по статусу
    filtered_tasks = [task for task in tasks if task['status'] == status]

    # Создаем кнопки для отфильтрованных задач
    task_buttons = [
        InlineKeyboardButton(
            text=f"{task['title'][:25]}...",  # Укороченное название задачи
            callback_data=f"view_task:{task['id']}"
        )
        for task in filtered_tasks
    ]

    # Генерируем клавиатуру
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [button] for button in task_buttons  # Каждая кнопка задачи в отдельной строке
        ]
    )


    await callback_query.message.delete()
    # Редактируем сообщение с новой клавиатурой
    await callback_query.message.answer(f"📋 Задачи со статусом '{status}':", reply_markup=keyboard)

@router.callback_query(F.data.startswith("filter:"))
async def filter_tasks(callback_query: CallbackQuery, db: Database):
    """
    Фильтрация задач по статусу.
    """
    status = callback_query.data.split(":")[1]  # Получаем статус из callback_data
    tasks = db.get_all_tasks()

    # Фильтруем задачи по статусу
    filtered_tasks = [task for task in tasks if task['status'] == status]

    if not filtered_tasks:
        await callback_query.message.edit_text("Нет задач с выбранным статусом.")
        return

    # Создаем кнопки для отфильтрованных задач
    task_buttons = [
        InlineKeyboardButton(
            text=f"{task['title'][:25]}...",  # Укороченное название задачи
            callback_data=f"view_task:{task['id']}"
        )
        for task in filtered_tasks
    ]

    # Генерируем клавиатуру
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [button] for button in task_buttons  # Каждая кнопка задачи в отдельной строке
        ]
    )

    # Редактируем сообщение с новой клавиатурой
    await callback_query.message.edit_text(f"📋 Задачи со статусом '{status}':", reply_markup=keyboard)

        

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





# @router.callback_query(F.data.startswith("reassign_"))
# async def reassign_executor(callback_query, state: FSMContext):
#     executor_id = callback_query.data.split("_")[1]
#     data = await state.get_data()
#     selected_executors = data.get("selected_executors", [])
    
#     if executor_id not in selected_executors:
#         selected_executors.append(executor_id)  # Добавляем исполнителя
#         await callback_query.answer("Исполнитель добавлен!")
#     else:
#         selected_executors.remove(executor_id)  # Убираем исполнителя
#         await callback_query.answer("Исполнитель удален!")
    
#     await state.set_state(selected_executors)
#     print(f'{selected_executors}')

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

    await callback_query.message.answer("Исполнители успешно назначены!")
    await callback_query.message.delete()  # Удаляем сообщение с выбором
    await state.clear()


@router.callback_query(F.data.startswith("checktask:"))
async def checktask_executor(callback_query, state: FSMContext, db: Database):
    # executor_id = callback_query.data.split("_")[1].split(":")[0]
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
    await callback_query.message.delete()  # Удаляем сообщение с выбором

@router.callback_query(F.data.startswith("approved:"))
async def complete_task_executor(callback_query: CallbackQuery, db: Database):
    # executor_id = callback_query.data.split("_")[1].split(":")[0]
    task_id = callback_query.data.split(":")[1]
    # task = db.get_task_by_id(task_id)
    db.update_task_status(task_id, 'completed')
    await callback_query.message.answer("Задача подтверждена")
    # await state.clear()
    


@router.callback_query(F.data.startswith("add_comment:"))
async def add_comment_handler(callback_query: CallbackQuery):
    db = Database()
    task_id = callback_query.data.split(":")[1]
    oldDesc = db.get_task_by_id(task_id)['description']
    await callback_query.message.answer("В разработке.")
    # updateDesc = f'{oldDesc}\n\n{newDesc}'


@router.callback_query(F.data.startswith("delete_task:"))
async def delete_task_handler(callback_query: CallbackQuery):
    task_id = callback_query.data.split(":")[1]
    db = Database()
    try:
        db.delete_task(task_id=task_id)
        await callback_query.message.answer("Задача удалена!", show_alert=True)
    except Exception as e:
        await callback_query.message.answer(f"Ошибка при удалении: {e}", show_alert=True)
    await callback_query.message.delete()  # Удаляем сообщение с выбором


