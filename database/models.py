import sqlite3
from config import DATABASE_PATH

def init_database():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            category TEXT,
            payment_method TEXT,
            customer_name TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')
    conn.commit()
    conn.close()

def save_order(user_data: dict):
    """Сохранение заказа в базу данных"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO orders 
        (user_id, username, category, payment_method, customer_name) 
        VALUES (?, ?, ?, ?, ?)
    ''', (
        user_data['user_id'], 
        user_data['username'], 
        user_data['category'], 
        user_data['payment_method'], 
        user_data['customer_name']
    ))
    
    conn.commit()
    order_id = cursor.lastrowid
    conn.close()
    
    return order_id