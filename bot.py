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

user_state = {}      # Хранит шаг заявки или состояние замера
user_answers = {}    # Хранит ответы пользователей для заявки
users_started = set()  # Пользователи, которым уже показана кнопка "Начать"

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
# Русские дни недели и месяцы
# ========================
RU_MONTHS = {
    1: "Января", 2: "Февраля", 3: "Марта", 4: "Апреля",
    5: "Мая", 6: "Июня", 7: "Июля", 8: "Августа",
    9: "Сентября", 10: "Октября", 11: "Ноября", 12: "Декабря"
}

RU_DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

def format_date_ru(date_obj):
    day_of_week = RU_DAYS[date_obj.weekday()]
    month = RU_MONTHS[date_obj.month]
    return f"{day_of_week}, {date_obj.day} {month}"

# ========================
# Главное меню
# ========================
def get_main_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📅 Записаться на замер", callback_data="measure"))
    markup.add(InlineKeyboardButton("📝 Оставить заявку", callback_data="start_request"))
    markup.add(InlineKeyboardButton("ℹ️ О компании", callback_data="about"))
    return markup

# ========================
# Кнопка "Начать" при первом сообщении
# ========================
@bot.message_handler(func=lambda message: True, content_types=["text"])
def show_start_button(message):
    user_id = message.chat.id
    if user_id not in user_state and user_id not in users_started:
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
                         "Оставляйте заявку — я свяжусь с вами для уточнения всех деталей. 🚀")
    elif call.data == "start_request":
        # Начало заявки
        user_state[user_id] = 0
        user_answers[user_id] = []
        bot.send_message(user_id, "📝 Давайте оформим заявку.")
        bot.send_message(user_id, questions[0])
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
# Календарь 30 дней на русском
# ========================
def build_calendar():
    markup = InlineKeyboardMarkup(row_width=7)
    today = datetime.date.today()
    buttons = []
    for i in range(30):
        day = today + datetime.timedelta(days=i)
        label = format_date_ru(day)
        callback = f"day_{day.isoformat()}"
        buttons.append(InlineKeyboardButton(label, callback_data=callback))
    markup.add(*buttons)
    return markup

# ========================
# Выбор даты для замера
# ========================
def handle_day_selection(call):
    bot.answer_callback_query(call.id)
    user_id = call.message.chat.id
    date_iso = call.data[4:]
    date_obj = datetime.date.fromisoformat(date_iso)
    formatted_date = format_date_ru(date_obj)

    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = KeyboardButton("Отправить номер телефона", request_contact=True)
    markup.add(btn)

    user_state[user_id] = {"type": "measure", "date": date_iso}

    bot.send_message(
        user_id,
        f"Вы выбрали день: *{formatted_date}*\nОставьте номер телефона для записи на замер:",
        parse_mode="Markdown",
        reply_markup=markup
    )

# ========================
# Обработка сообщений (вопросы и телефон)
# ========================
@bot.message_handler(content_types=["text", "contact"])
def process_messages(msg):
    user_id = msg.chat.id
    state = user_state.get(user_id)

    if state is None:
        return

    # --- Запись на замер ---
    if isinstance(state, dict) and state.get("type") == "measure":
        phone = msg.contact.phone_number if msg.contact else msg.text
        date = state["date"]
        bot.send_message(ADMIN_ID, f"📅 *Запись на замер*\nДата: {date}\nТелефон: {phone}", parse_mode="Markdown")
        bot.send_message(user_id, "Спасибо! Мы свяжемся с вами для подтверждения.", reply_markup=ReplyKeyboardRemove())
        user_state.pop(user_id, None)
        return

    # --- Заявка на мебель ---
    if isinstance(state, int):
        step = state
        user_answers.setdefault(user_id, []).append(msg.text)
        next_step = step + 1

        if next_step < len(questions):
            user_state[user_id] = next_step
            bot.send_message(user_id, questions[next_step])
        else:
            # Последний вопрос -> просим телефон
            user_state[user_id] = "phone_for_request"
            markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            btn = KeyboardButton("Отправить номер телефона", request_contact=True)
            markup.add(btn)
            bot.send_message(user_id, "Теперь оставьте номер телефона:", reply_markup=markup)
        return

    # --- Телефон для заявки ---
    if state == "phone_for_request":
        phone = msg.contact.phone_number if msg.contact else msg.text
        info = user_answers.get(user_id, [])
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
        user_state.pop(user_id, None)
        user_answers.pop(user_id, None)

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
