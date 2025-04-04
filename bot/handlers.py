    import logging
    from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
    from telegram.ext import (
        ContextTypes,
        CommandHandler,
        MessageHandler,
        filters,
        Application
    )

    # --- ДАННЫЕ (ЗАПОЛНИ ЭТО) ---
    # Словарь категорий и товаров: { "Категория": ["Товар1", "Товар2"], ... }
    CATEGORIES = {
        "🍕 Пицца": ["Маргарита", "Пепперони", "Четыре сыра", "Гавайская"],
        "🥤 Напитки": ["Кола", "Спрайт", "Вода", "Сок апельсиновый"],
        "🍰 Десерты": ["Чизкейк", "Тирамису", "Мороженое"]
        # Добавь сюда свои категории и товары
    }

    # Приветственное сообщение (НЕ МЕНЯЕТСЯ при выборе категории)
    # Добавь сюда всю нужную информацию (описание, цены и т.д.)
    WELCOME_MESSAGE = """
    Здравствуйте! 👋 
    Здесь ваше полное приветственное сообщение со всей информацией,
    включая описание категорий, товаров, возможно, цен и условий.

    Выберите категорию ниже, чтобы увидеть список товаров, или нажмите 'Оплата'.
    """

    # Информация об оплате
    PAYMENT_INFO = """
    **Информация об оплате:**

    Здесь будет подробная информация о способах и условиях оплаты.
    Пожалуйста, заполни этот раздел.
    """ # <-- ЗАПОЛНИ ЭТОТ ТЕКСТ

    # --- Генераторы Клавиатур ---

    def create_main_keyboard() -> ReplyKeyboardMarkup:
        """Создает главную клавиатуру с категориями и кнопкой Оплата."""
        keyboard_buttons = []
        category_names = list(CATEGORIES.keys())
        # По 2 кнопки категорий в ряд
        for i in range(0, len(category_names), 2):
            row = [KeyboardButton(text=name) for name in category_names[i:i+2]]
            keyboard_buttons.append(row)
        # Кнопка Оплата в последнем ряду
        keyboard_buttons.append([KeyboardButton(text="Оплата")])
        return ReplyKeyboardMarkup(
            keyboard_buttons,
            resize_keyboard=True,
            input_field_placeholder="Выберите категорию..."
        )

    def create_product_keyboard(category_name: str) -> ReplyKeyboardMarkup | None:
        """Создает клавиатуру с товарами для выбранной категории и кнопкой Назад."""
        if category_name not in CATEGORIES:
            return None # На случай ошибки

        items = CATEGORIES[category_name]
        keyboard_buttons = []
        # По 2 кнопки товаров в ряд
        for i in range(0, len(items), 2):
            row = [KeyboardButton(text=item) for item in items[i:i+2]]
            keyboard_buttons.append(row)
        # Кнопка Назад в последнем ряду
        keyboard_buttons.append([KeyboardButton(text="< Назад")])
        return ReplyKeyboardMarkup(
            keyboard_buttons,
            resize_keyboard=True,
            input_field_placeholder=f"Товары в '{category_name}'..."
        )

    # --- Обработчики ---

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Отправляет приветственное сообщение и главную клавиатуру."""
        user = update.effective_user
        logging.info(f"User {user.id} ({user.username}) started the bot.")
        await update.message.reply_text(
            WELCOME_MESSAGE,
            reply_markup=create_main_keyboard()
        )

    async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """При выборе категории меняет клавиатуру на список товаров и кнопку Назад."""
        category_name = update.message.text
        user = update.effective_user
        logging.info(f"User {user.id} selected category: {category_name}")

        product_keyboard = create_product_keyboard(category_name)
        if product_keyboard:
            # Отправляем только новую клавиатуру, без основного текста
            # Можно добавить короткий текст, если нужно: text=f"Выбрана категория: {category_name}"
            await update.message.reply_text(
                text=f"Товары в категории '{category_name}':", # Короткое сообщение
                reply_markup=product_keyboard
            )
        else:
            logging.warning(f"Category '{category_name}' not found for user {user.id}.")
            # Можно отправить сообщение об ошибке или вернуть на главный экран
            await update.message.reply_text(
                "Ошибка: Категория не найдена. Возврат в главное меню.",
                reply_markup=create_main_keyboard()
            )


    async def handle_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает нажатие на кнопку товара (пока просто логирует)."""
        product_name = update.message.text
        user = update.effective_user
        logging.info(f"User {user.id} selected product: {product_name}")
        # TODO: Добавить логику обработки выбора товара (например, добавление в корзину)
        # Пока просто оставляем клавиатуру с товарами
        await update.message.reply_text(f"Вы выбрали: {product_name}. (логика заказа пока не добавлена)")


    async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Возвращает пользователя к главной клавиатуре с категориями."""
        user = update.effective_user
        logging.info(f"User {user.id} returned to main menu.")
        # Отправляем только главную клавиатуру, без основного текста
        # Можно добавить короткий текст: text="Главное меню"
        await update.message.reply_text(
            text="Главное меню:", # Короткое сообщение
            reply_markup=create_main_keyboard()
        )

    async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Отправляет информацию об оплате."""
        user = update.effective_user
        logging.info(f"User {user.id} requested payment info.")
        # Отправляем сообщение об оплате. Клавиатура остается той, что была (главная).
        await update.message.reply_text(PAYMENT_INFO, parse_mode='Markdown')

    # --- Настройка Обработчиков ---

    def setup_handlers(application: Application) -> None:
        """Добавляет все обработчики в приложение."""

        # Получаем список всех возможных названий товаров для фильтра
        all_product_names = [
            item for sublist in CATEGORIES.values() for item in sublist
        ]

        # Важен порядок добавления: специфичные фильтры идут раньше общих
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^Оплата$') & ~filters.COMMAND, handle_payment))
        application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^< Назад$') & ~filters.COMMAND, handle_back))

        # Обработчик категорий (текст должен быть ключом в CATEGORIES)
        application.add_handler(MessageHandler(filters.TEXT & filters.In(CATEGORIES.keys()) & ~filters.COMMAND, handle_category))

        # Обработчик товаров (текст должен быть одним из названий товаров)
        if all_product_names: # Добавляем обработчик только если есть товары
             application.add_handler(MessageHandler(filters.TEXT & filters.In(all_product_names) & ~filters.COMMAND, handle_product))

        # (Опционально) Обработчик для любых других текстовых сообщений
        # async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
        #     await update.message.reply_text("Пожалуйста, используйте кнопки.")
        # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown))
        
        logging.info("Handlers configured successfully.")