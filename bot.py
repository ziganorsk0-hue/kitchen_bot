import telebot
from telebot import types

TOKEN = "8459688522:AAGWJLK3uEs2cqmXsOrUz0oIaGGK1beqtw8"
ADMIN_ID = 927677341   # твой Telegram ID

bot = telebot.TeleBot(TOKEN)

user_data = {}   # временное хранилище заявок


# -------------------------------
#  КНОПКИ МЕНЮ
# -------------------------------
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📚 Каталоги")
    kb.add("📝 Оставить заявку")
    return kb


# -------------------------------
#  START
# -------------------------------
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Здравствуйте! 👋
