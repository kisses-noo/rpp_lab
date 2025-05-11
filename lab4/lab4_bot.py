import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv 

load_dotenv() 

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s', 
                    filename='bot.log', filemode='a', encoding='utf-8')

# Получение токена из переменных окружения
bot_token = os.getenv('API_TOKEN')

# Инициализация бота и диспетчера
bot = Bot(token=bot_token)
dp = Dispatcher()

# Словарь для хранения валют и их курсов
currencies = {}

# Состояния FSM
class CurrencyStates(StatesGroup):
    waiting_for_currency_name = State()
    waiting_for_currency_rate = State()
    waiting_for_currency_to_convert = State()
    waiting_for_amount = State()

# Обработчик команды /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    logging.info(f"Команда /start от пользователя {message.from_user.id}")
    await message.answer(
        "Привет! Я бот для конвертации валют.\n"
        "Доступные команды:\n"
        "/save_currency - сохранить курс валюты\n"
        "/convert - конвертировать валюту в рубли\n"
        "/list_currencies - показать список сохраненных валют"
    )

# Обработчик команды /save_currency
@dp.message(Command("save_currency"))
async def save_currency_command(message: types.Message, state: FSMContext):
    logging.info(f"Пользователь {message.from_user.id} вызвал команду /save_currency")
    await message.answer("Введите название валюты (например, USD, EUR):")
    await state.set_state(CurrencyStates.waiting_for_currency_name)

# Обработчик ввода названия валюты
@dp.message(CurrencyStates.waiting_for_currency_name)
async def process_currency_name(message: types.Message, state: FSMContext):
    currency_name = message.text.upper()
    await state.update_data(currency_name=currency_name)
    logging.info(f"Пользователь {message.from_user.id} ввел название валюты: {currency_name}")
    await message.answer(f"Введите курс {currency_name} к рублю (например, 90.5):")
    await state.set_state(CurrencyStates.waiting_for_currency_rate)

# Обработчик ввода курса валюты
@dp.message(CurrencyStates.waiting_for_currency_rate)
async def process_currency_rate(message: types.Message, state: FSMContext):
    try:
        rate = float(message.text.replace(",", "."))
        if rate <= 0:
            raise ValueError("Курс должен быть положительным числом")
        
        data = await state.get_data()
        currency_name = data['currency_name']
        
        # Сохраняем валюту в словарь
        currencies[currency_name] = rate
        logging.info(f"Курс {currency_name} сохранен: {rate} руб. от пользователя {message.from_user.id}.")
        await message.answer(f"Курс {currency_name} сохранен: {rate} руб.")
        await state.clear()
    except ValueError:
        logging.error(f"Ошибка ввода курса от пользователя {message.from_user.id}: {message.text}")
        await message.answer("Пожалуйста, введите корректное число для курса (например, 90.5)")

# Обработчик команды /convert
@dp.message(Command("convert"))
async def convert_command(message: types.Message, state: FSMContext):
    logging.info(f"Пользователь {message.from_user.id} вызвал команду /convert")
    if not currencies:
        await message.answer("Нет сохраненных валют. Сначала используйте /save_currency")
        return
    
    await message.answer("Введите название валюты для конвертации:")
    await state.set_state(CurrencyStates.waiting_for_currency_to_convert)

# Обработчик ввода валюты для конвертации
@dp.message(CurrencyStates.waiting_for_currency_to_convert)
async def process_currency_to_convert(message: types.Message, state: FSMContext):
    currency_name = message.text.upper()
    if currency_name not in currencies:
        logging.warning(f"Пользователь {message.from_user.id} ввел некорректную валюту: {currency_name}")
        await message.answer(f"Валюта {currency_name} не найдена. Введите другую валюту.")
        return
    
    await state.update_data(currency_name=currency_name)
    await message.answer(f"Введите сумму в {currency_name} для конвертации в рубли:")
    await state.set_state(CurrencyStates.waiting_for_amount)

# Обработчик ввода суммы для конвертации
@dp.message(CurrencyStates.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        if amount <= 0:
            raise ValueError("Сумма должна быть положительным числом")
        
        data = await state.get_data()
        currency_name = data['currency_name']
        rate = currencies[currency_name]
        
        result = amount * rate
        logging.info(f"Конвертация: {amount} {currency_name} = {result:.2f} руб. от пользователя {message.from_user.id}.")
        await message.answer(
            f"{amount} {currency_name} = {result:.2f} руб.\n"
            f"Курс: 1 {currency_name} = {rate} руб."
        )
        await state.clear()
    except ValueError:
        logging.error(f"Ошибка ввода суммы от пользователя {message.from_user.id}: {message.text}")
        await message.answer("Пожалуйста, введите корректное число для суммы")

# Обработчик команды /list_currencies
@dp.message(Command("list_currencies"))
async def list_currencies_command(message: types.Message):
    logging.info(f"Пользователь {message.from_user.id} вызвал команду /list_currencies")
    if not currencies:
        await message.answer("Нет сохраненных валют.")
        return
    
    response = "Сохраненные валюты и их курсы:\n"
    for currency, rate in currencies.items():
        response += f"- {currency}: {rate} руб.\n"
    
    await message.answer(response)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
