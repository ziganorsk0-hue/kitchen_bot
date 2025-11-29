import os
from flask import Flask, request
import telebot

# ========================
# Настройки
# ========================
TOKEN = os.getenv("8459688522:AAGWJLK3uEs2cqmXsOrUz0oIaGGK1beqtw8")  # токен бота
ADMIN_ID = int(os.getenv("-1003493427992", "0"))  # ID администратора
RENDER_URL = os.getenv(") https://kitchen-bot-ou9m.onrender.com/123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
 # публичный домен Render

if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN не задан!")
if not RENDER_URL:
    raise ValueError("RENDER_EXTERNAL_URL не задан!")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ========================
# Вопросы для опроса
# ========================
questions = [
    "1️⃣ Какую мебель планируете заказать?",
    "2️⃣ В каком стиле хотите?",
    "3️⃣ На какой стадии ремонт?",
    "4️⃣ На какой примерно бюджет ориентируетесь?"
]

user_state = {}
user_answers = {}

# ========================
# Команда /start
# ========================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_state[user_id] = 0
    user_answers[user_id] = []
    bot.send_message(user_id, "Здравствуйте! 👋 Давайте уточним несколько моментов.")
    bot.send_message(user_id, questions[0])

# ========================
# Лог всех сообщений
# ========================
@bot.message_handler(func=lambda msg: True)
def log_all(msg):
    print("\n=== NEW MESSAGE ===")
    print(f"Chat ID: {msg.chat.id}")
    print(f"Type: {msg.chat.type}")
    print(f"User ID: {msg.from_user.id}")
    print(f"Text: {msg.text}")
    print("==================\n")

    if msg.chat.type == "private":
        process_private(msg)
    elif msg.chat.type in ["group", "supergroup"]:
        bot.send_message(msg.chat.id, "Группу вижу! Посмотрите ID в логах Render.")

# ========================
# Логика для лички
# ========================
def process_private(message):
    user_id = message.chat.id

    if message.text == "/start" and user_id not in user_state:
        user_state[user_id] = 0
        user_answers[user_id] = []
        bot.send_message(user_id, questions[0])
        return

    if user_id not in user_state:
        bot.send_message(user_id, "Нажмите /start, чтобы начать.")
        return

    step = user_state[user_id]

    if step < len(questions):
        user_answers[user_id].append(message.text)
        user_state[user_id] += 1

        if user_state[user_id] < len(questions):
            bot.send_message(user_id, questions[user_state[user_id]])
        else:
            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            btn = telebot.types.KeyboardButton("Отправить номер телефона", request_contact=True)
            markup.add(btn)
            bot.send_message(user_id, "Спасибо! Теперь оставьте номер телефона:", reply_markup=markup)
        return

    phone = message.contact.phone_number if message.contact else message.text
    info = user_answers[user_id]

    text = (
        "🔔 *Новая заявка!* \n\n"
        f"1. Мебель: {info[0]}\n"
        f"2. Стиль: {info[1]}\n"
        f"3. Ремонт: {info[2]}\n"
        f"4. Бюджет: {info[3]}\n"
        f"📱 Телефон: {phone}\n"
        f"🧍 Клиент: @{message.from_user.username if message.from_user.username else 'Не указан'}"
    )

    if ADMIN_ID != 0:
        bot.send_message(ADMIN_ID, text, parse_mode="Markdown")

    bot.send_message(user_id, "Спасибо! Я передал заявку мастеру.",
                     reply_markup=telebot.types.ReplyKeyboardRemove())

    user_state.pop(user_id)
    user_answers.pop(user_id)

# ========================
# Настройка webhook
# ========================
WEBHOOK_URL = f"https://{RENDER_URL}/{TOKEN}"

bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

# ========================
# Flask маршруты
# ========================
@app.route(f"/{TOKEN}", methods=['POST'])
def receive_update():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# GET маршрут для проверки в браузере
@app.route(f"/{TOKEN}", methods=['GET'])
def test_webhook():
    return "Webhook OK", 200

@app.route("/")
def index():
    return "Bot is running", 200

# ========================
# Запуск Flask
# ========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
