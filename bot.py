import telebot
import os

TOKEN = os.getenv("8459688522:AAGWJLK3uEs2cqmXsOrUz0oIaGGK1beqtw8")
ADMIN_ID = int(os.getenv("927677341", "0"))

bot = telebot.TeleBot(TOKEN)

user_state = {}          # состояние клиента
user_answers = {}        # ответы клиента


questions = [
    "1️⃣ Какую мебель планируете заказать? (Кухня, шкаф, гардеробная, тумба и т.д.)",
    "2️⃣ В каком стиле хотите? (современный, классический, минимализм...)",
    "3️⃣ На какой стадии ремонт?",
    "4️⃣ На какой примерно бюджет ориентируетесь?"
]


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_state[user_id] = 0
    user_answers[user_id] = []

    bot.send_message(
        user_id,
        "Здравствуйте! 👋\n"
        "Вы попали в *Кухни на заказ «Майя»*. Я помогаю с расчётом стоимости и консультацией.\n\n"
        "Давайте уточним несколько моментов 👇"
    )

    bot.send_message(user_id, questions[0])


@bot.message_handler(func=lambda msg: True)
def handle_answers(message):
    user_id = message.chat.id

    # если человек пишет без /start
    if user_id not in user_state:
        bot.send_message(user_id, "Нажмите /start чтобы начать 😊")
        return

    # сохраняем ответ
    step = user_state[user_id]
    user_answers[user_id].append(message.text)

    # если это был последний вопрос
    if step == len(questions) - 1:
        bot.send_message(
            user_id,
            "Спасибо! 🙌\n"
            "Готов предложить варианты. Могу записать вас на бесплатный замер 📏 или провести консультацию.\n\n"
            "Оставьте, пожалуйста, номер телефона."
        )
        user_state[user_id] += 1
        return

    # если вопрос не последний — задаём следующий
    user_state[user_id] += 1
    bot.send_message(user_id, questions[user_state[user_id]])


    # после телефона — отправляем заявку тебе
    if user_state[user_id] == len(questions) + 1:
        phone = message.text
        info = user_answers[user_id]

        text = (
            "🔔 *Новая заявка!*\n\n"
            f"1. Мебель: {info[0]}\n"
            f"2. Стиль: {info[1]}\n"
            f"3. Ремонт: {info[2]}\n"
            f"4. Бюджет: {info[3]}\n"
            f"📱 Телефон: {phone}\n"
            f"🧍‍♂️ Клиент: @{message.from_user.username}"
        )

        if ADMIN_ID:
            bot.send_message(ADMIN_ID, text, parse_mode='Markdown')

        bot.send_message(
            user_id,
            "Спасибо! 🙏 Я передал заявку мастеру. "
            "В ближайшее время вам перезвонят."
        )

        # очищаем состояние
        user_state.pop(user_id)
        user_answers.pop(user_id)


if __name__ == "__main__":
    bot.infinity_polling()
