import telebot

TOKEN = "8459688522:AAGWJLK3uEs2cqmXsOrUz0oIaGGK1beqtw8"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Здравствуйте! 👋\n\n"
        "Я бот компании *Кухни Майя*.\n"
        "Помогу принять заявку на изготовление кухни.\n\n"
        "Как вас зовут?"
    )

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_id = message.chat.id
    text = message.text

    if "имя" not in bot.__dict__:
        bot.__dict__["имя"] = {}
    if "телефон" not in bot.__dict__:
        bot.__dict__["телефон"] = {}

    if user_id not in bot.__dict__["имя"]:
        bot.__dict__["имя"][user_id] = text
        bot.send_message(user_id, "Спасибо! Теперь напишите ваш номер телефона 📱")
        return

    if user_id not in bot.__dict__["телефон"]:
        bot.__dict__["телефон"][user_id] = text

        name = bot.__dict__["имя"][user_id]
        phone = bot.__dict__["телефон"][user_id]

        bot.send_message(
            user_id,
            f"Отлично! Ваша заявка принята 🙌\n\n"
            f"Имя: *{name}*\n"
            f"Телефон: *{phone}*\n\n"
            f"Мы свяжемся с вами в ближайшее время!"
        )

        bot.send_message(
            927677341,
            f"📩 Новая заявка!\n\nИмя: {name}\nТелефон: {phone}"
        )
        return

bot.polling(non_stop=True)
