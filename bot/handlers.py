import logging
import re
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, User
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    Application,
    ConversationHandler
)
from telegram.helpers import escape_markdown # Для экранирования тега пользователя

# Импортируем необходимые данные и функции
from config import ARTIST_CHAT_ID
from database.models import add_order # Импортируем функцию добавления заказа

# --- ДАННЫЕ ---
CATEGORIES = {
    "Базовые работы": ["Скетч", "Лайнарт", "Шейд", "Рендер"],
    "Форматы персонажей": ["Портрет", "Халфбоди", "Фуллбоди", "Чиби"],
    "Доп. услуги": ["Сложный фон", "Дополнительный персонаж", "Срочный заказ"]
}

# Сообщения остаются те же
WELCOME_MESSAGE = """
📝 *ПРАЙС-ЛИСТ НА ЗАКАЗЫ*

📋 *Базовые работы*

_Скетч ............................ от 500₽_
_Лайнарт .......................... от 600₽_
_Шейд (с тенями и бликами) ........ от 700₽_
_Рендер (детализированная) ........ от 800₽_

👤 *Форматы персонажей*

_Портрет (по плечи) ............... от 650₽_
_Халфбоди (по пояс/до бёдер) ...... от 750₽_
_Фуллбоди (в полный рост) ......... от 850₽_
_Чиби (упрощённый стиль) .......... от 500₽_

🔍 *Дополнительные услуги*

_Сложный фон ...................... + 300₽_
_Дополнительный персонаж .......... + 350₽_
_Срочный заказ .................... + 300₽_

💰 *Условия оплаты*

_• Оплата делится 50/50_
_• Начальный взнос (50%) - на этапе скетча_
_• Остаток (50%) - после завершения работы_

`Убедительная просьба перед оформленим заказа ознакомиться с комиссией,        чтобы перекрыть её и оплатить нужную стоимость.`

⏱️ *Дедлайн*

_• Срок зависит от сложности работы_
_• В среднем: от 1 до 2 недель_

Выберите категорию ниже или нажмите 'Оплата', чтобы увидеть СПОСОБЫ оплаты:
"""
PAYMENT_INFO = """
💳 **Способы оплаты:**
... (твои способы оплаты) ...
"""

# --- Состояния для ConversationHandler ---
SELECTING_BASE, SELECTING_FORMAT, SELECTING_EXTRAS, CONFIRMATION = range(4)
# Отдельное состояние для тех, кто сразу нажал "Доп. услуги" (не лучший путь)
# SELECTING_ONLY_EXTRAS = range(4, 5) # Пока не будем реализовывать

# --- Клавиатуры ---
# (create_main_keyboard остается как есть)
def create_main_keyboard() -> ReplyKeyboardMarkup:
    keyboard_buttons = []
    category_names = list(CATEGORIES.keys())
    num_categories = len(category_names)
    rows = (num_categories + 1) // 2
    idx = 0
    for _ in range(rows):
        row_buttons = []
        for _ in range(2):
            if idx < num_categories:
                row_buttons.append(KeyboardButton(text=category_names[idx]))
                idx += 1
        if row_buttons:
            keyboard_buttons.append(row_buttons)
    keyboard_buttons.append([KeyboardButton(text="Оплата")])
    return ReplyKeyboardMarkup(keyboard_buttons, resize_keyboard=True, input_field_placeholder="Выберите категорию или Оплату...")

