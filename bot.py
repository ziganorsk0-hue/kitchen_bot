import telebot
from telebot import types
from flask import Flask, request
import os

TOKEN = "8459688522:AAGWJLK3uEs2cqmXsOrUz0oIaGGK1beqtw8"
ADMIN_ID = 927677341  # твой Telegram ID

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_data = {}  # временное хранилище заявок


# -------------------------------
# МЕНЮ
# -------------------------------
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📝 Оставить заявку")
    return kb


# -------------------------------
# START
# -------------------------------
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Здравствуйте! 👋\n"
        "Я бот компании *Кухни Майя*.\n"
        "Готов принять заявку.",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )


# -------------------------------
# НАЧАТЬ ЗАЯВКУ
# -------------------------------
@bot.message_handler(func=lambda m: m.text == "📝 Оставить заявку")
def ask_name(message):
    user_data[message.chat.id] = {}
    bot.send_message(message.chat.id, "Как вас зовут?")


# -------------------------------
# ЛОГИКА СБОРА ЗАЯВКИ
# -------------------------------
@bot.message_handler(func=lambda m: True)
def form_handler(message):
    user_id = message.chat.id
    text = message.text

    if user_id not in user_data:
        return

    # 1 — имя
    if "name" not in user_data[user_id]:
        user_data[user_id]["name"] = text
        bot.send_message(
            user_id,
            "Какую мебель планируете заказать?\n"
            "• Кухня\n• Шкаф\n• Гардеробная\n• Детская\n• В офис\n• Другое"
        )
        return

    # 2 — тип мебели
    if "type" not in user_data[user_id]:
        user_data[user_id]["type"] = text
        bot.send_message(user_id, "Оставьте ваш номер телефона:")
        return

    # 3 — телефон
    if "phone" not in user_data[user_id]:
        user_data[user_id]["phone"] = text

        name = user_data[user_id]["name"]
        type_f = user_data[user_id]["type"]
        phone = user_data[user_id]["phone"]
        username = message.from_user.username

        # отправка админу
        bot.send_message(
            ADMIN_ID,
            f"📩 Новая заявка!\n\n"
            f"👤 Имя: {name}\n"
            f"📦 Мебель: {type_f}\n"
            f"📞 Телефон: {phone}\n"
            f"🆔 Пользователь: @{username}"
        )

        bot.send_message(
            user_id,
            "Спасибо! 🙌 Заявка отправлена менеджеру.",
            reply_markup=main_menu()
        )

        del user_data[user_id]
        return


# -------------------------------
# WEBHOOK
# -------------------------------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_data = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_data)
    bot.process_new_updates([update])
    return "ok", 200


# -------------------------------
# ЗАПУСК
# -------------------------------
if __name__ == "__main__":
    # URL твоего приложения на Render
    WEBHOOK_URL = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

    # Flask сервер
    app.run(host="0.0.0.0", port=5000)
