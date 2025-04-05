import logging
import os
from telegram.ext import Application
from handlers import setup_handlers
from database.models import init_database
from config import BOT_TOKEN

def main():
    os.makedirs('logs', exist_ok=True)

    # Настройка логирования
    logging.basicConfig(
        filename='logs/bot.log',
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        encoding='utf-8' # Важно для кириллицы в логах
    )
    logging.getLogger("httpx").setLevel(logging.WARNING) # Убрать лишние логи от http клиента

    # Инициализация базы данных
    init_database()

    # Проверка токена
    if not BOT_TOKEN or BOT_TOKEN == 'YOUR_BOT_TOKEN': # Замени YOUR_BOT_TOKEN, если используешь его как плейсхолдер
        logging.error("Токен бота не установлен! Укажите BOT_TOKEN в config.py.")
        print("Ошибка: Токен бота не установлен! Укажите BOT_TOKEN в config.py.")
        return

    # Запуск бота
    application = Application.builder().token(BOT_TOKEN).build()

    # Установка обработчиков из handlers.py
    setup_handlers(application)

    # Запуск бота
    logging.info("Запуск polling...")
    print("Бот запускается...")
    # Убираем callback_query, если не используется
    application.run_polling(allowed_updates=["message"])

    logging.info("Бот остановлен.")
    print("Бот остановлен.")

if __name__ == '__main__':
    main()