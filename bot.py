import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = "8459688522:AAGWJLK3uEs2cqmXsOrUz0oIaGGK1beqtw8"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --------- STATES ---------
class Form(StatesGroup):
    kitchen_type = State()
    room_type = State()
    size = State()
    contact = State()

# --------- START ---------
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(
        "Здравствуйте! 👋\n"
        "Я бот компании по изготовлению кухонь.\n"
        "Помогу подобрать вариант и записаться на замер.\n\n"
        "Какую кухню вы планируете: прямую, Г-образную или П-образную?"
    )
    await Form.kitchen_type.set()

# --------- Q1 ---------
@dp.message_handler(state=Form.kitchen_type)
async def process_kitchen_type(message: types.Message, state: FSMContext):
    await state.update_data(kitchen_type=message.text)
    await message.answer("Для какого помещения планируете кухню — квартира или дом?")
    await Form.room_type.set()

# --------- Q2 ---------
@dp.message_handler(state=Form.room_type)
async def process_room_type(message: types.Message, state: FSMContext):
    await state.update_data(room_type=message.text)
    await message.answer("Подскажите, пожалуйста, примерную длину кухни?")
    await Form.size.set()

# --------- Q3 ---------
@dp.message_handler(state=Form.size)
async def pro
