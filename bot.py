import telebot
from telebot import types

TOKEN = "ТОКЕН"
bot = telebot.TeleBot(TOKEN)

user_state = {}

START = "start"
ASK_CONTACT = "ask_contact"
ASK_TYPE = "ask_type"
ASK_PROJECT = "ask_project"
ASK_MEASUREMENT = "ask_measurement"

@bot.message_handler(commands=['start'])
def start(message):
    user_state[message.chat.id] = START
    bot.send_message(message.chat.id, 
                     "Здравствуйте! 👋\nЯ помогу вам сделать заказ или расчёт мебели.\n\n"
                     "Как вас зовут?")
    

@bot.message_handler(func=lambda msg: True)
def main_handler(message):
    chat_id = message.chat.id
    state = user_state.get(chat_id, START)

    # --- 1. Имя ---
    if state == START:
        user_state[chat_id] = ASK_CONTACT
        bot.send_message(chat_id, "Приятно познакомиться! 😊\nОставьте, пожалуйста, номер телефона для связи.")
        return

    # --- 2. Контакт ---
    if state == ASK_CONTACT:
        user_state[chat_id] = ASK_TYPE
        bot.send_message(chat_id,
                         "Отлично! 📞\nТеперь подскажите:\n"
                         "Какую мебель хотите заказать? (кухня, шкаф, гардеробная, тумба или другое)")
        return

    # --- 3. Тип мебели ---
    if state == ASK_TYPE:
        user_state[chat_id] = ASK_PROJECT
        bot.send_message(chat_id,
                         "Понял! 😊\nХотите расчёт по готовому проекту или сначала нужен проект от дизайнера?")
        return

    # --- 4. Готовый проект / дизайн ---
    if state == ASK_PROJECT:
        user_state[chat_id] = ASK_MEASUREMENT

        keyboard = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Записаться на замер", callback_data="measure_yes")
        btn2 = types.InlineKeyboardButton("Пока не нужно", callback_data="measure_no")
        keyboard.add(btn1, btn2)

        bot.send_message(chat_id,
                         "Хотите записаться на замер? 📐\nЗамерщик приедет бесплатно, подскажет по проекту и материалам.",
                         reply_markup=keyboard)
        return


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id

    if call.data == "measure_yes":
        bot.send_message(chat_id,
                         "Отлично! 🙌\nМы свяжемся с вами в ближайшее время и согласуем дату замера.")
        user_state[chat_id] = START  # сбрасываем состояние
    elif call.data == "measure_no":
        bot.send_message(chat_id,
                         "Хорошо! Если понадобится — вы всегда можете записаться позже 😊")
        user_state[chat_id] = START  # сброс

# --- Чтобы бот всегда отвечал ---
bot.infinity_polling(skip_pending=True)
