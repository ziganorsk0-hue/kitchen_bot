import os
import telebot

# === Чтение токена и ID администратора из переменных окружения ===
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Проверка на случай, если токен не установлен
if not TOKEN:
    raise ValueError("Ошибка: переменная окружения TELEGRAM_TOKEN не задана!")

bot = telebot.TeleBot(TOKEN)

# === Состояние пользователей ===
user_state = {}    # текущий шаг опроса
user_answers = {}  # ответы пользователя

# === Вопросы для клиента ===
questions = [
    "1️⃣ Какую мебель планируете заказать? (Кухня, шкаф, гардеробная, тумба и т.д.)",
    "2️⃣ В каком стиле хотите? (современный, классический, минимализм...)",
    "3️⃣ На какой стадии ремонт?",
    "4️⃣ На какой примерно бюджет ориентируетесь?"
]

# === Старт бота ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_state[user_id] = 0
    user_answers[user_id] = []

    bot.send_message(
        user_id,
        "Здравствуйте! 👋\n"
        "Вы попали в *Кухни на заказ «Майя»*. Я помогу с расчётом стоимости и консультацией.\n\n"
        "Давайте уточним несколько моментов 👇",
        parse_mode='Markdown'
    )

    bot.send_message(user_id, questions[0])


# === Обработка сообщений ===
@bot.message_handler(func=lambda msg: True)
def handle_answers(message):
    user_id = message.chat.id

    # Если пользователь ещё не начал через /start
    if user_id not in user_state:
        bot.send_message(user_id, "Нажмите /start чтобы начать 😊")
        return

    step = user_state[user_id]

    # === Заполняем ответы на вопросы ===
    if step < len(questions):
        user_answers[user_id].append(message.text)
        step += 1
        user_state[user_id] = step

        if step < len(questions):
            bot.send_message(user_id, questions[step])
            return
        else:
            # Вопросы закончились — спрашиваем телефон
            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            button = telebot.types.KeyboardButton("Отправить номер телефона", request_contact=True)
            markup.add(button)
            bot.send_message(user_id, "Спасибо! 🙌\nПожалуйста, оставьте ваш номер телефона:", reply_markup=markup)
            return

    # === Обработка телефона ===
    if message.contact and message.contact.phone_number:
        phone = message.contact.phone_number
    else:
        phone = message.text  # если ввёл вручную

    info = user_answers[user_id]

    text = (
        "🔔 *Новая заявка!*\n\n"
        f"1. Мебель: {info[0]}\n"
        f"2. Стиль: {info[1]}\n"
        f"3. Ремонт: {info[2]}\n"
        f"4. Бюджет: {info[3]}\n"
        f"📱 Телефон: {phone}\n"
        f"🧍‍♂️ Клиент: @{message.from_user.username if message.from_user.username else 'Не указан'}"
    )

    if ADMIN_ID:
        bot.send_message(ADMIN_ID, text, parse_mode='Markdown')

    bot.send_message(
        user_id,
        "Спасибо! 🙏 Я передал заявку мастеру. В ближайшее время вам перезвонят.",
        reply_markup=telebot.types.ReplyKeyboardRemove()
    )

    # Очистка состояния
    user_state.pop(user_id)
    user_answers.pop(user_id)


# === Запуск бота ===
bot.infinity_polling()
# Удаляем webhook, чтобы можно было использовать polling
bot.remove_webhook()
bot.infinity_polling()
