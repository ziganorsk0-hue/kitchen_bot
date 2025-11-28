import os
from flask import Flask, request
import telebot

# Токен бота из переменной окружения
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN не задан!")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ============================
# Временный обработчик для получения ID группы
# ============================
@bot.message_handler(func=lambda msg: True)
def show_group_id(message):
    # Печатаем все данные о чате
    print("Сообщение пришло в чат:", message.chat)
    
    # Если это группа или супергруппа
    if message.chat.type in ["group", "supergroup"]:
        print("===== GROUP ID =====")
        print(message.chat.id)  # <-- здесь появится ID в логах Render
        bot.send_message(message.chat.id, "Бот видит группу! Проверьте логи Render для ID.")

# ============================
# Webhook для Render
# ============================
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
