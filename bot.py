import telebot

TOKEN = "8459688522:AAGWJLK3uEs2cqmXsOrUz0oIaGGK1beqtw8"

bot = telebot.TeleBot(TOKEN)

user_data = {}   # здесь храним ответы пользователей


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_data[user_id] = {}

    bot.send_message(
        user_id,
        "Здравствуйте! 👋\n"
        "Я бот компании *Кухни Майя*.\n"
        "Помогу принять заявку на изготовление корпусной мебели.\n\n"
        "Как вас зовут?"
    )


@bot.message_handler(func=lambda m: True)
def handle(message):
    user_id = message.chat.id
    text = message.text

    # --- 1. ИМЯ ---
    if "name" not in user_data[user_id]:
        user_data[user_id]["name"] = text
        bot.send_message(
            user_id,
            "Приятно познакомиться! 🙌\n"
            "Какую мебель планируете заказать?\n\n"
            "Варианты:\n"
            "• Кухня\n"
            "• Шкаф\n"
            "• Гардеробная\n"
            "• Детская\n"
            "• В офис\n"
            "• Другое"
        )
        return

    # --- 2. ТИП МЕБЕЛИ ---
    if "type" not in user_data[user_id]:
        user_data[user_id]["type"] = text
        bot.send_message(
            user_id,
            "Отлично! 📐\n"
            "Напишите, пожалуйста, размеры или приблизительную площадь."
        )
        return

    # --- 3. РАЗМЕРЫ ---
    if "size" not in user_data[user_id]:
        user_data[user_id]["size"] = text
        bot.send_message(
            user_id,
            "Принято! 🎨\n"
            "Какой стиль мебели вам нравится?\n"
            "Например: современный, классика, минимализм и т.д."
        )
        return

    # --- 4. СТИЛЬ ---
    if "style" not in user_data[user_id]:
        user_data[user_id]["style"] = text
        bot.send_message(
            user_id,
            "Спасибо! ❤️\n"
            "Что вам нужно сейчас?\n"
            "• Замер\n"
            "• Расчет стоимости"
        )
        return

    # --- 5. ЗАМЕР / РАСЧЁТ ---
    if "request" not in user_data[user_id]:
        user_data[user_id]["request"] = text

        data = user_data[user_id]

        # Отправка клиенту подтверждения
        bot.send_message(
            user_id,
            "Отлично! Ваша заявка принята 🙌\n\n"
            f"Имя: *{data['name']}*\n"
            f"Мебель: *{data['type']}*\n"
            f"Размеры: *{data['size']}*\n"
            f"Стиль: *{data['style']}*\n"
            f"Потребность: *{data['request']}*\n\n"
            "Мы свяжемся с вами в ближайшее время!"
        )

        # Отправка заявки тебе (на твой id)
        bot.send_message(
            927677341,
            "📩 *Новая заявка!* \n\n"
            f"Имя: {data['name']}\n"
            f"Мебель: {data['type']}\n"
            f"Размеры: {data['size']}\n"
            f"Стиль: {data['style']}\n"
            f"Потребность: {data['request']}"
        )

        return


bot.polling(non_stop=True)
