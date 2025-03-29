import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ConversationHandler, CallbackContext
)
from config import PICTURE_CATEGORIES, PAYMENT_METHODS, ARTIST_CHAT_ID
from database.models import save_order

# Состояния для машины состояний
START, CATEGORY_SELECTION, PAYMENT_METHOD, NAME_INPUT, CONFIRMATION = range(5)

async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        "👋 Привет! Я бот для заказа художественных работ. "
        "Давайте начнем процесс заказа!\n\n"
        "Выберите категорию рисунка:",
        reply_markup=ReplyKeyboardMarkup(
            [[category] for category in PICTURE_CATEGORIES.keys()], 
            one_time_keyboard=True
        )
    )
    return CATEGORY_SELECTION

# Другие обработчики (select_category, select_payment_method и т.д.)

def setup_handlers(application: Application):
    # Настройка ConversationHandler с машиной состояний
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CATEGORY_SELECTION: [
                MessageHandler(filters.Text(PICTURE_CATEGORIES.keys()), select_category)
            ],
            # Другие состояния
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    application.add_handler(conv_handler)