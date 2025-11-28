import os
from flask import Flask, request
import telebot

# ========================
# Настройки
# ========================
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not TOKEN:
    raise ValueError("Ошибка: переменная окружения TELEGRAM_TOKEN не задана!")

bot = telebot.TeleBot(TOKEN)

# ========================
# ЛОГИРОВАНИЕ ВСЕХ ВХОДЯЩИХ СООБЩЕНИЙ (добавил!)
# ========================
@bot.middleware_handler(update_types=['message'])
def log_updates(bot_instance, message):
    print("\n========== NEW UPDATE ==========")
    print(f"Chat ID: {message.chat.id}")
    print(f"Chat type: {message.chat.type}")
    print(f"User ID: {message.from_user.id}")
    print(f"Text: {message.text}")
    print("================================\n")


# ========================
# ВРЕМЕННЫЙ обработчик для получения ID группы
# ========================
@bot.message_handler(func=lambda msg: msg.chat.type in ["group", "supergroup"])
def get_group_id(message):
    print(f"GROUP ID DETECTED: {message.chat.id}")
    bot.send_message(message.chat.id, "Группу вижу! Проверьте логи Render для ID.")


# ========================
# Основная логика бота
# ========================
user_state = {}
user_answers = {}

questions = [
    "1️⃣ Какую мебель планируете заказать?",
    "2️⃣ В каком стиле хотите?",
    "3️⃣ На какой стадии ремонт?",
    "4️⃣ На какой примерно бюджет ориентируетесь?"
]

@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type != "private":
        return

    user_id = message.chat.id
    user_state[user_id] = 0
    user_answers[user_id] = []

    bot.send_message(user_id, "Здравствуйте! 👋 Давайте уточним несколько моментов.")
    bot.send_message(user_id, questions[0])

@bot.message_handler(func=lambda msg: msg.chat.type == "private")
def handle_answers(message):
    user_id = message.chat.id

    if user_id not in user_state:
        bot.send_message(user_id, "Нажмите /start, чтобы начать.")
        return

    step = user_state[user_id]

    # Сохраняем ответ
    if step < len(questions):
        user_answers[user_id].append(message.text)
        user_state[user_id] += 1

        # Следующий вопрос
        if user_state[user_id] < len(questions):
            bot.send_message(user_id, questions[user_state[user_id]])
            return
        else:
            # Просим номер телефона
            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            btn = telebot.types.KeyboardButton("Отправить номер телефона", request_contact=True)
            markup.add(btn)
            bot.send_message(user_id, "Спасибо! Теперь оставьте номер телефона:", reply_markup=markup)
            return

    # Телефон
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

    bot.send_message(
        user_id,
        "Спасибо! Я передал заявку мастеру.",
        reply_markup=telebot.types.ReplyKeyboardRemove()
    )

    user_state.pop(user_id)
    user_answers.pop(user_id)


# ========================
# Webhook для Render
# ========================
app = Flask(__name__)

bot.remove_webhook()
bot.set_webhook(url=f"https://kitchen-bot-ou9m.onrender.com/{TOKEN}")

@app.route(f"/{TOKEN}", methods=['POST'])
def receive_update():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "Bot is running", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