# Клавиатура для выбора базовой работы
def create_base_work_keyboard() -> ReplyKeyboardMarkup:
    items = CATEGORIES["Базовые работы"]
    keyboard = [[KeyboardButton(text=item) for item in items[i:i+2]] for i in range(0, len(items), 2)]
    keyboard.append([KeyboardButton(text="Отмена")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Выберите базовую работу...")

# Клавиатура для выбора формата
def create_format_keyboard() -> ReplyKeyboardMarkup:
    items = CATEGORIES["Форматы персонажей"]
    keyboard = [[KeyboardButton(text=item) for item in items[i:i+2]] for i in range(0, len(items), 2)]
    keyboard.append([KeyboardButton(text="Отмена")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Выберите формат...")

# Клавиатура для выбора доп. услуг
def create_extras_keyboard() -> ReplyKeyboardMarkup:
    items = CATEGORIES["Доп. услуги"]
    keyboard = [[KeyboardButton(text=item) for item in items[i:i+2]] for i in range(0, len(items), 2)]
    # Добавляем кнопки для управления выбором доп. услуг
    keyboard.append([KeyboardButton(text="Готово (без доп. услуг)")])
    keyboard.append([KeyboardButton(text="Завершить выбор допов")]) # Если уже выбрал хотя бы одну
    keyboard.append([KeyboardButton(text="Отмена")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False, input_field_placeholder="Выберите доп. услугу или завершите...")


# --- Функции диалога ---

async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает процесс заказа, запрашивая базовую работу."""
    # Этот хендлер сработает, когда пользователь нажмет кнопку "Базовые работы" или "Форматы персонажей"
    category_name = update.message.text
    user = update.effective_user
    logging.info(f"User {user.id} starts order process selecting '{category_name}'.")

    context.user_data['order'] = {'extras': []} # Инициализируем заказ

    await update.message.reply_text(
        "Отлично! Давайте начнем оформление заказа.\nПожалуйста, выберите *базовую работу*:",
        reply_markup=create_base_work_keyboard(),
        parse_mode='Markdown'
    )
    return SELECTING_BASE

async def select_base_work(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет выбранную базовую работу и запрашивает формат."""
    base_work = update.message.text
    user = update.effective_user
    if base_work not in CATEGORIES["Базовые работы"]:
        await update.message.reply_text("Пожалуйста, выберите один из вариантов на клавиатуре.", reply_markup=create_base_work_keyboard())
        return SELECTING_BASE # Остаемся в том же состоянии

    logging.info(f"User {user.id} selected base work: {base_work}")
    context.user_data['order']['base_work'] = base_work

    await update.message.reply_text(
        f"Выбрано: {base_work}.\nТеперь выберите *формат персонажа*:",
        reply_markup=create_format_keyboard(),
        parse_mode='Markdown'
    )
    return SELECTING_FORMAT

async def select_format(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет выбранный формат и запрашивает доп. услуги."""
    character_format = update.message.text
    user = update.effective_user
    if character_format not in CATEGORIES["Форматы персонажей"]:
        await update.message.reply_text("Пожалуйста, выберите один из вариантов на клавиатуре.", reply_markup=create_format_keyboard())
        return SELECTING_FORMAT

    logging.info(f"User {user.id} selected format: {character_format}")
    context.user_data['order']['format'] = character_format

    await update.message.reply_text(
        f"Выбрано: {character_format}.\nХотите добавить *дополнительные услуги*? Выберите их или нажмите 'Готово'.",
        reply_markup=create_extras_keyboard(),
        parse_mode='Markdown'
    )
    return SELECTING_EXTRAS

async def select_extras(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Добавляет выбранную доп. услугу."""
    extra_service = update.message.text
    user = update.effective_user

    if extra_service in CATEGORIES["Доп. услуги"]:
        if extra_service not in context.user_data['order']['extras']:
            context.user_data['order']['extras'].append(extra_service)
            logging.info(f"User {user.id} added extra: {extra_service}")
            chosen_extras = ", ".join(context.user_data['order']['extras'])
            await update.message.reply_text(
                f"Добавлено: {extra_service}.\nВыбранные доп. услуги: {chosen_extras}.\n\nВыберите еще или нажмите 'Завершить выбор допов'.",
                reply_markup=create_extras_keyboard() # Оставляем ту же клавиатуру
            )
        else:
            await update.message.reply_text(
                f"Услуга '{extra_service}' уже добавлена. Выберите другую или нажмите 'Завершить выбор допов'.",
                reply_markup=create_extras_keyboard()
            )
        return SELECTING_EXTRAS # Остаемся в том же состоянии для выбора новых допов
    else:
        # Если нажали не доп. услугу и не кнопку завершения/отмены
        await update.message.reply_text(
            "Не распознано. Выберите доп. услугу с клавиатуры, 'Готово (без доп. услуг)', 'Завершить выбор допов' или 'Отмена'.",
            reply_markup=create_extras_keyboard()
        )
        return SELECTING_EXTRAS


async def finish_extras(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Завершает выбор доп. услуг и переходит к подтверждению."""
    user = update.effective_user
    action = update.message.text
    logging.info(f"User {user.id} finishing extras selection with action: '{action}'.")

    # Собираем заказ
    order_data = context.user_data.get('order', {})
    base = order_data.get('base_work', 'Не выбрано')
    fmt = order_data.get('format', 'Не выбрано')
    extras = order_data.get('extras', [])
    extras_str = ", ".join(extras) if extras else "Нет"

    # Формируем сообщение для подтверждения (можно пропустить этот шаг и сразу сохранять/отправлять)
    summary = (
        f"Ваш заказ:\n"
        f"- Базовая работа: *{escape_markdown(base)}*\n"
        f"- Формат: *{escape_markdown(fmt)}*\n"
        f"- Доп. услуги: *{escape_markdown(extras_str)}*\n\n"
        f"Всё верно? Отправляем заказ художнику?"
    )
    # Пока пропустим подтверждение и сразу сохраним/отправим
    logging.info(f"Order details for user {user.id}: Base='{base}', Format='{fmt}', Extras='{extras_str}'")

    # 1. Сохраняем в БД
    username = user.username if user.username else user.full_name # Используем имя, если нет @username
    order_id = add_order(user.id, username, base, fmt, extras)

    if order_id:
        # 2. Уведомляем художника
        user_mention = user.mention_markdown_v2() # Получаем тег пользователя
        artist_message = (
            f"🎨 Новый заказ \\! ID: {order_id}\n\n"
            f"*От:* {user_mention} `({escape_markdown(str(user.id))})`\n"
            f"*База:* {escape_markdown(base)}\n"
            f"*Формат:* {escape_markdown(fmt)}\n"
            f"*Доп\\. услуги:* {escape_markdown(extras_str)}"
        )
        try:
            await context.bot.send_message(
                chat_id=ARTIST_CHAT_ID,
                text=artist_message,
                parse_mode='MarkdownV2'
            )
            logging.info(f"Notification for order {order_id} sent to artist {ARTIST_CHAT_ID}.")
            # 3. Уведомляем пользователя
            await update.message.reply_text(
                f"✅ Ваш заказ (ID: {order_id}) успешно создан и отправлен художнику! Ожидайте ответа.",
                reply_markup=create_main_keyboard() # Возвращаем главную клавиатуру
            )
        except Exception as e:
            logging.error(f"Ошибка отправки уведомления художнику для заказа {order_id}: {e}")
            await update.message.reply_text(
                f"✅ Ваш заказ (ID: {order_id}) создан, но произошла ошибка при отправке уведомления художнику. Пожалуйста, свяжитесь с ним напрямую.",
                reply_markup=create_main_keyboard()
            )
    else:
        logging.error(f"Не удалось сохранить заказ в БД для пользователя {user.id}.")
        await update.message.reply_text(
            "❌ Произошла ошибка при сохранении вашего заказа. Пожалуйста, попробуйте еще раз или свяжитесь с поддержкой.",
            reply_markup=create_main_keyboard()
        )

    context.user_data.clear() # Очищаем данные заказа
    return ConversationHandler.END # Завершаем диалог

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет текущий процесс заказа."""
    user = update.effective_user
    logging.info(f"User {user.id} cancelled the order process.")
    context.user_data.clear() # Очищаем данные
    await update.message.reply_text(
        "Оформление заказа отменено.",
        reply_markup=create_main_keyboard() # Возвращаем главную клавиатуру
    )
    return ConversationHandler.END

# --- Обычные обработчики (вне диалога) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение."""
    await update.message.reply_text(
        WELCOME_MESSAGE,
        reply_markup=create_main_keyboard(),
        parse_mode='Markdown'
    )

async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет информацию о способах оплаты."""
    await update.message.reply_text(PAYMENT_INFO, parse_mode='Markdown')

async def handle_other_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает нажатие на 'Доп. услуги' из главного меню (не рекомендуется)."""
    await update.message.reply_text(
        "Чтобы добавить доп. услуги, пожалуйста, начните оформление заказа, выбрав 'Базовые работы'.",
        reply_markup=create_main_keyboard()
    )

# --- Настройка Обработчиков ---

def setup_handlers(application: Application) -> None:
    """Настраивает все обработчики, включая ConversationHandler."""

    # Создаем ConversationHandler для процесса заказа
    order_conv_handler = ConversationHandler(
        entry_points=[
            # Начинаем диалог при выборе категорий для заказа
            MessageHandler(filters.TEXT & filters.Regex(f'^({"|".join(map(re.escape, [k for k in CATEGORIES if k != "Доп. услуги"]))})$') & ~filters.COMMAND, start_order),
        ],
        states={
            SELECTING_BASE: [
                MessageHandler(filters.TEXT & filters.Regex(f'^({"|".join(CATEGORIES["Базовые работы"])})$') & ~filters.COMMAND, select_base_work)
            ],
            SELECTING_FORMAT: [
                MessageHandler(filters.TEXT & filters.In(CATEGORIES["Форматы персонажей"]) & ~filters.COMMAND, select_format)
            ],
            SELECTING_EXTRAS: [
                MessageHandler(filters.TEXT & filters.In(CATEGORIES["Доп. услуги"]) & ~filters.COMMAND, select_extras),
                MessageHandler(filters.TEXT & filters.Regex(r'^(Готово \(без доп\. услуг\)|Завершить выбор допов)$') & ~filters.COMMAND, finish_extras),
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_order),
            MessageHandler(filters.TEXT & filters.Regex('^Отмена$') & ~filters.COMMAND, cancel_order),
            # Можно добавить обработчик для неожиданных сообщений внутри диалога
            # MessageHandler(filters.TEXT & ~filters.COMMAND, unexpected_message_in_conv)
        ],
        # persistent=True, name="order_conversation" # Можно включить персистентность между перезапусками
    )

    # Добавляем обработчики в приложение
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^Оплата$') & ~filters.COMMAND, handle_payment))

    # Добавляем обработчик для нажатия "Доп. услуги" из главного меню
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^Доп\. услуги$') & ~filters.COMMAND, handle_other_categories))

    # Добавляем сам ConversationHandler
    application.add_handler(order_conv_handler)

    # Обработчик для любых других текстовых сообщений (вне диалога) можно добавить последним
    # async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     await update.message.reply_text("Не понимаю вас. Используйте кнопки или команду /start.")
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown))

    logging.info("Handlers configured with ConversationHandler for orders.")