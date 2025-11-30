import sys
import os
from flask import Flask, request
import telebot
from telebot.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
import datetime
import calendar

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

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

# ========================
# Память
# ========================
users_started = set()
user_state = {}
calendar_page = {}

# ========================
# Русские дни недели и месяцы
# ========================
RU_DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
RU_MONTHS = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

# ========================
# Главное меню
# ========================
def get_main_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📅 Записаться на замер", callback_data="measure"))
    markup.add(InlineKeyboardButton("ℹ️ О компании", callback_data="about"))
    return markup

# ========================
# Первый старт — только один раз
# ========================
@bot.message_handler(func=lambda m: m.chat.id not in users_started, content_types=["text"])
def show_start_button(message):
    user_id = message.chat.id
    users_started.add(user_id)

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🚀 Начать", callback_data="start"))

    bot.send_message(user_id, "Привет! Нажмите кнопку чтобы начать:", reply_markup=markup)

# ========================
# CALLBACK HANDLER
# ========================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    bot.answer_callback_query(call.id)
    user_id = call.message.chat.id

    if call.data == "start":
        greet_user(user_id)

    elif call.data == "about":
        bot.send_message(
            user_id,
            "Я частный мастер, Павел.\n"
            "Изготавливаю корпусную мебель на заказ с 2006 года.\n"
            "Делаю кухни, шкафы, гардеробные.\n"
            "Запишитесь на замер, и я сделаю расчёт. 🚀"
        )

    elif call.data == "measure":
        today = datetime.date.today()
        calendar_page[user_id] = (today.year, today.month)
        bot.send_message(user_id, "Выберите день:", reply_markup=build_calendar(user_id))

    elif call.data.startswith("month_"):
        _, y, m = call.data.split("_")
        calendar_page[user_id] = (int(y), int(m))
        bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id,
                                      reply_markup=build_calendar(user_id))

    elif call.data.startswith("day_"):
        handle_day_selection(call)

# ========================
# Приветствие и меню
# ========================
def greet_user(user_id):
    bot.send_message(
        user_id,
        "Здравствуйте! 👋\nВыберите действие:",
        reply_markup=get_main_menu()
    )

# ========================
# Построение календаря
# ========================
def build_calendar(user_id):
    year, month = calendar_page[user_id]
    markup = InlineKeyboardMarkup()

    # Заголовок
    markup.add(InlineKeyboardButton(f"{RU_MONTHS[month]} {year}", callback_data="ignore"))

    # Дни недели
    markup.row(*[InlineKeyboardButton(d, callback_data="ignore") for d in RU_DAYS])

    # Дни месяца
    dates = calendar.Calendar(firstweekday=0).itermonthdays(year, month)
    week = []

    for day in dates:
        if day == 0:
            week.append(InlineKeyboardButton(" ", callback_data="ignore"))
        else:
            dt = datetime.date(year, month, day)
            week.append(InlineKeyboardButton(str(day), callback_data=f"day_{dt.isoformat()}"))

        if len(week) == 7:
            markup.row(*week)
            week = []

    if week:
        markup.row(*week)

    # Переключение месяца
    prev_m = month - 1
    prev_y = year
    if prev_m == 0:
        prev_m = 12
        prev_y -= 1

    next_m = month + 1
    next_y = year
    if next_m == 13:
        next_m = 1
        next_y += 1

    markup.row(
        InlineKeyboardButton("◀️ Назад", callback_data=f"month_{prev_y}_{prev_m}"),
        InlineKeyboardButton("▶️ Вперёд", callback_data=f"month_{next_y}_{next_m}")
    )

    return markup

# ========================
# Выбор дня
# ========================
def handle_day_selection(call):
    user_id = call.message.chat.id
    date_iso = call.data[4:]

    user_state[user_id] = {"type": "measure", "date": date_iso}

    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("Отправить номер телефона", request_contact=True))

    bot.send_message(
        user_id,
        f"Вы выбрали: <b>{date_iso}</b>\n"
        "Пожалуйста, отправьте номер телефона:",
        reply_markup=markup
    )

# ========================
# Обработка номера телефона
# ========================
@bot.message_handler(content_types=["text", "contact"])
def process_user_message(msg):
    user_id = msg.chat.id
    state = user_state.get(user_id)

    if not state:
        return  # игнорируем, если нет контекста

    if state["type"] == "measure":
        phone = msg.contact.phone_number if msg.contact else msg.text
        date = state["date"]

        bot.send_message(
            ADMIN_ID,
            f"<b>📅 Запись на замер</b>\nДата: {date}\nТелефон: {phone}"
        )

        bot.send_message(
            user_id,
            "Спасибо! Я свяжусь с вами для подтверждения.",
            reply_markup=ReplyKeyboardRemove()
        )

        user_state.pop(user_id, None)

# ========================
# WEBHOOK
# ========================
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.data.decode("utf-8"))])
    return "ok"

@app.route("/")
def index():
    return "Bot is running", 200

# Запуск Flask (Render)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
