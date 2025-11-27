import telebot

TOKEN = "8459688522:AAGWJLK3uEs2cqmXsOrUz0oIaGGK1beqtw8"
ADMIN_ID = 927677341   # ← твой Telegram ID

bot = telebot.TeleBot(TOKEN)

user_data = {}   # хранилище данных


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

    if user_id not in user_data:
        user_data[user_id] = {}
        bot.send_message(user_id, "Давайте начнём сначала 🙂\nКак вас зовут?")
        return

    # --- 1. ИМЯ ---
    if "name" not in user_data[user_id]:
        user_data[user_id]["name"] = text
        bot.send_message(
            user_id,
            "Приятно познакомиться! 🙌\n"
            "Какую мебель планируете заказать?\n\n"
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
