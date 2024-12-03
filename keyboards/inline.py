from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def assign_executor_keyboard(executors, multiple=False):
    """
    Создает клавиатуру для выбора исполнителей.
    :param executors: Список исполнителей, содержащий user_id и имя.
    :param multiple: Флаг для добавления кнопки завершения выбора.
    :return: InlineKeyboardMarkup
    """
    buttons = [
        [InlineKeyboardButton(text=executor['name'], callback_data=f"assign_{executor['user_id']}")]
        for executor in executors
    ]
    if multiple:
        buttons.append([InlineKeyboardButton(text="Завершить выбор", callback_data="finish_selection")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)



def task_executor_keyboard(task_id):
    """
    Создает клавиатуру для исполнителя задачи.
    """
    # Создаем список кнопок с callback_data
    buttons = [
        [InlineKeyboardButton(text="Взяться за задачу", callback_data=f"take_task:{task_id}")],
        [InlineKeyboardButton(text="Добавить комментарий", callback_data=f"add_comment{task_id}")],
        [InlineKeyboardButton(text="Назад к списку", callback_data="back_to_my_tasks")]
        # [InlineKeyboardButton(text="Завершить задачу", callback_data="complete_task")]
    ]
    # Создаем клавиатуру с этими кнопками
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def task_executor_keyboarda(task_id):
    """
    Создает клавиатуру для исполнителя задачи.
    """
    # Создаем список кнопок с callback_data
    buttons = [
        # [InlineKeyboardButton(text="Взяться за задачу", callback_data="take_task")],
        [InlineKeyboardButton(text="Завершить задачу", callback_data=f"complete_task:{task_id}")],
        [InlineKeyboardButton(text="Добавить комментарий", callback_data=f"add_comment:{task_id}")],
        [InlineKeyboardButton(text="Назад к списку", callback_data="back_to_my_tasks")]
    ]
    # Создаем клавиатуру с этими кнопками
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def task_admin_keyboard(task_id: int, status):
    """
    Создает клавиатуру для исполнителя задачи.
    """

    if status == 'completed':
    # Создаем список кнопок с callback_data
        buttons = [
            [InlineKeyboardButton(text="Удалить задачу", callback_data=f"delete_task:{task_id}")],
            [InlineKeyboardButton(text="Назад к списку", callback_data="back_to_task_list")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="Переназначить", callback_data=f"reassign_task:{task_id}")],
            [InlineKeyboardButton(text="Добавить комментарий", callback_data=f"add_comment:{task_id}")],
            [InlineKeyboardButton(text="Удалить задачу", callback_data=f"delete_task:{task_id}")],
            [InlineKeyboardButton(text="Назад к списку", callback_data="back_to_task_list")]
        ]
    # Создаем клавиатуру с этими кнопками
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def task_admin_keyboarda(task_id: int, status):
    """
    Создает клавиатуру для исполнителя задачи.
    """
    # Создаем список кнопок с callback_data
    buttons = [
        [InlineKeyboardButton(text="Проверить", callback_data=f"checktask:{task_id}")],
        [InlineKeyboardButton(text="Добавить комментарий", callback_data=f"add_comment:{task_id}")],
        [InlineKeyboardButton(text="Назад к списку", callback_data=f"back_to_filter_list:{status}")]
        # [InlineKeyboardButton(text="Удалить задачу", callback_data=f"delete_task:{task_id}")]
    ]
    # Создаем клавиатуру с этими кнопками
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def task_admin_keyboardb(task_id: int):
    """
    Создает клавиатуру для исполнителя задачи.
    """
    # Создаем список кнопок с callback_data
    buttons = [
        [InlineKeyboardButton(text="Потдвердить", callback_data=f"approved:{task_id}")],
        [InlineKeyboardButton(text="Добавить комментарий", callback_data=f"add_comment:{task_id}")],
    ]
    # Создаем клавиатуру с этими кнопками
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def reassign_executor_keyboard(executors, task_id, allow_finish=False):
    """
    Клавиатура для выбора нескольких исполнителей.
    :param executors: Список исполнителей.
    :param task_id: ID задачи.
    :param allow_finish: Добавлять ли кнопку "Завершить выбор".
    :return: InlineKeyboardMarkup
    """
    buttons = [
        [InlineKeyboardButton(text=executor['name'], callback_data=f"toggle_executor:{executor['user_id']}")]
        for executor in executors
    ]
    if allow_finish:
        buttons.append([InlineKeyboardButton(text="Завершить выбор", callback_data="finish_selectionw")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)