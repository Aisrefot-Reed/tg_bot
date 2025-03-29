def format_artist_message(order_details: dict) -> str:
    """Форматирование сообщения для художника"""
    return (
        "🎨 Новый заказ!\n\n"
        f"Номер заказа: {order_details['order_id']}\n"
        f"Категория рисунка: {order_details['category']}\n"
        f"Способ оплаты: {order_details['payment_method']}\n"
        f"Имя клиента: {order_details['customer_name']}\n"
        f"Юзернейм: @{order_details['username']}"
    )