import asyncio
import os
import logging
import psycopg2 
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s', 
                    filename='bot.log', 
                    filemode='a', 
                    encoding='utf-8')

# Получение токена из переменных окружения
bot_token = os.getenv('API_TOKEN')
db_host = os.getenv('DB_HOST', 'localhost')
db_name = os.getenv('DB_NAME', 'currency_bot')
db_user = os.getenv('DB_USER', 'postgres')
db_password = os.getenv('DB_PASSWORD', 'postgres')

# Инициализация бота и диспетчера
bot = Bot(token=bot_token)
dp = Dispatcher()

# Состояния FSM
class CurrencyStates(StatesGroup):
    waiting_for_currency_name = State()
    waiting_for_currency_rate = State()
    waiting_for_currency_to_delete = State()
    waiting_for_currency_to_update = State()
    waiting_for_new_rate = State()
    waiting_for_currency_to_convert = State()
    waiting_for_amount = State()

# Функции для работы с базой данных
def create_tables():
    try:
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS currencies (
                id SERIAL PRIMARY KEY,
                currency_name VARCHAR(10) UNIQUE NOT NULL,
                rate NUMERIC(10, 2) NOT NULL
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id SERIAL PRIMARY KEY,
                chat_id VARCHAR(20) UNIQUE NOT NULL
            )
        """)
        
        conn.commit()
        logging.info("Таблицы успешно созданы")
    except Exception as e:
        logging.error(f"Ошибка при создании таблиц: {e}")
    finally:
        if conn:
            conn.close()

# Проверка, является ли пользователь администратором
async def is_admin(chat_id):
    try:
        response = requests.get(f'http://localhost:5003/is_admin/{chat_id}')
        if response.status_code == 200:
            return response.json().get('is_admin', False)
        return False
    except Exception as e:
        logging.error(f"Ошибка при проверке администратора: {e}")
        return False

# Обработчики команд
@dp.message(Command("start"))
async def start_command(message: types.Message):
    logging.info(f"Пользователь {message.from_user.id} вызвал команду /start")
    
    if await is_admin(str(message.from_user.id)):
        commands = (
            "/start - Начало работы\n"
            "/manage_currency - Управление валютами (админ)\n"
            "/get_currencies - Список валют\n"
            "/convert - Конвертировать валюту"
        )
    else:
        commands = (
            "/start - Начало работы\n"
            "/get_currencies - Список валют\n"
            "/convert - Конвертировать валюту"
        )
    
    await message.answer(
        f"Привет! Я бот для работы с валютами.\n\n"
        f"Доступные команды:\n{commands}"
    )

@dp.message(Command("manage_currency"))
async def manage_currency_command(message: types.Message):
    logging.info(f"Пользователь {message.from_user.id} вызвал команду /manage_currency")
    
    if not await is_admin(str(message.from_user.id)):
        await message.answer("Нет доступа к команде")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добавить валюту", callback_data="add_currency")],
        [InlineKeyboardButton(text="Удалить валюту", callback_data="delete_currency")],
        [InlineKeyboardButton(text="Изменить курс", callback_data="update_currency")]
    ])
    
    await message.answer(
        "Управление валютами:",
        reply_markup=keyboard
    )

# Обработчик для нажатия кнопки "Добавить валюту"
@dp.callback_query(F.data == "add_currency")
async def add_currency_callback(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("У вас нет доступа для управления валютами.")
        return
    
    await callback.message.answer("Введите название валюты:")
    await state.set_state(CurrencyStates.waiting_for_currency_name)
    await callback.answer()

# Обработчик для ожидания ввода названия валюты
@dp.message(CurrencyStates.waiting_for_currency_name)
async def process_currency_name(message: types.Message, state: FSMContext):
    currency_name = message.text.upper()
    await state.update_data(currency_name=currency_name)
    await message.answer(f"Введите курс {currency_name} к рублю (например, 90.5):")
    await state.set_state(CurrencyStates.waiting_for_currency_rate)

# Обработчик для ожидания ввода курса валюты
@dp.message(CurrencyStates.waiting_for_currency_rate)
async def process_currency_rate(message: types.Message, state: FSMContext):
    try:
        rate = float(message.text.replace(",", "."))
        if rate <= 0:
            raise ValueError("Курс должен быть положительным числом")

        data = await state.get_data()
        currency_name = data['currency_name']

        response = requests.post('http://localhost:5001/load', json={
            'currency_name': currency_name,
            'rate': rate
        })

        if response.status_code == 200:
            await message.answer(f"Валюта {currency_name} успешно добавлена")
        else:
            error = response.json().get('error', 'Неизвестная ошибка')
            await message.answer(f"Ошибка: {error}")

        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число для курса (например, 90.5)")

# Обработчик для нажатия кнопки "Удалить валюту"
@dp.callback_query(F.data == "delete_currency")
async def delete_currency_callback(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("У вас нет доступа для управления валютами.")
        return
    
    await callback.message.answer("Введите название валюты для удаления:")
    await state.set_state(CurrencyStates.waiting_for_currency_to_delete)
    await callback.answer()

# Обработчик для ожидания ввода названия валюты для удаления
@dp.message(CurrencyStates.waiting_for_currency_to_delete)
async def process_currency_to_delete(message: types.Message, state: FSMContext):
    currency_name = message.text.upper()
    
    response = requests.post('http://localhost:5001/delete', json={
        'currency_name': currency_name
    })
    
    if response.status_code == 200:
        await message.answer(f"Валюта {currency_name} успешно удалена")
    else:
        error = response.json().get('error', 'Неизвестная ошибка')
        await message.answer(f"Ошибка: {error}")
    
    await state.clear()

# Обработчик для нажатия кнопки "Изменить курс"
@dp.callback_query(F.data == "update_currency")
async def update_currency_callback(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("У вас нет доступа для управления валютами.")
        return
    
    await callback.message.answer("Введите название валюты для изменения курса:")
    await state.set_state(CurrencyStates.waiting_for_currency_to_update)
    await callback.answer()

# Обработчик для ожидания ввода названия валюты для изменения курса
@dp.message(CurrencyStates.waiting_for_currency_to_update)
async def process_currency_to_update(message: types.Message, state: FSMContext):
    currency_name = message.text.upper()
    await state.update_data(currency_name=currency_name)
    await message.answer(f"Введите новый курс {currency_name} к рублю:")
    await state.set_state(CurrencyStates.waiting_for_new_rate)

# Обработчик для ожидания ввода нового курса валюты
@dp.message(CurrencyStates.waiting_for_new_rate)
async def process_new_rate(message: types.Message, state: FSMContext):
    try:
        new_rate = float(message.text.replace(",", "."))
        if new_rate <= 0:
            raise ValueError("Курс должен быть положительным числом")

        data = await state.get_data()
        currency_name = data['currency_name']

        response = requests.post('http://localhost:5001/update_currency', json={
            'currency_name': currency_name,
            'new_rate': new_rate
        })

        if response.status_code == 200:
            await message.answer(f"Курс {currency_name} успешно обновлен: {new_rate} руб.")
        else:
            error = response.json().get('error', 'Неизвестная ошибка')
            await message.answer(f"Ошибка: {error}")

        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число для курса (например, 90.5)")

# Обработчик для команды /get_currencies
@dp.message(Command("get_currencies"))
async def get_currencies_command(message: types.Message):
    logging.info(f"Пользователь {message.from_user.id} вызвал команду /get_currencies")
    
    response = requests.get('http://localhost:5002/currencies')
    if response.status_code == 200:
        currencies = response.json()
        if not currencies:
            await message.answer("Нет сохраненных валют.")
            return
        
        response_message = "Список валют и их курсов к рублю:\n\n"
        for currency in currencies:
            response_message += f"- {currency[0]}: {currency[1]} руб.\n"
        
        await message.answer(response_message)
    else:
        await message.answer("Ошибка при получении списка валют.")

# Обработчик для команды /convert
@dp.message(Command("convert"))
async def convert_command(message: types.Message, state: FSMContext):
    logging.info(f"Пользователь {message.from_user.id} вызвал команду /convert")
    await message.answer("Введите название валюты для конвертации:")
    await state.set_state(CurrencyStates.waiting_for_currency_to_convert)

# Обработчик для ожидания ввода валюты для конвертации
@dp.message(CurrencyStates.waiting_for_currency_to_convert)
async def process_currency_to_convert(message: types.Message, state: FSMContext):
    currency_name = message.text.upper()
    await state.update_data(currency_name=currency_name)
    await message.answer("Введите сумму для конвертации:")
    await state.set_state(CurrencyStates.waiting_for_amount)

# Обработчик для ожидания ввода суммы для конвертации
@dp.message(CurrencyStates.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        if amount <= 0:
            raise ValueError("Сумма должна быть положительным числом")

        data = await state.get_data()
        currency_name = data['currency_name']

        response = requests.get('http://localhost:5002/convert', params={
            'currency_name': currency_name,
            'amount': amount
        })

        if response.status_code == 200:
            result = response.json()
            await message.answer(
                f"{amount} {currency_name} = {result['converted_amount']:.2f} руб.\n"
                f"Курс: 1 {currency_name} = {result['rate']} руб."
            )
        else:
            error = response.json().get('error', 'Неизвестная ошибка')
            await message.answer(f"Ошибка: {error}")

        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число для суммы")
    finally:
        await state.clear()

# Запуск бота
async def main():
    create_tables() # Создаем таблицы при запуске бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())