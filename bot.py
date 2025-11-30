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
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")  # https://your-bot.onrender.com

if not TOKEN or not ADMIN_ID or not RENDER_URL:
    print("❌ Не заданы TELEGRAM_TOKEN, ADMIN_ID или RENDER_EXTERNAL_URL")
    sys.exit(1)

ADMIN_ID = int(ADMIN_ID)
WEBHOOK_URL = f"{RENDER_URL}/{TOKEN}"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

# ========================
# Состояния пользователей
# ========================
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
    markup.add(InlineKeyboardButton("🪑 Рассчитать стоимость", callback_data="calc_cost"))
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

# ========================
# CALLBACKS
# ========================
@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    bot.answer_callback_query(call.id)
    uid = call.message.chat.id

    # ---- О компании (мощный текст) ----
    if call.data == "about":
        text = (
            "<b>Здравствуйте! Я — Павел, частный мастер по мебели с опытом более 18 лет.</b>\n\n"
            "Я создаю кухни, шкафы и корпусную мебель, которая идеально подходит под размеры, "
            "задачу и стиль интерьера.\n\n"
            "Работаю без посредников и салонов — лично веду каждый проект от первого сообщения до установки. "
            "Вы получаете честную цену, аккуратную работу и результат, за который не стыдно.\n\n"
            "<b>Что я делаю:</b>\n"
            "✔ Точный замер и профессиональная консультация\n"
            "✔ Помощь с проектом и подбором материалов\n"
            "✔ Расчёт, изготовление и установка «под ключ»\n"
            "✔ Качество, которое служит годами\n\n"
            "Делаю мебель, которая не просто стоит в квартире — "
            "<b>а радует, работает и выглядит так, как вы задумали.</b>\n\n"
            "Готов помочь с вашим проектом."
        )
        bot.send_message(uid, text, parse_mode="HTML")
        return

    # ---- Запись на замер ----
    if call.data == "measure":
        today = datetime.date.today()
        calendar_page[uid] = (today.year, today.month)
        bot.send_message(uid, "Выберите день:", reply_markup=build_calendar(uid))
        return

    if call.data.startswith("month_"):
        _, y, m = call.data.split("_")
        calendar_page[uid] = (int(y), int(m))
        bot.edit_message_reply_markup(uid, call.message.message_id, reply_markup=build_calendar(uid))
        return

    if call.data.startswith("day_"):
        handle_day_selection(call)
        return

    # ---- Расчёт стоимости ----
    if call.data == "calc_cost":
        ask_furniture_type(uid)
        return

    if call.data.startswith("furn_"):
        furniture = call.data[5:]
        user_state[uid] = {"type": "calc", "furniture": furniture}
        ask_project_exist(uid)
        return

    if call.data.startswith("proj_"):
        proj = call.data[5:]
        user_state[uid]["project"] = proj
        ask_phone(uid)
        return

# ========================
# Календарь
# ========================
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

# ========================
# День выбран для замера
# ========================
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

# ========================
# Блок расчёта стоимости
# ========================
def ask_furniture_type(uid):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Кухня", callback_data="furn_Кухня"))
    markup.add(InlineKeyboardButton("Шкаф", callback_data="furn_Шкаф"))
    markup.add(InlineKeyboardButton("Гардеробная", callback_data="furn_Гардеробная"))
    markup.add(InlineKeyboardButton("Тумба", callback_data="furn_Тумба"))
    markup.add(InlineKeyboardButton("Другое", callback_data="furn_Другое"))

    bot.send_message(uid, "Какую мебель планируете заказать?", reply_markup=markup)

def ask_project_exist(uid):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Да, есть проект", callback_data="proj_Да"))
    markup.add(InlineKeyboardButton("Нет, нужна помощь", callback_data="proj_Нет"))

    bot.send_message(uid, "Есть готовый проект?", reply_markup=markup)

def ask_phone(uid):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("Отправить телефон", request_contact=True))
    bot.send_message(uid, "Оставьте номер телефона:", reply_markup=kb)

# ========================
# Принимаем телефон / контакт
# ========================
@bot.message_handler(content_types=["contact", "text"])
def get_phone(msg):
    uid = msg.chat.id
    state = user_state.get(uid)

    if not state:
        bot.send_message(uid, "Напишите /start чтобы начать заново.")
        return

    phone = msg.contact.phone_number if msg.contact else msg.text

    # ---- Замер ----
    if state["type"] == "measure":
        bot.send_message(
            ADMIN_ID,
            f"<b>📅 Запись на замер</b>\nДата: {state['date']}\nТелефон: {phone}"
        )
        bot.send_message(uid, "Спасибо! Я свяжусь с вами.", reply_markup=ReplyKeyboardRemove())

    # ---- Расчёт стоимости ----
    elif state["type"] == "calc":
        bot.send_message(
            ADMIN_ID,
            f"<b>💰 Заявка на расчет стоимости</b>\n"
            f"Тип мебели: {state['furniture']}\n"
            f"Проект: {state['project']}\n"
            f"Телефон: {phone}"
        )
        bot.send_message(uid, "Спасибо! Сделаю расчёт и свяжусь с вами.", reply_markup=ReplyKeyboardRemove())

    user_state.pop(uid, None)

# ========================
# WEBHOOK для Render
# ========================
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_string = request.data.decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/", methods=["GET"])
def index():
    return "Bot is running", 200

# ========================
# Запуск на Render
# ========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
