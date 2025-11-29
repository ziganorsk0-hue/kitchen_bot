import os
import sys
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import datetime

# ========================
# Переменные окружения
# ========================
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN or not ADMIN_ID or not RENDER_URL:
    print("❌ Ошибка: TELEGRAM_TOKEN, ADMIN_ID или RENDER_EXTERNAL_URL не заданы")
    sys.exit(1)

ADMIN_ID = int(ADMIN_ID)
WEBHOOK_URL = f"{RENDER_URL}/{TOKEN}"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_state = {}
user_answers = {}

# ========================
# Вопросы для заявки
# ========================
questions = [
    "1️⃣ Какую мебель планируете заказать?",
    "2️⃣ В каком стиле хотите?"
]

# ========================
# Мини-меню
# ========================
def get_main_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📅 Записаться на замер", callback_data="measure"))
    markup.add(InlineKeyboardButton("📝 Оставить заявку", callback_data="start_request"))
    markup.add(InlineKeyboardButton("ℹ️ О компании", callback_data="about"))
    return markup

# ========================
# /start
# ========================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    bot.send_message(user_id, "Здравствуйте! 👋\nВыберите действие:", reply_markup=get_main_menu())

# ========================
# О компании
# ========================
@bot.callback_query_handler(func=lambda call: call.data == "about")
def about(call):
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "👋 Привет! Я Павел — частный мастер по изготовлению корпусной мебели с 2006 года.\n\n"
        "🛠️ Моя цель — воплотить в жизнь любой проект по вашим размерам и пожеланиям.\n\n"
        "📌 Я работаю индивидуально с каждым клиентом, поэтому каждая мебель уникальна.\n\n"
        "✏️ Оставьте заявку, и я свяжусь с вами, чтобы обсудить детали и предложить лучшие решения для вашего интерьера.\n\n"
        "🚀 Давайте создадим мебель вашей мечты вместе!",
        parse_mode="Markdown"
    )

# ========================
# Начало заявки
# ========================
@bot.callback_query_handler(func=lambda call: call.data == "start_request")
def start_request(call):
    user_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    user_state[user_id] = 0
    user_answers[user_id] = []
    bot.send_message(user_id, "📝 Давайте оформим заявку.")
    bot.send_message(user_id, questions[0])

# ========================
# Календарь для замера
# ========================
def build_calendar():
    markup = InlineKeyboardMarkup()
    today = datetime.date.today()
    for i in range(7):
        day = today + datetime.timedelta(days=i)
        label = day.strftime("%d.%m (%a)")
        markup.add(InlineKeyboardButton(label, callback_data=f"day_{day}"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "measure")
def measure(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Выберите удобный день:", reply_markup=build_calendar())

@bot.callback_query_handler(func=lambda call: call.data.startswith("day_"))
def choose_day(call):
    bot.answer_callback_query(call.id)
    date = call.data[4:]
    bot.send_message(call.message.chat.id, f"Вы выбрали день: *{date}*\nТеперь оставьте телефон.", parse_mode="Markdown")

    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = KeyboardButton("Отправить номер телефона", request_contact=True)
    markup.add(btn)

    user_state[call.message.chat.id] = "phone_for_measure"
    bot.send_message(call.message.chat.id, "Нажмите кнопку ниже:", reply_markup=markup)

# ========================
# Обработка сообщений и контактов
# ========================
@bot.message_handler(func=lambda msg: True, content_types=["text", "contact"])
def process(msg):
    user_id = msg.chat.id

    # Запись на замер
    if user_state.get(user_id) == "phone_for_measure":
        phone = msg.contact.phone_number if msg.contact else msg.text
        bot.send_message(ADMIN_ID, f"📅 *Запись на замер*\nТелефон: {phone}", parse_mode="Markdown")
        bot.send_message(user_id, "Спасибо! Мы свяжемся с вами.", reply_markup=ReplyKeyboardRemove())
        user_state.pop(user_id, None)
        return

    # Заявка по вопросам
    if user_id not in user_state:
        return

    step = user_state[user_id]
    if step < len(questions):
        user_answers[user_id].append(msg.text)
        user_state[user_id] += 1

        if user_state[user_id] < len(questions):
            bot.send_message(user_id, questions[user_state[user_id]])
        else:
            markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            btn = KeyboardButton("Отправить номер телефона", request_contact=True)
            markup.add(btn)
            bot.send_message(user_id, "Теперь оставьте номер телефона:", reply_markup=markup)
        return

    # Отправка заявки
    phone = msg.contact.phone_number if msg.contact else msg.text
    info = user_answers[user_id]
    txt = (
        "🔔 *Новая заявка!*\n\n"
        f"1. Мебель: {info[0]}\n"
        f"2. Стиль: {info[1]}\n"
        f"📱 Телефон: {phone}"
    )
    bot.send_message(ADMIN_ID, txt, parse_mode="Markdown")
    bot.send_message(user_id, "Спасибо! Заявка отправлена.", reply_markup=ReplyKeyboardRemove())

    user_state.pop(user_id)
    user_answers.pop(user_id)

# ========================
# Webhook
# ========================
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.data.decode("utf-8"))])
    return "ok"

@app.route("/")
def index():
    return "Bot is running", 200

# ========================
# Запуск Flask
# ========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
