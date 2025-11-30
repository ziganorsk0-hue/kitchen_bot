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
# ENV
# ========================
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN or not ADMIN_ID or not RENDER_URL:
    print("❌ Missing TELEGRAM_TOKEN, ADMIN_ID or RENDER_EXTERNAL_URL")
    sys.exit(1)

ADMIN_ID = int(ADMIN_ID)
WEBHOOK_URL = f"{RENDER_URL}/{TOKEN}"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

# хранение состояний
user_state = {}
calendar_page = {}

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
# Команда /start
# ========================
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Здравствуйте! 👋\nВыберите действие:",
        reply_markup=get_main_menu()
    )


# =========================================================
# CALLBACKS
# =========================================================
@bot.callback_query_handler(func=lambda c: True)
def callbacks(call):
    bot.answer_callback_query(call.id)
    uid = call.message.chat.id

    if call.data == "about":
        bot.send_message(
            uid,
            "Я частный мастер, Павел.\n"
            "Изготавливаю кухни и корпусную мебель с 2006 года.\n"
            "Могу рассчитать проект по вашим размерам. 🚀"
        )

    elif call.data == "measure":
        today = datetime.date.today()
        calendar_page[uid] = (today.year, today.month)
        bot.send_message(uid, "Выберите день:", reply_markup=build_calendar(uid))

    elif call.data.startswith("month_"):
        _, y, m = call.data.split("_")
        calendar_page[uid] = (int(y), int(m))
        bot.edit_message_reply_markup(uid, call.message.message_id, reply_markup=build_calendar(uid))

    elif call.data.startswith("day_"):
        handle_day_selection(call)


# =========================================================
# Календарь
# =========================================================
def build_calendar(uid):
    year, month = calendar_page[uid]
    markup = InlineKeyboardMarkup()

    markup.add(InlineKeyboardButton(f"{RU_MONTHS[month]} {year}", callback_data="ignore"))
    markup.row(*[InlineKeyboardButton(d, callback_data="ignore") for d in RU_DAYS])

    days = calendar.Calendar().itermonthdays(year, month)
    week = []

    for d in days:
        if d == 0:
            week.append(InlineKeyboardButton(" ", callback_data="ignore"))
        else:
            iso = datetime.date(year, month, d).isoformat()
            week.append(InlineKeyboardButton(str(d), callback_data=f"day_{iso}"))

        if len(week) == 7:
            markup.row(*week)
            week = []

    if week:
        markup.row(*week)

    # переключение месяцев
    pm = month - 1 if month > 1 else 12
    py = year - 1 if month == 1 else year

    nm = month + 1 if month < 12 else 1
    ny = year + 1 if month == 12 else year

    markup.row(
        InlineKeyboardButton("◀️", callback_data=f"month_{py}_{pm}"),
        InlineKeyboardButton("▶️", callback_data=f"month_{ny}_{nm}")
    )
    return markup


# =========================================================
# День выбран
# =========================================================
def handle_day_selection(call):
    uid = call.message.chat.id
    date_iso = call.data[4:]

    user_state[uid] = {"type": "measure", "date": date_iso}

    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("Отправить телефон", request_contact=True))

    bot.send_message(
        uid,
        f"Вы выбрали: <b>{date_iso}</b>\nОтправьте номер телефона:",
        reply_markup=kb
    )


# =========================================================
# Сообщения (контакт или текст)
# =========================================================
@bot.message_handler(content_types=["contact", "text"])
def get_phone(msg):
    uid = msg.chat.id
    state = user_state.get(uid)

    if not state:
        bot.send_message(uid, "Напишите /start чтобы начать заново.")
        return

    if state["type"] == "measure":
        phone = msg.contact.phone_number if msg.contact else msg.text
        date = state["date"]

        bot.send_message(
            ADMIN_ID,
            f"<b>📅 Запись на замер</b>\nДата: {date}\nТелефон: {phone}"
        )

        bot.send_message(uid, "Спасибо! Я свяжусь с вами.", reply_markup=ReplyKeyboardRemove())
        user_state.pop(uid, None)


# =========================================================
# WEBHOOK
# =========================================================
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.data.decode())])
    return "ok"

@app.route("/")
def index():
    return "Bot is running", 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
