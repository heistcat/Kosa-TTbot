import os
import sqlite3
import time
from datetime import datetime
os.environ['TZ'] = 'Etc/GMT-5'
time.tzset() # Обновляем информацию о таймзоне

class Database:
    def __init__(self, db_path="database/database.db"):
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
            status TEXT DEFAULT 'новая',
            report_text TEXT DEFAULT '_',
            report_photo TEXT DEFAULT '_',
            comments TEXT DEFAULT '_',
            created_by INTEGER,
            FOREIGN KEY (assigned_to) REFERENCES users(user_id)
        )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS su (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            timestamp INTEGER,
            user_id TEXT,
            action TEXT,
            details TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE,
            score INTEGER DEFAULT 0,
            last_update INTEGER
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS score_tariffs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tariff_name TEXT UNIQUE,
            time_threshold INTEGER,
            score INTEGER
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            user_id TEXT,
            deadline INTEGER,
            notification_type TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
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
    
    def get_all_sus(self):
        query = "SELECT * FROM su"
        return self.connection.execute(query).fetchall()
    
    def remove_su(self, user_id):
        self.cursor.execute("DELETE FROM su WHERE user_id = ?", (user_id,))
        self.connection.commit()

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

    def get_user_by_phone_number(self, phone_number):
        """Получение информации о пользователе по ID."""
        query = "SELECT * FROM users WHERE phone_number = ?"
        return self.connection.execute(query, (phone_number,)).fetchone()

    def get_all_users(self):
        """Получение всех пользователей."""
        query = "SELECT * FROM users"
        return self.connection.execute(query).fetchall()

    def get_all_executors(self):
        """Получение всех исполнителей (executor)."""
        query = "SELECT * FROM users WHERE role = 'Исполнитель'"
        return self.connection.execute(query).fetchall()

    # --- Методы для работы с задачами ---
    def create_task(self, title, description, ref_photo, deadline, deadline_formatted, assigned_to, report_text, report_photo, location, created_by):
        """Создание задачи."""
        timestamp = int(time.mktime(datetime.strptime(deadline, "%d-%m-%Y %H:%M").timetuple()))
        self.connection.execute("""
        INSERT INTO tasks (title, description, ref_photo, deadline, deadline_formatted, assigned_to, report_text, report_photo, location, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, description, ref_photo, timestamp, deadline_formatted, assigned_to, report_text, report_photo, location, created_by))
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
    
    def get_task_by_title(self, task_id):
        """Получение задачи по ID."""
        query = """
        SELECT *, strftime('%d-%m-%Y %H:%M', deadline, 'unixepoch') AS deadline_formatted
        FROM tasks WHERE title = ?
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
        UPDATE tasks SET report_text = ?, report_photo = ?, status = 'выполнено' WHERE id = ?
        """, (report_text, report_photo, task_id))
        self.connection.commit()

    def get_all_tasks(self):
        """Получение всех задач."""
        query = """
        SELECT *, strftime('%d-%m-%Y %H:%M', deadline, 'unixepoch') AS deadline_formatted FROM tasks ORDER BY deadline ASC
        """
        return self.connection.execute(query).fetchall()


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
        # timestamp = int(time.mktime(datetime.strptime(new_deadline, "%d-%m-%Y %H:%M").timetuple()))
        timestamp = int(new_deadline)
        self.cursor.execute("UPDATE tasks SET deadline = ? WHERE id = ?", (timestamp, task_id))
        self.connection.commit()

    def add_task_history_entry(self, task_id, user_id, action, details):
        """Добавляет запись в историю изменений задачи."""
        timestamp = int(time.time())
        self.cursor.execute("""
            INSERT INTO task_history (task_id, timestamp, user_id, action, details)
            VALUES (?, ?, ?, ?, ?)
        """, (task_id, timestamp, user_id, action, details))
        self.connection.commit()

    def get_task_history(self, task_id):
        """Получает историю изменений задачи."""
        query = """
            SELECT timestamp, user_id, action, details
            FROM task_history
            WHERE task_id = ?
            ORDER BY timestamp ASC
        """
        return self.connection.execute(query, (task_id,)).fetchall()
    
    def get_user_score(self, user_id):
        """Получает баллы пользователя."""
        query = "SELECT score FROM user_scores WHERE user_id = ?"
        result = self.connection.execute(query, (user_id,)).fetchone()
        if result:
            return result['score']
        return 0
    
    def get_all_done_tasks(self, status):
        """Получение всех задач с определенным статусом."""
        query = """
            SELECT *, strftime('%d-%m-%Y %H:%M', deadline, 'unixepoch') AS deadline_formatted
            FROM tasks
            WHERE status = 'done'
            ORDER BY deadline ASC
        """
        return self.connection.execute(query, (status,)).fetchall()
    
    def get_all_completed_tasks(self, status):
        """Получение всех задач с определенным статусом."""
        query = """
            SELECT *, strftime('%d-%m-%Y %H:%M', deadline, 'unixepoch') AS deadline_formatted
            FROM tasks
            WHERE status = 'completed'
            ORDER BY deadline ASC
        """
        return self.connection.execute(query, (status,)).fetchall()
        

    def add_user_score(self, user_id, score):
        """Начисляет баллы пользователю."""
        timestamp = int(time.time())
        self.cursor.execute("""
            INSERT INTO user_scores (user_id, score, last_update)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET score = score + ?, last_update = ?
        """, (user_id, score, timestamp, score, timestamp))
        self.connection.commit()

    def remove_user_score(self, user_id, score):
        """Снимает баллы у пользователя."""
        timestamp = int(time.time())
        self.cursor.execute("""
            INSERT INTO user_scores (user_id, score, last_update)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET score = score - ?, last_update = ?
        """, (user_id, score, timestamp, score, timestamp))
        self.connection.commit()

    def reset_all_scores(self):
        """Обнуляет баллы всех пользователей."""
        timestamp = int(time.time())
        self.cursor.execute("UPDATE user_scores SET score = 0, last_update = ?", (timestamp,))
        self.connection.commit()

    def get_tariff(self, tariff_name):
        """Получает тариф по имени."""
        query = "SELECT time_threshold, score FROM score_tariffs WHERE tariff_name = ?"
        result = self.connection.execute(query, (tariff_name,)).fetchone()
        if result:
            return result
        return None

    def get_all_tariffs(self):
        """Получает все тарифы."""
        query = "SELECT * FROM score_tariffs"
        return self.connection.execute(query).fetchall()

    def update_tariff(self, tariff_name, time_threshold, score):
        """Обновляет тариф."""
        self.cursor.execute("""
            INSERT INTO score_tariffs (tariff_name, time_threshold, score)
            VALUES (?, ?, ?)
            ON CONFLICT(tariff_name) DO UPDATE SET time_threshold = ?, score = ?
        """, (tariff_name, time_threshold, score, time_threshold, score))
        self.connection.commit()

    def create_tariff(self, tariff_name, time_threshold, score):
        """Создает новый тариф."""
        self.cursor.execute("""
            INSERT INTO score_tariffs (tariff_name, time_threshold, score)
            VALUES (?, ?, ?)
        """, (tariff_name, time_threshold, score))
        self.connection.commit()

    def delete_tariff(self, tariff_name):
        """Удаляет тариф."""
        self.cursor.execute("DELETE FROM score_tariffs WHERE tariff_name = ?", (tariff_name,))
        self.connection.commit()

    def add_task_notification(self, task_id, user_id, deadline, notification_type):
        """Добавляет запись об отправленном уведомлении."""
        self.cursor.execute("""
            INSERT INTO task_notifications (task_id, user_id, deadline, notification_type)
            VALUES (?, ?, ?, ?)
        """, (task_id, user_id, deadline, notification_type))
        self.connection.commit()

    def check_task_notification(self, task_id, user_id, deadline, notification_type):
        """Проверяет, было ли уже отправлено уведомление для данного дедлайна."""
        query = """
            SELECT id FROM task_notifications
            WHERE task_id = ? AND user_id = ? AND deadline = ? AND notification_type = ?
        """
        result = self.connection.execute(query, (task_id, user_id, deadline, notification_type)).fetchone()
        return bool(result)

    def delete_task_notifications(self, task_id):
        """Удаляет все уведомления для задачи."""
        self.cursor.execute("DELETE FROM task_notifications WHERE task_id = ?", (task_id,))
        self.connection.commit()