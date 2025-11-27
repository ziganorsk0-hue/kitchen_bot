import telebot

TOKEN = "ТВОЙ_ТОКЕН_БОТА"

bot = telebot.TeleBot(TOKEN)

# Хранилище данных пользователей
user_data = {}


# === СТАРТ ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_data[user_id] = {"step": "name"}

    bot.send_message(
        user_id,
        "Здравствуйте! 👋\n\n"
        "Я бот компании *Кухни Майя*.\n"
        "Помогу принять заявку на изготовление мебели.\n\n"
        "Как вас зовут?"
    )


# === ОБЩИЙ ХЭНДЛЕР ===
@bot.message_handler(func=lambda m: True)
def handle(message):
    user_id = message.chat.id
    text = message.text

    # Если нет записи — начинаем сначала
    if user_id not in user_data:
        user_data[user_id] = {"step": "name"}
        bot.send_message(user_id, "Как вас зовут?")
        return

    step = user_data[user_id]["step"]

    # 1 — Сохраняем имя
    if step == "name":
        user_data[user_id]["name"] = text
        user_data[user_id]["step"] = "type"

        bot.send_message(
            user_id,
            "Приятно познакомиться! 😊\n\n"
            "Какую мебель планируете заказать?\n"
            "Выберите или напишите свой вариант:\n\n"
            "• Кухня\n• Шкаф\n• Гардеробная\n• Детская\n• Офисная мебель\n• Другое"
        )
        return

    # 2 — Тип мебели
    if step == "type":
        user_data[user_id]["type"] = text
        user_data[user_id]["step"] = "details"

        bot.send_message(
            user_id,
            "Отлично!\nНапишите, пожалуйста, *размеры*, *стиль* или любые пожелания.\n"
            "Можете отправить несколько сообщений — я всё запомню 😊"
        )
        return

    # 3 — Клиент описывает детали
    if step == "details":
        # сохраняем все сообщения как список
        if "details" not in user_data[user_id]:
            user_data[user_id]["details"] = []

        user_data[user_id]["details"].append(text)

        bot.send_message(
            user_id,
            "Принял 👍\nЕсли хотите ещё что-то добавить — напишите.\n\n"
            "Когда готовы, напишите: *готово*"
        )
        return

    # 4 — Готово → спросить замер/расчёт
    if step == "details" and text.lower() == "готово":
        user_data[user_id]["step"] = "final"

        bot.send_message(
            user_id,
            "Что вам нужно? Выберите:\n\n"
            "🔧 Замер\n📐 Расчёт стоимости"
        )
        return

    # 5 — финальный выбор
    if step == "final":
        user_data[user_id]["final"] = text

        name = user_data[user_id]["name"]
        mtype = user_data[user_id]["type"]
