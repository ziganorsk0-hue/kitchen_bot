import telebot
from telebot import types
from flask import Flask, request
import os

# 👉 Твой токен
TOKEN = "8459688522:AAGWJLK3uEs2cqmXsOrUz0oIaGGK1beqtw8"

# 👉 Твой Telegram ID (чтобы заявки приходили в личку)
ADMIN_ID = 927677341

bot = telebot.TeleBot(TOKEN, threaded=False)
server = Flask(__name__)

user_state = {}
user_data = {}

# -------------------------------
# МЕНЮ
# -------------------------------
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📝 Оставить заявку", "💬 Консультация")
    return kb


# -------------------------------
# START
# -------------------------------
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Здравствуйте! 👋\n"
        "Я Павел, мастер компании *Кухни Майя*.\n"
        "Делаю кухни и корпусную мебель на заказ.\n\n"
        "Чем могу помочь? 🙂",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )


# -------------------------------
# НАЧАТЬ ЗАЯВКУ
# -------------------------------
@bot.message_handler(func=lambda m: m.text == "📝 Оставить заявку")
def start_form(message):
    chat_id = message.chat.id

    user_state[chat_id] = "q1"
    user_data[chat_id] = {}

    bot.send_message(chat_id, "1️⃣ Какую мебель планируете заказать?")


# -------------------------------
# КОНСУЛЬТАЦИЯ
# -------------------------------
@bot.message_handler(func=lambda m: m.text == "💬 Консультация")
def consult(message):
    bot.send_message(
        message.chat.id,
        "С удовольствием помогу! 😊\nОпишите, что хотите — и я подскажу лучшее решение."
    )


# -------------------------------
# ЛОГИКА ОПРОСА
# -------------------------------
@bot.message_handler(func=lambda m: m.chat.id in user_state)
def form_logic(message):
    chat_id = message.chat.id
    text = message.text
    state = user_state[chat_id]

    if state == "q1":
        user_data[chat_id]["type"] = text
        bot.send_message(chat_id, "2️⃣ Какой стиль предпочитаете?")
        user_state[chat_id] = "q2"
        return

    if state == "q2":
        user_data[chat_id]["style"] = text
        bot.send_message(chat_id, "3️⃣ На какой стадии ремонт?")
        user_state[chat_id] = "q3"
        return

    if state == "q3":
        user_data[chat_id]["repair"] = text
        bot.send_message(chat_id, "4️⃣ На какой бюджет ориентируетесь?")
        user_state[chat_id] = "q4"
        return

    if state == "q4":
        user_data[chat_id]["budget"] = text
        bot.send_message(chat_id, "5️⃣ Оставьте, пожалуйста, ваш номер телефона 📞")
        user_state[chat_id] = "phone"
        return

    if state == "phone":
        user_data[chat_id]["phone"] = text

        data = user_data[chat_id]
        username = message.from_user.username or "—"

        bot.send_message(
            ADMIN_ID,
            f"📩 *Новая заявка!*\n\n"
            f"📦 Мебель: {data['type']}\n"
            f"🎨 Стиль: {data['style']}\n"
            f"🏡 Ремонт: {data['repair']}\n"
            f"💵 Бюджет: {data['budget']}\n"
            f"📞 Телефон: {data['phone']}\n"
            f"🧑 Клиент: @{username}",
            parse_mode="Markdown"
        )

        bot.send_message(
            chat_id,
            "Спасибо! 🙌 Я получил вашу заявку. Скоро свяжусь 😊",
            reply_markup=main_menu()
        )

        del user_state[chat_id]
        del user_data[chat_id]
        return


# -------------------------------
# FLASK + WEBHOOK ДЛЯ RENDER
# -------------------------------
@server.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


@server.route("/", methods=["GET"])
def index():
    return "Bot is running!", 200


if __name__ == "__main__":
    bot.remove_webhook()

    # Render создаёт переменную окружения с доменом
    APP_URL = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')}/{TOKEN}"

    bot.set_webhook(url=APP_URL)
    server.run(host="0.0.0.0", port=5000)
