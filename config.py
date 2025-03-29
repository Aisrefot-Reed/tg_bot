# Конфигурационные параметры бота

# Токен бота от BotFather
BOT_TOKEN = '7728251431:AAEZ3y5HDcNk7nto1IcHu6rsteCr1vMnd38'

# ID художника для получения заказов
ARTIST_CHAT_ID = 'TELEGRAM_ARTIST_ID'

# Настройки категорий и цен
PICTURE_CATEGORIES = {
    "Портрет": 2000,
    "Пейзаж": 1500,
    "Абстракция": 1000,
    "Фентези": 2500
}

# Способы оплаты
PAYMENT_METHODS = [
    "Сбербанк", 
    "Тинькофф", 
    "Яндекс.Деньги", 
    "PayPal"
]

# Настройки базы данных
DATABASE_PATH = 'artist_orders.db'