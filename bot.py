import sys
import os
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import datetime
import locale

# ========================
# Русская локализация для дат
# ========================
locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

# ========================
# Переменные окружения
# ========================
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN or not ADMIN_ID or not RENDER_URL:
    print("❌ TELEGRAM_TOKEN, ADMIN_ID или RENDER_EXTERNAL_URL не заданы")
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
    "2️⃣ В каком стиле хотите?",
    "3️⃣ Какой материал предпочитаете?",
    "4️⃣ Есть ли особые требования к размерам или конструкции?",
    "5️⃣ Когда планируете начать проект / нужен замер?"
]

# ========================
# М И Н И  -  М Е Н Ю
# ========================
def get_main_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📅 Записаться на замер", callback_data="measure"))
    markup.add(InlineKeyboardButton("📝 Оставить заявку", callback_data="start_request"))
    markup.add(InlineKeyboardButton("ℹ️ О компании", callback_data="about"))
    return markup

# ========================
# /start и приветствие
# ========================
def greet_user(user_id):
    bot.send_message(user_id, "Здравствуйте! 👋\nВыберите действие:", reply_markup=get_main_menu())

# ========================
# Автозапуск при входе
# ========================
@bot.message_handler(func=lambda message: True)
def greet_first(message):
    user_id = message.chat.id
    if user_id not in user_state:
        greet_user(user_id)
    # Далее обработка сообщений будет идти через callback или phone

# ========================
# Обработка меню
# ========================
@bot.callback_query_handler(func=lambda call: True)
def handle_menu(call):
    bot.answer_callback_query(call.id)
    user_id = call.message.chat.id

    if call.data == "about":
        bot.send_message(user_id,
                         "Я частный мастер, Павел.\n"
                         "Изготавливаю корпусную мебель на заказ с 2006 года.\n"
                         "Реализую проекты по вашим размерам и пожеланиям.\n"
                         "Оставляйте заявку — я свяжусь с вами для уточнения всех деталей. 🚀")
    elif call.data == "start_request":
        user_state[user_id] = 0
        user_answers[user_id] = []
        bot.send_message(user_id, "📝 Давайте оформим заявку.")
        bot.send_message(user_id, questions[0])
    elif call.data == "measure":
        bot.send_message(user_id, "Выберите удобный день для замера:", reply_markup=build_calendar())
    elif call.data.startswith("day_"):
        date = call.data[4:]
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn = KeyboardButton("Отправить номер телефона", request_contact=True)
        markup.add(btn)
        user_state[user_id] = f"phone_for_measure_{date}"
        bot.send_message(user_id,
                         f"Вы выбрали день: *{date}*\nОставьте номер телефона для записи на замер:",
                         parse_mode="Markdown",
                         reply_markup=markup)

# ========================
# Календарь на месяц (русский)
# ========================
def build_calendar():
    markup = InlineKeyboardMarkup()
    today = datetime.date.today()
    for i in range(30):
        day = today + datetime.timedelta(days=i)
        label = day.strftime("%a, %d %b")  # Пн, 01 Ноя
        markup.add(InlineKeyboardButton(label, callback_data=f"day_{day}"))
    return markup

# ========================
# Обработка сообщений
# ========================
@bot.message_handler(content_types=["text", "contact"])
def process_messages(msg):
    user_id = msg.chat.id

    # Запись на замер
    if user_state.get(user_id, "").startswith("phone_for_measure_"):
        date = user_state[user_id].replace("phone_for_measure_", "")
        phone = msg.contact.phone_number if msg.contact else msg.text
        bot.send_message(ADMIN_ID, f"📅 *Запись на замер*\nДата: {date}\nТелефон: {phone}", parse_mode="Markdown")
        bot.send_message(user_id, "Спасибо! Мы свяжемся с вами для подтверждения.", reply_markup=ReplyKeyboardRemove())
        user_state.pop(user_id, None)
        return

    # Заявка на мебель
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
        f"3. Материал: {info[2]}\n"
        f"4. Особенности: {info[3]}\n"
        f"5. Сроки: {info[4]}\n"
        f"📱 Телефон: {phone}"
    )
    bot.send_message(ADMIN_ID, txt, parse_mode="Markdown")
    bot.send_message(user_id, "Спасибо! Заявка отправлена.", reply_markup=ReplyKeyboardRemove())

    user_state.pop(user_id)
    user_answers.pop(user_id)

# ========================
# WEBHOOK
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
