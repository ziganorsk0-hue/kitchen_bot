import sys
import os
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import datetime
import calendar

# ========================
# Переменные окружения
# ========================
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")
WEBHOOK_URL = f"{RENDER_URL}/{TOKEN}"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_state = {}
user_answers = []

# ========================
# Вопросы пользователя
# ========================
questions = [
    "1️⃣ Какую мебель планируете заказать?",
    "2️⃣ В каком стиле хотите?"
]

# ========================
# Главное меню
# ========================
def send_main_menu(user_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📅 Записаться на замер", callback_data="measure"))
    markup.add(InlineKeyboardButton("📝 Оставить заявку", callback_data="start_request"))
    markup.add(InlineKeyboardButton("ℹ️ О компании", callback_data="about"))
    bot.send_message(user_id, "Выберите действие:", reply_markup=markup)

# ========================
# О компании
# ========================
@bot.callback_query_handler(func=lambda call: call.data == "about")
def about(call):
    bot.answer_callback_query(call.id)
    text = (
        "Привет! 👋\n"
        "Я Павел, частный мастер по изготовлению корпусной мебели с 2006 года.\n"
        "Реализую любые проекты по вашим размерам и пожеланиям.\n"
        "Оставьте заявку, и я скоро свяжусь с вами для обсуждения деталей."
    )
    bot.send_message(call.message.chat.id, text)

# ========================
# Заявка по вопросам
# ========================
@bot.callback_query_handler(func=lambda
