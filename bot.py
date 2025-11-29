import os
import sys
from flask import Flask, request
import telebot

# ========================
# Переменные окружения
# ========================
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")  # только домен

if not TOKEN or not ADMIN_ID or not RENDER_URL:
    print("❌ Ошибка: убедитесь, что заданы TELEGRAM_TOKEN, ADMIN_ID и RENDER_EXTERNAL_URL")
    sys.exit(1)

ADMIN_ID = int(ADMIN_ID)
WEBHOOK_URL = f"https://{RENDER_URL}/{TOKEN}"
print(f"✅ WEBHOOK_URL: {WEBHOOK_URL}")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ========================
# Вопросы для пользователя
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
# /start
# ========================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_state[user_id] = 0
    user_answers[user_id] = []
    bot.send_message(user_id, "Здравствуйте! 👋 Давайте уточним несколько моментов.")
    bot.send_message(user_id, questions[0])

# ========================
# Логирование сообщений
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
# Логика личных сообщений
# ========================
def process_private(message):
    user_id = message.chat.id

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

    bot.send_message(ADMIN_ID, text, parse_mode="Markdown")
    bot.send_message(user_id, "Спасибо! Я передал заявку мастеру.",
                     reply_markup=telebot.types.ReplyKeyboardRemove())

    user_state.pop(user_id)
    user_answers.pop(user_id)

# ========================
# Настройка webhook
# ========================
bot.remove_webhook()
try:
    bot.set_webhook(url=WEBHOOK_URL)
    print("✅ Webhook установлен успешно!")
except Exception as e:
    print("❌ Ошибка при установке webhook:", e)
    sys.exit(1)

# ========================
# Flask маршруты
# ========================
@app.route(f"/{TOKEN}", methods=['POST'])
def receive_update():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

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
