    import logging
    import re
    from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
    from telegram.ext import (
        ContextTypes,
        CommandHandler,
        MessageHandler,
        filters,
        Application
    )

    # --- ДАННЫЕ (ОБНОВЛЕНЫ) ---

    # Словарь категорий и товаров
    CATEGORIES = {
        "Базовые работы": ["Скетч", "Лайнарт", "Шейд", "Рендер"],
        "Форматы персонажей": ["Портрет", "Халфбоди", "Фуллбоди", "Чиби"],
        "Доп. услуги": ["Сложный фон", "Дополнительный персонаж", "Срочный заказ"] # Добавлена категория
    }

    # Приветственное сообщение с прайс-листом и УСЛОВИЯМИ оплаты
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

    # Информация о СПОСОБАХ оплаты (ЗАПОЛНИ ЭТО)
    PAYMENT_INFO = """
    💳 **Способы оплаты:**

    Пожалуйста, укажите здесь, как можно оплатить ваши услуги.
    Например:
    - Перевод на карту Сбербанк (номер ...)
    - Перевод на карту Тинькофф (номер ...)
    - Система быстрых платежей (СБП) по номеру телефона ...
    - (Другие способы, если есть)

    Не забудьте учесть комиссию при переводе!
    """ # <-- ЗАПОЛНИ ЭТОТ ТЕКСТ

    # --- Генераторы Клавиатур ---

    def create_main_keyboard() -> ReplyKeyboardMarkup:
        """Создает главную клавиатуру с категориями и кнопкой Оплата."""
        keyboard_buttons = []
        category_names = list(CATEGORIES.keys()) # Теперь включает "Доп. услуги"
        # Распределяем кнопки категорий по рядам (например, по 2)
        num_categories = len(category_names)
        rows = (num_categories + 1) // 2 # По 2 кнопки в ряд

        idx = 0
        for _ in range(rows):
            row_buttons = []
            for _ in range(2):
                if idx < num_categories:
                    row_buttons.append(KeyboardButton(text=category_names[idx]))
                    idx += 1
            if row_buttons:
                 keyboard_buttons.append(row_buttons)

        # Кнопка "Оплата" всегда в последнем ряду
        keyboard_buttons.append([KeyboardButton(text="Оплата")])
        return ReplyKeyboardMarkup(
            keyboard_buttons,
            resize_keyboard=True,
            input_field_placeholder="Выберите категорию или Оплату..."
        )

    def create_product_keyboard(category_name: str) -> ReplyKeyboardMarkup | None:
        """Создает клавиатуру с товарами/услугами для выбранной категории и кнопкой Назад."""
        if category_name not in CATEGORIES:
            return None

        items = CATEGORIES[category_name]
        keyboard_buttons = []
        # По 2 кнопки товаров/услуг в ряд
        for i in range(0, len(items), 2):
            row = [KeyboardButton(text=item) for item in items[i:i+2]]
            keyboard_buttons.append(row)
        # Кнопка Назад в последнем ряду
        keyboard_buttons.append([KeyboardButton(text="< Назад")])
        return ReplyKeyboardMarkup(
            keyboard_buttons,
            resize_keyboard=True,
            input_field_placeholder=f"Опции в '{category_name}'..."
        )

    # --- Обработчики ---

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Отправляет приветственное сообщение и главную клавиатуру."""
        user = update.effective_user
        logging.info(f"User {user.id} ({user.username}) started the bot.")
        await update.message.reply_text(
            WELCOME_MESSAGE,
            reply_markup=create_main_keyboard(),
            parse_mode='Markdown'
        )

    async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """При выборе категории меняет клавиатуру на список товаров/услуг и кнопку Назад."""
        category_name = update.message.text
        user = update.effective_user
        logging.info(f"User {user.id} selected category: {category_name}")

        product_keyboard = create_product_keyboard(category_name)
        if product_keyboard:
            # Определяем текст в зависимости от категории
            text_prefix = "Виды работ" if category_name in ["Базовые работы", "Форматы персонажей"] else "Доступные опции"
            await update.message.reply_text(
                text=f"{text_prefix} в категории '{category_name}':",
                reply_markup=product_keyboard
            )
        else:
            logging.warning(f"Category '{category_name}' not found for user {user.id}.")
            await update.message.reply_text(
                "Ошибка: Категория не найдена. Возврат в главное меню.",
                reply_markup=create_main_keyboard()
            )

    async def handle_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает нажатие на кнопку товара/услуги (пока просто логирует)."""
        product_name = update.message.text
        user = update.effective_user
        logging.info(f"User {user.id} selected product/service: {product_name}")
        # TODO: Добавить логику обработки выбора товара/услуги
        await update.message.reply_text(f"Вы выбрали: {product_name}. (логика заказа пока не добавлена)")

    async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Возвращает пользователя к главной клавиатуре с категориями."""
        user = update.effective_user
        logging.info(f"User {user.id} returned to main menu.")
        await update.message.reply_text(
            text="Главное меню:",
            reply_markup=create_main_keyboard()
        )

    async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Отправляет информацию о СПОСОБАХ оплаты."""
        user = update.effective_user
        logging.info(f"User {user.id} requested payment methods.")
        await update.message.reply_text(
            PAYMENT_INFO, # Теперь здесь способы оплаты
            parse_mode='Markdown'
        )

    # --- Настройка Обработчиков ---

    def setup_handlers(application: Application) -> None:
        """Добавляет все обработчики в приложение."""

        # Обновляем списки для Regex с учетом "Доп. услуги"
        category_keys_pattern = "|".join(map(re.escape, CATEGORIES.keys()))
        all_product_names = [
            item for sublist in CATEGORIES.values() for item in sublist
        ]
        product_names_pattern = "|".join(map(re.escape, all_product_names)) if all_product_names else None

        # Порядок важен: Команда -> Точные совпадения -> Категории -> Товары/Услуги
        application.add_handler(CommandHandler("start", start))
        # Обработчик для кнопки "Оплата" (способы оплаты)
        application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^Оплата$') & ~filters.COMMAND, handle_payment))
        # Обработчик для кнопки "< Назад"
        application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^< Назад$') & ~filters.COMMAND, handle_back))

        # Обработчик категорий (включая "Доп. услуги")
        if category_keys_pattern:
            application.add_handler(MessageHandler(
                filters.TEXT & filters.Regex(f'^({category_keys_pattern})$') & ~filters.COMMAND,
                handle_category
            ))

        # Обработчик товаров и доп. услуг
        if product_names_pattern:
            application.add_handler(MessageHandler(
                filters.TEXT & filters.Regex(f'^({product_names_pattern})$') & ~filters.COMMAND,
                handle_product
            ))

        logging.info("Handlers reconfigured successfully (Payment Conditions in Welcome, Payment Methods on button).")