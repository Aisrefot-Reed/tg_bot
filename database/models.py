import sqlite3
import logging
from datetime import datetime
from config import DATABASE_PATH # Импортируем путь из конфига

def init_database():
    """Инициализирует базу данных и создает таблицу заказов, если её нет."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                base_work TEXT,
                character_format TEXT,
                extras TEXT, -- Храним как строку, разделенную запятыми
                status TEXT DEFAULT 'new',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        logging.info("База данных инициализирована успешно.")
    except sqlite3.Error as e:
        logging.error(f"Ошибка при инициализации БД: {e}")
    finally:
        if conn:
            conn.close()

def add_order(user_id: int, username: str | None, base_work: str, character_format: str, extras_list: list[str]) -> int | None:
    """Добавляет новый заказ в базу данных и возвращает его ID."""
    extras_str = ", ".join(extras_list) if extras_list else ""
    query = '''
        INSERT INTO orders (user_id, username, base_work, character_format, extras)
        VALUES (?, ?, ?, ?, ?)
    '''
    conn = None
    order_id = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(query, (user_id, username, base_work, character_format, extras_str))
        conn.commit()
        order_id = cursor.lastrowid # Получаем ID вставленной записи
        logging.info(f"Заказ {order_id} от user_id {user_id} добавлен в БД.")
        return order_id
    except sqlite3.Error as e:
        logging.error(f"Ошибка при добавлении заказа для user_id {user_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

# Добавь другие функции, если нужно (например, для получения заказов)