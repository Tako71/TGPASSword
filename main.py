import random
import string
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor

BOT_TOKEN = "6564194460:AAEcT_DveOivJIhwTGMBLrDNrBDDrcYTnLw"

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()  # Создаем экземпляр MemoryStorage
dp = Dispatcher(bot, storage=storage)

class CustomPasswordState(StatesGroup):
    waiting_for_code_word = State()
    waiting_for_number = State()
    waiting_for_complexity = State()

class PasswordGenerator:
    def generate_strong_password(self):
        length = random.randint(12, 16)
        characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(random.choice(characters) for _ in range(length))
        return password

def calculate_password_strength(password):
    if len(password) < 8:
        return "Слабый"
    elif len(password) < 12:
        return "Средний"
    else:
        return "Надежный"

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    random_password_btn = types.KeyboardButton("Случайный пароль")
    custom_password_btn = types.KeyboardButton("Пароль по вводным данным")
    markup.add(random_password_btn, custom_password_btn)
    await message.answer("Привет! Хотите создать пароль по вводным данным или случайный пароль?", reply_markup=markup)

@dp.message_handler(lambda message: message.text.lower() == "случайный пароль")
async def generate_random_password(message: types.Message):
    password_generator = PasswordGenerator()
    password = password_generator.generate_strong_password()
    await message.answer(f"Ваш случайный надежный пароль: {password}")

@dp.message_handler(lambda message: message.text.lower() == "пароль по вводным данным")
async def generate_custom_password_step1(message: types.Message):
    await message.answer("Введите кодовое слово:")
    await CustomPasswordState.waiting_for_code_word.set()

@dp.message_handler(state=CustomPasswordState.waiting_for_code_word)
async def generate_custom_password_step2(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['code_word'] = message.text
    await message.answer("Введите любое число:")
    await CustomPasswordState.next()

@dp.message_handler(state=CustomPasswordState.waiting_for_number)
async def generate_custom_password_step3(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['number'] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    weak_btn = types.KeyboardButton("Слабый")
    medium_btn = types.KeyboardButton("Средний")
    strong_btn = types.KeyboardButton("Сложный")
    markup.add(weak_btn, medium_btn, strong_btn)
    await message.answer("Выберите сложность пароля:", reply_markup=markup)
    await message.answer("Отправьте /cancel чтобы отменить.")
    await CustomPasswordState.next()

@dp.message_handler(lambda message: message.text in ["Слабый", "Средний", "Сложный"], state=CustomPasswordState.waiting_for_complexity)
async def generate_custom_password_step4(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        code_word = data['code_word']
        number = data['number']

    complexity = message.text
    await state.finish()

    if complexity == "Слабый":
        password = f"{code_word}{number}"
    elif complexity == "Средний":
        password = f"{code_word}{number}{''.join(random.choices(string.ascii_letters, k=4))}"
    else:
        password = f"{code_word}{number}{''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=8))}"

    strength = calculate_password_strength(password)
    await message.answer(f"Ваш пароль: {password}\nОценка надежности: {strength}")

if __name__ == '__main__':
    dp.middleware.setup(LoggingMiddleware())
    executor.start_polling(dp, skip_updates=True)
