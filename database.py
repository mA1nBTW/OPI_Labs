import sqlite3
import threading
import os
from datetime import datetime

# 1. Hardcoded Configuration: Використання os.getenv замість Magic String
DEFAULT_DB_PATH = os.getenv("DB_PATH", "garden.db")

class LocalDatabase:
    """Обгортка над SQLite для проєкту Garden з потокобезпечними з'єднаннями."""

    def __init__(self, db_path: str = None):
        """Ініціалізує з'єднання з базою даних та створює схему, якщо вона відсутня."""
        # Беремо шлях з аргументу, змінної середовища або використовуємо дефолтний
        self.db_path = db_path or DEFAULT_DB_PATH
        self._local = threading.local()
        self._init_db()

    @property
    def conn(self):
        """Повертає потокобезпечне з'єднання з базою даних."""
        if getattr(self._local, 'conn', None) is None:
            c = sqlite3.connect(self.db_path)
            # Вмикаємо підтримку зовнішніх ключів SQLite (важливо для каскадного видалення)
            c.execute("PRAGMA foreign_keys = ON")
            c.row_factory = sqlite3.Row
            self._local.conn = c
        return self._local.conn

    # ==========================================
    # 2. Resource Leak: Додано метод close() та підтримку контекстного менеджера
    # ==========================================
    def close(self) -> None:
        """Закриває з'єднання з БД для поточного потоку."""
        if getattr(self._local, 'conn', None) is not None:
            self._local.conn.close()
            self._local.conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _init_db(self) -> None:
        """Ініціалізація бази даних: створення таблиць та індексів."""
        # 3. Error Handling / Transaction Management: використання with self.conn (авто-commit/rollback)
        with self.conn:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    email TEXT UNIQUE,
                    password_hash TEXT
                );
                
                CREATE TABLE IF NOT EXISTS contacts (
                    contact_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    name TEXT,
                    reminder_frequency_days INTEGER,
                    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
                
                CREATE TABLE IF NOT EXISTS plants (
                    plant_id TEXT PRIMARY KEY,
                    contact_id TEXT UNIQUE,
                    growth_level INTEGER DEFAULT 1,
                    FOREIGN KEY(contact_id) REFERENCES contacts(contact_id) ON DELETE CASCADE
                );
                
                CREATE TABLE IF NOT EXISTS interactions (
                    interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_id TEXT,
                    media_path TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(contact_id) REFERENCES contacts(contact_id) ON DELETE CASCADE
                );
                
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_id TEXT,
                    sender TEXT,
                    content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(contact_id) REFERENCES contacts(contact_id) ON DELETE CASCADE
                );

                -- 4. Performance: Створення індексів для зовнішніх ключів (оптимізація JOIN)
                CREATE INDEX IF NOT EXISTS idx_contacts_user_id ON contacts(user_id);
                CREATE INDEX IF NOT EXISTS idx_plants_contact_id ON plants(contact_id);
                CREATE INDEX IF NOT EXISTS idx_interactions_contact_id ON interactions(contact_id);
                CREATE INDEX IF NOT EXISTS idx_messages_contact_id ON messages(contact_id);
            """)

    # ==========================================
    # 5. Maintainability / Documentation: Додано docstrings до всіх публічних методів
    # ==========================================

    def insert_user(self, user_id: str, email: str, password_hash: str) -> None:
        """
        Додає нового користувача до бази даних.

        :param user_id: Унікальний ідентифікатор користувача.
        :param email: Електронна пошта.
        :param password_hash: Хешований пароль.
        """
        with self.conn:
            self.conn.execute(
                "INSERT INTO users (user_id, email, password_hash) VALUES (?, ?, ?)",
                (user_id, email, password_hash)
            )

    def get_user_by_email(self, email: str) -> dict:
        """
        Шукає користувача за електронною поштою.

        :param email: Електронна пошта для пошуку.
        :return: Словник з даними користувача або None, якщо не знайдено.
        """
        cur = self.conn.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        return dict(row) if row else None

    def insert_contact(self, user_id: str, contact) -> None:
        """
        Додає новий контакт, прив'язаний до користувача.

        :param user_id: Ідентифікатор користувача, якому належить контакт.
        :param contact: Об'єкт контакту з атрибутами contact_id, name, reminder_frequency_days.
        """
        with self.conn:
            self.conn.execute(
                "INSERT INTO contacts (contact_id, user_id, name, reminder_frequency_days) VALUES (?, ?, ?, ?)",
                (contact.contact_id, user_id, contact.name, contact.reminder_frequency_days)
            )

    def get_contacts(self, user_id: str) -> list:
        """
        Повертає список всіх контактів певного користувача.

        :param user_id: Ідентифікатор користувача.
        :return: Список словників з інформацією про контакти.
        """
        cur = self.conn.execute("SELECT * FROM contacts WHERE user_id = ?", (user_id,))
        return [dict(row) for row in cur.fetchall()]

    def update_contact(self, contact_id: str, name: str, reminder_frequency_days: int) -> None:
        """
        Оновлює інформацію про існуючий контакт.

        :param contact_id: Унікальний ідентифікатор контакту.
        :param name: Нове ім'я контакту.
        :param reminder_frequency_days: Нова частота нагадувань у днях.
        """
        with self.conn:
            self.conn.execute(
                "UPDATE contacts SET name = ?, reminder_frequency_days = ? WHERE contact_id = ?",
                (name, reminder_frequency_days, contact_id)
            )

    def delete_contact(self, contact_id: str) -> None:
        """
        Видаляє контакт із бази даних (рослина та повідомлення видаляються каскадно).

        :param contact_id: Унікальний ідентифікатор контакту.
        """
        with self.conn:
            self.conn.execute("DELETE FROM contacts WHERE contact_id = ?", (contact_id,))

    def insert_plant(self, plant) -> None:
        """
        Створює віртуальну рослину для вказаного контакту.

        :param plant: Об'єкт рослини з атрибутами plant_id, contact_id, growth_level.
        """
        with self.conn:
            self.conn.execute(
                "INSERT INTO plants (plant_id, contact_id, growth_level) VALUES (?, ?, ?)",
                (plant.plant_id, plant.contact_id, plant.growth_level)
            )

    def get_all_plants(self, user_id: str) -> list:
        """
        Отримує всі рослини, що належать контактам конкретного користувача.

        :param user_id: Ідентифікатор користувача.
        :return: Список словників з даними про рослини.
        """
        query = """
            SELECT p.* FROM plants p
            JOIN contacts c ON p.contact_id = c.contact_id
            WHERE c.user_id = ?
        """
        cur = self.conn.execute(query, (user_id,))
        return [dict(row) for row in cur.fetchall()]

    def get_plant(self, contact_id: str) -> dict:
        """
        Повертає рослину, прив'язану до певного контакту.

        :param contact_id: Ідентифікатор контакту.
        :return: Словник з даними про рослину або None.
        """
        cur = self.conn.execute("SELECT * FROM plants WHERE contact_id = ?", (contact_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def update_plant_state(self, plant) -> None:
        """
        Оновлює рівень росту рослини.

        :param plant: Об'єкт рослини з актуальним growth_level.
        """
        with self.conn:
            self.conn.execute(
                "UPDATE plants SET growth_level = ? WHERE plant_id = ?",
                (plant.growth_level, plant.plant_id)
            )

    def add_interaction(self, contact_id: str, media_path: str = None) -> None:
        """
        Зберігає запис про взаємодію з контактом (повідомлення, фото).

        :param contact_id: Ідентифікатор контакту.
        :param media_path: Шлях до збереженого медіафайлу (опціонально).
        """
        with self.conn:
            self.conn.execute(
                "INSERT INTO interactions (contact_id, media_path, timestamp) VALUES (?, ?, ?)",
                (contact_id, media_path, datetime.now().isoformat())
            )

    def get_interactions(self, contact_id: str) -> list:
        """
        Отримує історію всіх взаємодій з контактом.

        :param contact_id: Ідентифікатор контакту.
        :return: Список словників взаємодій, відсортований від найновіших до найстаріших.
        """
        cur = self.conn.execute(
            "SELECT * FROM interactions WHERE contact_id = ? ORDER BY timestamp DESC", 
            (contact_id,)
        )
        return [dict(row) for row in cur.fetchall()]

    def insert_message(self, contact_id: str, sender: str, content: str) -> dict:
        """
        Зберігає повідомлення чату.

        :param contact_id: Ідентифікатор контакту.
        :param sender: Відправник ('user' або ім'я контакту).
        :param content: Текст повідомлення.
        :return: Словник зі збереженим повідомленням (включаючи згенерований ID).
        """
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO messages (contact_id, sender, content, timestamp) VALUES (?, ?, ?, ?)",
                (contact_id, sender, content, datetime.now().isoformat())
            )
            msg_id = cur.lastrowid
            
        # Повертаємо збережене повідомлення
        return dict(self.conn.execute("SELECT * FROM messages WHERE message_id = ?", (msg_id,)).fetchone())

    def get_messages(self, contact_id: str) -> list:
        """
        Отримує історію повідомлень для конкретного контакту.

        :param contact_id: Ідентифікатор контакту.
        :return: Список словників повідомлень, відсортований за часом.
        """
        cur = self.conn.execute(
            "SELECT * FROM messages WHERE contact_id = ? ORDER BY timestamp ASC",
            (contact_id,)
        )
        return [dict(row) for row in cur.fetchall()]