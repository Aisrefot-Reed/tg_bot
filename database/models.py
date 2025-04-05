
import sqlite3
import logging
from config import DATABASE_PATH

def init_database():
    """Инициализирует базу данных и создает необходимые таблицы."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Создаем таблицу заказов
        cursor.execute('DROP TABLE IF EXISTS orders')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                base_work TEXT NOT NULL,
                character_format TEXT NOT NULL,
                extras TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        logging.info("База данных успешно инициализирована")
        
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
        logging.error(f"Ошибка при добавлении заказа в БД: {e}")
        return None
    finally:
        if conn:
            conn.close()
