import sys
import os
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
    print("❌ TELEGRAM_TOKEN, ADMIN_ID или RENDER_EXTERNAL_URL не заданы")
    sys.exit(1)

ADMIN_ID = int(ADMIN_ID)
WEBHOOK_URL = f"{RENDER_URL}/{TOKEN}"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_state = {}
users_started = set()

# ========================
# Русские дни недели
# ========================
RU_DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

# ========================
# Главное меню
# ========================
def get_main_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📅 Записаться на замер", callback_data="measure"))
    markup.add(InlineKeyboardButton("ℹ️ О компании", callback_data="about"))
    return markup

# ========================
# Кнопка "Начать" при первом сообщении
# ========================
@bot.message_handler(func=lambda message: True, content_types=["text"])
def show_start_button(message):
    user_id = message.chat.id
    if user_id not in users_started:
        users_started.add(user_id)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🚀 Начать", callback_data="start"))
        bot.send_message(user_id, "Привет! Нажми кнопку чтобы начать:", reply_markup=markup)

# ========================
# Обработка callback
# ========================
@bot.callback_query_handler(func=lambda call: True)
def handle_menu(call):
    bot.answer_callback_query(call.id)
    user_id = call.message.chat.id

    if call.data == "start":
        greet_user(user_id)
    elif call.data == "about":
        bot.send_message(user_id,
                         "Я частный мастер, Павел.\n"
                         "Изготавливаю корпусную мебель на заказ с 2006 года.\n"
                         "Реализую проекты по вашим размерам и пожеланиям.\n"
                         "Свяжитесь со мной через запись на замер. 🚀")
    elif call.data == "measure":
        bot.send_message(user_id, "Выберите удобный день для замера:", reply_markup=build_calendar())
    elif call.data.startswith("day_"):
        handle_day_selection(call)

# ========================
# Главное меню после нажатия "Начать"
# ========================
def greet_user(user_id):
    bot.send_message(user_id, "Здравствуйте! 👋\nВыберите действие:", reply_markup=get_main_menu())

# ========================
# Календарь 30 дней: день недели + число
# ========================
def build_calendar():
    markup = InlineKeyboardMarkup(row_width=7)
    today = datetime.date.today()
    
    days = [today + datetime.timedelta(days=i) for i in range(30)]
    week_buttons = []
    
    for i, day in enumerate(days, start=1):
        day_of_week = RU_DAYS[day.weekday()]       # Пн, Вт и т.д.
        label = f"{day_of_week} {day.day}"         # Пн 29, Вт 30 ...
        callback = f"day_{day.isoformat()}"
        week_buttons.append(InlineKeyboardButton(label, callback_data=callback))

        if i % 7 == 0:
            markup.row(*week_buttons)
            week_buttons = []

    if week_buttons:
        markup.row(*week_buttons)

    return markup

# ========================
# Выбор даты для замера
# ========================
def handle_day_selection(call):
    bot.answer_callback_query(call.id)
    user_id = call.message.chat.id
    date_iso = call.data[4:]

    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = KeyboardButton("Отправить номер телефона", request_contact=True)
    markup.add(btn)

    user_state[user_id] = {"type": "measure", "date": date_iso}

    bot.send_message(
        user_id,
        f"Вы выбрали день: {date_iso}\nОставьте номер телефона для записи на замер:",
        reply_markup=markup
    )

# ========================
# Обработка сообщений для замера
# ========================
@bot.message_handler(content_types=["text", "contact"])
def process_messages(msg):
    user_id = msg.chat.id
    state = user_state.get(user_id)

    if isinstance(state, dict) and state.get("type") == "measure":
        phone = msg.contact.phone_number if msg.contact else msg.text
        date = state["date"]
        bot.send_message(ADMIN_ID, f"📅 *Запись на замер*\nДата: {date}\nТелефон: {phone}", parse_mode="Markdown")
        bot.send_message(user_id, "Спасибо! Мы свяжемся с вами для подтверждения.", reply_markup=ReplyKeyboardRemove())
        user_state.pop(user_id, None)

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
