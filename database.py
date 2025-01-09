import sqlite3
import time
from datetime import datetime

class Database:
    def __init__(self, db_path="database.db"):
        # Инициализация подключения к базе данных
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row  # Удобный формат возвращения данных
        self.cursor = self.connection.cursor()  # Создание курсора для выполнения запросов
        self.create_tables()

    def create_tables(self):
        """Создание таблиц, если их нет."""
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE,
            username TEXT,
            name TEXT,
            phone_number TEXT,
            birth_date TEXT DEFAULT 'not set',
            role TEXT DEFAULT 'Исполнитель'
        )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            deadline INTEGER,
            deadline_formatted TEXT,
            ref_photo TEXT,
            assigned_to TEXT,
            location TEXT,
            status TEXT DEFAULT 'pending',
            report_text TEXT DEFAULT '_',
            report_photo TEXT DEFAULT '_',
            comments TEXT DEFAULT '_',  -- Новое поле для комментариев
            FOREIGN KEY (assigned_to) REFERENCES users(user_id)
        )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS su (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE
        )
        """)
        self.connection.commit()


    def register_su(self, user_id):
        self.cursor.execute("""
        INSERT INTO su (user_id) VALUES (?)
        """, (user_id,))
        self.connection.commit()

    def get_su_by_id(self, user_id):
        query = "SELECT * FROM su WHERE user_id = ?"
        return self.connection.execute(query, (user_id,)).fetchone()

    # --- Методы для работы с пользователями ---
    def register_user(self, user_id, username, name, phone_number, birth_date, role):
        """Добавление нового пользователя."""
        self.connection.execute("""
        INSERT INTO users (user_id, username, name, phone_number, birth_date, role)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, username, name, phone_number, birth_date, role))
        self.connection.commit()

    def update_user_role(self, user_id, role):
        """Обновляет роль пользователя."""
        self.cursor.execute("""
        UPDATE users
        SET role = ?
        WHERE user_id = ?
        """, (role, user_id))
        self.connection.commit()

    def delete_user(self, user_id):
        """Удаляет пользователя из базы данных."""
        self.cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        self.connection.commit()

    def get_user(self, user_id):
        """Получение информации о пользователе по ID."""
        query = "SELECT * FROM users WHERE user_id = ?"
        return self.connection.execute(query, (user_id,)).fetchone()

    def get_all_users(self):
        """Получение всех пользователей."""
        query = "SELECT * FROM users"
        return self.connection.execute(query).fetchall()

    def get_all_executors(self):
        """Получение всех исполнителей (executor)."""
        query = "SELECT * FROM users WHERE role = 'Исполнитель'"
        return self.connection.execute(query).fetchall()

    # --- Методы для работы с задачами ---
    def create_task(self, title, description, ref_photo, deadline, deadline_formatted, assigned_to, report_text, report_photo, location):
        """Создание задачи."""
        timestamp = int(time.mktime(datetime.strptime(deadline, "%d-%m-%Y %H:%M").timetuple()))
        self.connection.execute("""
        INSERT INTO tasks (title, description, ref_photo, deadline, deadline_formatted, assigned_to, report_text, report_photo, location)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, description, ref_photo, timestamp, deadline_formatted, assigned_to, report_text, report_photo, location))
        self.connection.commit()

    def update_task_assigned_to(self, assigned_to, task_id):
        """Переназначение исполнителя"""
        self.connection.execute("""
        UPDATE tasks
        SET assigned_to = ?
        WHERE id = ?
        """, (assigned_to, task_id)
        )
        self.connection.commit()

    def update_task_desc(self, description, task_id):
        """Переназначение исполнителя"""
        self.connection.execute("""
        UPDATE tasks
        SET description = ?
        WHERE id = ?
        """, (description, task_id)
        )
        self.connection.commit()


    def get_tasks_by_user(self, user_id):
        """Получение задач, назначенных конкретному пользователю."""
        query = """
        SELECT *, strftime('%d-%m-%Y %H:%M', deadline, 'unixepoch') AS deadline_formatted
        FROM tasks
        WHERE ',' || assigned_to || ',' LIKE '%,' || ? || ',%';
        """
        return self.connection.execute(query, (user_id,)).fetchall()

    def get_task_by_id(self, task_id):
        """Получение задачи по ID."""
        query = """
        SELECT *, strftime('%d-%m-%Y %H:%M', deadline, 'unixepoch') AS deadline_formatted
        FROM tasks WHERE id = ?
        """
        return self.connection.execute(query, (task_id,)).fetchone()

    def update_task_status(self, task_id, status):
        """Обновление статуса задачи."""
        self.connection.execute("""
        UPDATE tasks SET status = ? WHERE id = ?
        """, (status, task_id))
        self.connection.commit()

    def update_task_report(self, task_id, report_text, report_photo):
        """Добавление отчета к задаче."""
        self.connection.execute("""
        UPDATE tasks SET report_text = ?, report_photo = ?, status = 'done' WHERE id = ?
        """, (report_text, report_photo, task_id))
        self.connection.commit()

    def get_all_tasks(self):
        """Получение всех задач."""
        query = """
        SELECT *, strftime('%d-%m-%Y %H:%M', deadline, 'unixepoch') AS deadline_formatted FROM tasks ORDER BY deadline ASC
        """
        return self.connection.execute(query).fetchall()

    # --- Методы для работы со статистикой ---
    def increment_task_done(self, user_id):
        """Увеличить счетчик выполненных задач."""
        self.connection.execute("""
        UPDATE statistics SET tasks_done = tasks_done + 1 WHERE user_id = ?
        """, (user_id,))
        self.connection.commit()

    def increment_task_overdue(self, user_id):
        """Увеличить счетчик просроченных задач."""
        self.connection.execute("""
        UPDATE statistics SET tasks_overdue = tasks_overdue + 1 WHERE user_id = ?
        """, (user_id,))
        self.connection.commit()

    def get_admin_statistics(self, user_id):
        """Получить статистику по пользователю."""
        query = """
        SELECT tasks_done, tasks_overdue FROM statistics WHERE user_id = ?
        """
        return self.connection.execute(query, (user_id,)).fetchone()
    
    def get_my_statistics(self, user_id):
        """Получить статистику по пользователю."""
        query = """
        SELECT tasks_done, tasks_overdue FROM statistics WHERE user_id = ?
        """
        return self.connection.execute(query, (user_id,)).fetchone()

    def initialize_statistics(self, user_id):
        """Инициализация статистики для нового пользователя."""
        self.connection.execute("""
        INSERT OR IGNORE INTO statistics (user_id) VALUES (?)
        """, (user_id,))
        self.connection.commit()

    def get_user_by_id(self, user_id):
        """
        Получить пользователя по user_id.
        :param user_id: ID пользователя.
        :return: Словарь с данными пользователя или None, если не найден.
        """
        query = "SELECT * FROM users WHERE user_id = ?"
        user = self.connection.execute(query, (user_id,)).fetchone()
        if user:
            return {
                "id": user[0],  # ID пользователя (внутренний автоинкремент)
                "user_id": user[1],  # Telegram ID пользователя
                "username": user[2],  # Username пользователя
                "name": user[3],  # Полное имя пользователя
                "phone_number": user[4],  # Номер телефона пользователя
                "birth_date": user[5],  # Дата рождения пользователя
                "role": user[6]  # Роль пользователя (admin или executor)
            }
        return None
    
    def delete_task(self, task_id):
        """
        Удаляет задачу из базы данных.
        :param task_id: ID задачи.
        """
        query = "DELETE FROM tasks WHERE id = ?"
        self.connection.execute(query, (task_id,))
        self.connection.commit()

    # Добавляем метод для обновления комментариев:
    def update_task_comments(self, task_id, comment):
        """Добавляет комментарий к задаче."""
        task = self.get_task_by_id(task_id)
        if task:
            old_comments = task['comments'] if task['comments'] != '_' else ''
            new_comments = f"{old_comments}\n{comment}" if old_comments else comment
            self.cursor.execute("""
            UPDATE tasks SET comments = ? WHERE id = ?
            """, (new_comments, task_id))
            self.connection.commit()

    def get_total_tasks_count(self):
        """Возвращает общее количество задач."""
        self.cursor.execute("SELECT COUNT(*) FROM tasks")
        return self.cursor.fetchone()[0]

    def get_tasks_count_by_status(self, status):
        """Возвращает количество задач с определенным статусом."""
        self.cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = ?", (status,))
        return self.cursor.fetchone()[0]

    def get_user_tasks_count(self, user_id):
        """Возвращает количество задач, назначенных на пользователя."""
        self.cursor.execute("SELECT COUNT(*) FROM tasks WHERE assigned_to LIKE ?", (f"%{user_id}%",))
        return self.cursor.fetchone()[0]

    def get_user_tasks_count_by_status(self, user_id, status):
        """Возвращает количество задач пользователя с определенным статусом."""
        self.cursor.execute("SELECT COUNT(*) FROM tasks WHERE assigned_to LIKE ? AND status = ?", (f"%{user_id}%", status))
        return self.cursor.fetchone()[0]

    def get_all_users_count(self):
        """Возвращает общее количество пользователей."""
        self.cursor.execute("SELECT COUNT(*) FROM users")
        return self.cursor.fetchone()[0]

    def get_users_count_by_role(self, role):
        """Возвращает количество пользователей с определенной ролью."""
        self.cursor.execute("SELECT COUNT(*) FROM users WHERE role = ?", (role,))
        return self.cursor.fetchone()[0]
    
    def update_task_deadline(self, task_id, new_deadline):
        """Обновляет дедлайн задачи."""
        timestamp = int(time.mktime(datetime.strptime(new_deadline, "%d-%m-%Y %H:%M").timetuple()))
        self.cursor.execute("UPDATE tasks SET deadline = ? WHERE id = ?", (timestamp, task_id))
        self.connection.commit()