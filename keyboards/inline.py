from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

ADD_COMMENT_BUTTON = "Добавить комментарий" # переместил сюда константу

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
        [InlineKeyboardButton(text="📲 Взяться за задачу", callback_data=f"take_task:{task_id}")],
        [InlineKeyboardButton(text="🗓️ Запросить перенос", callback_data=f"request_redeadline:{task_id}")],
        [
            InlineKeyboardButton(text="💬 Коммент", callback_data=f"add_comment_exec:{task_id}"),
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_my_tasks")
        ]
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
        [InlineKeyboardButton(text="📲 Взяться за задачу", callback_data=f"complete_task:{task_id}")],
        [InlineKeyboardButton(text="🗓️ Запросить перенос", callback_data=f"request_redeadline:{task_id}")],
        [
            InlineKeyboardButton(text="💬 Коммент", callback_data=f"add_comment_exec:{task_id}"),
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_my_tasks")
        ]
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
            [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_task:{task_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_task_list")]
        ]
    elif status == 'is_on_work':
        buttons = [
            [InlineKeyboardButton(text="✅ Завершить", callback_data=f"complete_task:{task_id}")],
            [InlineKeyboardButton(text="🗓️ Перенести дедлайн", callback_data=f"redeadline:{task_id}")],
            [
                InlineKeyboardButton(text="💬 Коммент", callback_data=f"add_comment:{task_id}"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_task_list")
            ]
        ]
    elif status == 'done':
        buttons = [
        [InlineKeyboardButton(text="☑️ Проверить", callback_data=f"checktask:{task_id}")],
        [InlineKeyboardButton(text="💬 Коммент", callback_data=f"add_comment:{task_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_filter_list:{status}")]
        # [InlineKeyboardButton(text="Удалить задачу", callback_data=f"delete_task:{task_id}")]
        ]
    elif status == 'pending':
        buttons = [
            [InlineKeyboardButton(text="📲 Взяться за задачу", callback_data=f"take_task:{task_id}")],
            [InlineKeyboardButton(text="🔄 Переназначить", callback_data=f"reassign_task:{task_id}")],
            [InlineKeyboardButton(text="🗓️ Перенести дедлайн", callback_data=f"redeadline:{task_id}")],
            [
                InlineKeyboardButton(text="💬 Коммент", callback_data=f"add_comment:{task_id}"),
                InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_task:{task_id}")
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_task_list")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="📲 Взяться за задачу", callback_data=f"take_task:{task_id}")],
            [InlineKeyboardButton(text="🔄 Переназначить", callback_data=f"reassign_task:{task_id}")],
            [InlineKeyboardButton(text="🗓️ Перенести дедлайн", callback_data=f"redeadline:{task_id}")],
            [
                InlineKeyboardButton(text="💬 Коммент", callback_data=f"add_comment:{task_id}"),
                InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_task:{task_id}")
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_task_list")]
        ]
    # Создаем клавиатуру с этими кнопками
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def task_admin_keyboardb(task_id: int):
    """
    Создает клавиатуру для исполнителя задачи.
    """
    # Создаем список кнопок с callback_data
    buttons = [
        [
            InlineKeyboardButton(text="✅ Потдвердить", callback_data=f"approved:{task_id}"),
            InlineKeyboardButton(text="❌ Отказать", callback_data=f"rejected:{task_id}")
        ],
        [
            InlineKeyboardButton(text="💬 Коммент", callback_data=f"add_comment:{task_id}"),
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_task_list")
        ]
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


def user_list_keyboard(users):
    """Создает клавиатуру со списком пользователей."""
    buttons = []
    for user in users:
        buttons.append([InlineKeyboardButton(text=f"{user['username']} ({user['role']})", callback_data=f"user_info:{user['user_id']}")]) # callback data для получения инфо о пользователе
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def role_selection_keyboard(user_id):
    """Создает клавиатуру для выбора роли."""
    buttons = [
        [
            InlineKeyboardButton(text="👑 Админ", callback_data=f"set_role:Админ:{user_id}"),
            InlineKeyboardButton(text="👨‍🔧 Исполнитель", callback_data=f"set_role:Исполнитель:{user_id}")
        ],
        [InlineKeyboardButton(text="📊 Статистика пользователя", callback_data=f"user_stats:{user_id}")],
        [InlineKeyboardButton(text="❌ Удалить пользователя", callback_data=f"delete_user:{user_id}")], # Новая кнопка
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_users")] # Кнопка "Назад"
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def empty_keyboard():
    """Пустая клавиатура."""
    # buttons = [[InlineKeyboardButton(text="Статистика пользователей", callback_data="view_users_for_stats")]]

    return InlineKeyboardMarkup(inline_keyboard=[])