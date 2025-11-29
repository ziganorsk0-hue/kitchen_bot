import sys
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import datetime
import os

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
    text = (
        "Я частный мастер, меня зовут Павел. 👋\n"
        "Занимаюсь изготовлением корпусной мебели с 2006 года.\n"
        "Реализую любые проекты по вашим размерам и пожеланиям.\n"
        "Оставляйте заявку, и я свяжусь с вами, чтобы обсудить детали."
    )
    bot.send_message(call.message.chat.id, text)

# ========================
# Вопросы для заявки
# ========================
questions = [
    "1️⃣ Какую мебель планируете заказать?",
    "2️⃣ В каком стиле хотите?"
]

# ========================
# Календарь с навигацией
# ========================
def build_calendar(start_date=None, weeks=2):
    if start_date is None:
        start_date = datetime.date.today()
    markup = InlineKeyboardMarkup(row_width=7)
    weekdays = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]
    for wd in weekdays:
        markup.add(InlineKeyboardButton(wd, callback_data="ignore"))

    start_week = start_date - datetime.timedelta(days=start_date.weekday())
    for week in range(weeks):
        for day_offset in range(7):
            day = start_week + datetime.timedelta(days=week*7 + day_offset)
            label = str(day.day)
            markup.add(InlineKeyboardButton(label, callback_data=f"day_{day}"))

    # Навигация
    prev_week = start_week - datetime.timedelta(weeks=weeks)
    next_week = start_week + datetime.timedelta(weeks=weeks)
    markup.add(
        InlineKeyboardButton("⬅️ Назад", callback_data=f"cal_{prev_week}"),
        InlineKeyboardButton("➡️ Вперед", callback_data=f"cal_{next_week}")
    )
    return markup

# ========================
# Обработка кнопки "Записаться на замер"
# ========================
@bot.callback_query_handler(func=lambda call: call.data == "measure")
def measure(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Выберите удобный день:", reply_markup=build_calendar())

# Обработка листания календаря
@bot.callback_query_handler(func=lambda call: call.data.startswith("cal_"))
def calendar_navigation(call):
    bot.answer_callback_query(call.id)
    date_str = call.data[4:]
    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    bot.send_message(call.message.chat.id, "Выберите день:", reply_markup=build_calendar(start_date=date_obj))

# Выбор конкретного дня
@bot.callback_query_handler(func=lambda call: call.data.startswith("day_"))
def choose_day(call):
    bot.answer_callback_query(call.id)
    date = call.data[4:]
    user_state[call.message.chat.id] = {"action":"measure", "day": date}

    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = KeyboardButton("Отправить номер телефона", request_contact=True)
    markup.add(btn)
    bot.send_message(call.message.chat.id, f"Вы выбрали {date}. Теперь оставьте телефон:", reply_markup=markup)

# ========================
# Обработка заявки и записи
# ========================
@bot.callback_query_handler(func=lambda call: call.data == "start_request")
def start_request(call):
    user_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    user_state[user_id] = {"action":"request", "step":0, "answers":[]}
    bot.send_message(user_id, "📝 Давайте оформим заявку.")
    bot.send_message(user_id, questions[0])

@bot.message_handler(func=lambda msg: True, content_types=["text","contact"])
def process(msg):
    user_id = msg.chat.id

    if user_id not in user_state:
        return

    state = user_state[user_id]

    # === Запись на замер ===
    if state.get("action")=="measure":
        phone = msg.contact.phone_number if msg.contact else msg.text
        bot.send_message(ADMIN_ID, f"📅 *Запись на замер*\nДата: {state['day']}\nТелефон: {phone}", parse_mode="Markdown")
        bot.send_message(user_id, "Спасибо! Мы свяжемся с вами.", reply_markup=ReplyKeyboardRemove())
        user_state.pop(user_id, None)
        return

    # === Заявка на мебель ===
    if state.get("action")=="request":
        step = state["step"]
        state["answers"].append(msg.text)
        state["step"] += 1

        if step+1 < len(questions):
            bot.send_message(user_id, questions[step+1])
        else:
            markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            btn = KeyboardButton("Отправить номер телефона", request_contact=True)
            markup.add(btn)
            bot.send_message(user_id, "Теперь оставьте номер телефона:", reply_markup=markup)
        return

    # Отправка телефона
    phone = msg.contact.phone_number if msg.contact else msg.text
    info = state["answers"]
    txt = (
        "🔔 *Новая заявка!*\n\n"
        f"1. Мебель: {info[0]}\n"
        f"2. Стиль: {info[1]}\n"
        f"📱 Телефон: {phone}"
    )
    bot.send_message(ADMIN_ID, txt, parse_mode="Markdown")
    bot.send_message(user_id, "Спасибо! Заявка отправлена.", reply_markup=ReplyKeyboardRemove())
    user_state.pop(user_id, None)

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0", port=port)
