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
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s', 
                    filename='bot.log', 
                    filemode='a', 
                    encoding='utf-8')

# Инициализация бота
bot = Bot(token=os.getenv('API_TOKEN'))
dp = Dispatcher()

# Состояния FSM
class FinanceStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_operation_type = State()
    waiting_for_amount = State()
    waiting_for_date = State()
    waiting_for_currency = State()
    waiting_for_sort_order = State()

# Подключение к БД
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

# Создание таблиц
def create_tables():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                chat_id BIGINT UNIQUE NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS operations (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL,
                sum NUMERIC(10, 2) NOT NULL,
                chat_id BIGINT NOT NULL,
                type_operation VARCHAR(10) NOT NULL
            )
        """)
        conn.commit()
    except Exception as e:
        logging.error(f"Ошибка при создании таблиц: {e}")
    finally:
        conn.close()

# Проверка регистрации пользователя
async def is_user_registered(chat_id):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE chat_id = %s", (chat_id,))
        return cur.fetchone() is not None
    finally:
        conn.close()

# Обработчик команды /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "Привет! Я бот для учета финансов.\n"
        "Доступные команды:\n"
        "/reg - Регистрация\n"
        "/add_operation - Добавить операцию\n"
        "/operations - Просмотр операций"
    )

# Обработчик команды /reg
@dp.message(Command("reg"))
async def reg_command(message: types.Message, state: FSMContext):
    if await is_user_registered(message.chat.id):
        await message.answer("Вы уже зарегистрированы!")
        return
    
    await message.answer("Введите ваше имя:")
    await state.set_state(FinanceStates.waiting_for_username)

# Обработчик ввода имени
@dp.message(FinanceStates.waiting_for_username)
async def process_username(message: types.Message, state: FSMContext):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (name, chat_id) VALUES (%s, %s)",
            (message.text, message.chat.id)
        )
        conn.commit()
        await message.answer(f"Регистрация завершена, {message.text}!")
    except Exception as e:
        logging.error(f"Ошибка при регистрации: {e}")
        await message.answer("Произошла ошибка при регистрации")
    finally:
        conn.close()
        await state.clear()

# Обработчик команды /add_operation
@dp.message(Command("add_operation"))
async def add_operation_command(message: types.Message, state: FSMContext):
    if not await is_user_registered(message.chat.id):
        await message.answer("Сначала зарегистрируйтесь с помощью /reg")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ДОХОД", callback_data="type_income")],
        [InlineKeyboardButton(text="РАСХОД", callback_data="type_expense")]
    ])
    await message.answer("Выберите тип операции:", reply_markup=keyboard)
    await state.set_state(FinanceStates.waiting_for_operation_type)

# Обработчик выбора типа операции
@dp.callback_query(FinanceStates.waiting_for_operation_type)
async def process_operation_type(callback: types.CallbackQuery, state: FSMContext):
    operation_type = "ДОХОД" if callback.data == "type_income" else "РАСХОД"
    await state.update_data(type_operation=operation_type)
    
    await callback.message.answer("Введите сумму операции в рублях:")
    await state.set_state(FinanceStates.waiting_for_amount)
    await callback.answer()

# Обработчик ввода суммы
@dp.message(FinanceStates.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        if amount <= 0:
            raise ValueError
        await state.update_data(sum=amount)
        await message.answer("Введите дату операции (ГГГГ-ММ-ДД):")
        await state.set_state(FinanceStates.waiting_for_date)
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму")

# Обработчик ввода даты
@dp.message(FinanceStates.waiting_for_date)
async def process_date(message: types.Message, state: FSMContext):
    try:
        datetime.strptime(message.text, "%Y-%m-%d")
        data = await state.get_data()
        
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO operations (date, sum, chat_id, type_operation) VALUES (%s, %s, %s, %s)",
                (message.text, data['sum'], message.chat.id, data['type_operation'])
            )
            conn.commit()
            await message.answer("Операция успешно добавлена!")
        except Exception as e:
            logging.error(f"Ошибка при добавлении операции: {e}")
            await message.answer("Произошла ошибка при добавлении операции")
        finally:
            conn.close()
    except ValueError:
        await message.answer("Введите дату в формате ГГГГ-ММ-ДД")
    finally:
        await state.clear()

# Обработчик команды /operations
@dp.message(Command("operations"))
async def operations_command(message: types.Message, state: FSMContext):
    if not await is_user_registered(message.chat.id):
        await message.answer("Сначала зарегистрируйтесь с помощью /reg")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="RUB", callback_data="RUB")],
        [InlineKeyboardButton(text="EUR", callback_data="EUR")],
        [InlineKeyboardButton(text="USD", callback_data="USD")]
    ])
    await message.answer("Выберите валюту для отображения:", reply_markup=keyboard)
    await state.set_state(FinanceStates.waiting_for_currency)

# Обработчик выбора валюты
@dp.callback_query(FinanceStates.waiting_for_currency)
async def process_currency(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(currency=callback.data)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ПО ВОЗРАСТАНИЮ", callback_data="ASC")],
        [InlineKeyboardButton(text="ПО УБЫВАНИЮ", callback_data="DESC")]
    ])
    await callback.message.answer("Выберите порядок сортировки:", reply_markup=keyboard)
    await state.set_state(FinanceStates.waiting_for_sort_order)
    await callback.answer()

# Обработчик выбора сортировки
@dp.callback_query(FinanceStates.waiting_for_sort_order)
async def process_sort_order(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    currency = data['currency']
    sort_order = callback.data
    
    try:
        # Получаем курс валюты, если нужно
        rate = 1.0
        if currency != "RUB":
            response = requests.get(f"http://localhost:5003/rate?currency={currency}")

            # Проверка статуса ответа и обработка ошибок
            if response.status_code == 500:
                await callback.message.answer("Внутренняя ошибка сервиса. Попробуйте позже.")
                return
            # Если статус другой, то проверяем на успешный ответ
            if response.status_code != 200:
                await callback.message.answer("Не удалось получить курс валюты")
                return
            # Получаем курс из ответа
            rate = response.json().get('rate', 1.0)

        # Получаем операции из БД
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                f"SELECT date, sum, type_operation FROM operations WHERE chat_id = %s ORDER BY date {sort_order}",
                (callback.message.chat.id,)
            )
            operations = cur.fetchall()
            
            if not operations:
                await callback.message.answer("У вас пока нет операций")
                return
            
            # Формируем сообщение
            message_text = f"Ваши операции ({currency}):\n\n"
            for op in operations:
                converted_sum = round(float(op[1]) / rate, 2)
                message_text += f"{op[0]}: {converted_sum} {currency} ({op[2]})\n"
            
            await callback.message.answer(message_text)
        finally:
            conn.close()
    except Exception as e:
        logging.error(f"Ошибка при получении операций: {e}")
        await callback.message.answer("Произошла ошибка при получении операций")
    finally:
        await state.clear()
    await callback.answer()

# Запуск бота
async def main():
    create_tables()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
