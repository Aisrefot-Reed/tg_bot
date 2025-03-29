import logging
from telegram.ext import Application, Update
from bot.handlers import setup_handlers
from database.models import init_database
from config import BOT_TOKEN

def main():
    # Инициализация базы данных
    init_database()
    
    # Настройка логирования
    logging.basicConfig(
        filename='logs/bot.log', 
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Запуск бота
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Установка обработчиков
    setup_handlers(application)
    
    # Запуск бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()