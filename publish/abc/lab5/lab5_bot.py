import asyncio
import os
import logging
import psycopg2
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='bot.log',
    filemode='a',
    encoding='utf-8'
)

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
    #Создание таблиц в базе данных
    try:
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )
        cur = conn.cursor()
        
        # Создание таблицы currencies
        cur.execute("""
            CREATE TABLE IF NOT EXISTS currencies (
                id SERIAL PRIMARY KEY,
                currency_name VARCHAR(10) UNIQUE NOT NULL,
                rate NUMERIC(10, 2) NOT NULL
            )
        """)
        
        # Создание таблицы admins
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
def is_admin(chat_id):
    try:
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )
        cur = conn.cursor()
        
        cur.execute("SELECT 1 FROM admins WHERE chat_id = %s", (chat_id,))
        return bool(cur.fetchone())
    except Exception as e:
        logging.error(f"Ошибка при проверке администратора: {e}")
        return False
    finally:
        if conn:
            conn.close()

# Добавление новой валюты
def add_currency(currency_name, rate):
    try:
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )
        cur = conn.cursor()
        
        cur.execute(
            "INSERT INTO currencies (currency_name, rate) VALUES (%s, %s)",
            (currency_name.upper(), rate)
        )
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        logging.warning(f"Валюта {currency_name} уже существует")
        return False
    except Exception as e:
        logging.error(f"Ошибка при добавлении валюты: {e}")
        return False
    finally:
        if conn:
            conn.close()

# Удаление валюты
def delete_currency(currency_name):
    try:
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )
        cur = conn.cursor()
        
        cur.execute(
            "DELETE FROM currencies WHERE currency_name = %s",
            (currency_name.upper(),)
        )
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        logging.error(f"Ошибка при удалении валюты: {e}")
        return False
    finally:
        if conn:
            conn.close()

#Обновление курса валюты
def update_currency_rate(currency_name, new_rate):
    try:
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )
        cur = conn.cursor()
        
        cur.execute(
            "UPDATE currencies SET rate = %s WHERE currency_name = %s",
            (new_rate, currency_name.upper())
        )
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        logging.error(f"Ошибка при обновлении курса: {e}")
        return False
    finally:
        if conn:
            conn.close()

# Получение списка всех валют
def get_all_currencies():
    try:
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )
        cur = conn.cursor()
        
        cur.execute("SELECT currency_name, rate FROM currencies ORDER BY currency_name")
        return cur.fetchall()
    except Exception as e:
        logging.error(f"Ошибка при получении списка валют: {e}")
        return []
    finally:
        if conn:
            conn.close()

# Получение курса валюты
def get_currency_rate(currency_name):
    try:
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )
        cur = conn.cursor()
        
        cur.execute(
            "SELECT rate FROM currencies WHERE currency_name = %s",
            (currency_name.upper(),)
        )
        result = cur.fetchone()
        return result[0] if result else None
    except Exception as e:
        logging.error(f"Ошибка при получении курса валюты: {e}")
        return None
    finally:
        if conn:
            conn.close()

# Обработчики команд
@dp.message(Command("start"))
async def start_command(message: types.Message):
    logging.info(f"Команда /start от пользователя {message.from_user.id}")
    
    if is_admin(str(message.from_user.id)):
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
    
    if not is_admin(str(message.from_user.id)):
        await message.answer("Нет доступа к команде")
        return
    
    # Создаем кнопки
    btn_add = types.InlineKeyboardButton(text="Добавить", callback_data="add_currency")
    btn_delete = types.InlineKeyboardButton(text="Удалить", callback_data="delete_currency")
    btn_update = types.InlineKeyboardButton(text="Изменить курс", callback_data="update_currency")
    
    # Создаем клавиатуру
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [btn_add, btn_delete, btn_update]
    ])
    
    await message.answer(
        "Управление валютами:",
        reply_markup=keyboard
    )

# Обработчик для нажатия кнопки "Добавить валюту"
@dp.callback_query(F.data == "add_currency")
async def add_currency_callback(callback: types.CallbackQuery, state: FSMContext):
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
        
        if add_currency(currency_name, rate):
            await message.answer(f"Валюта: {currency_name} успешно добавлена")
        else:
            await message.answer(f"Валюта {currency_name} уже существует")
        
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число для курса (например, 90.5)")

# Обработчик для нажатия кнопки "Удалить валюту"
@dp.callback_query(F.data == "delete_currency")
async def delete_currency_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите название валюты для удаления:")
    await state.set_state(CurrencyStates.waiting_for_currency_to_delete)
    await callback.answer()

# Обработчик для ожидания ввода названия валюты для удаления
@dp.message(CurrencyStates.waiting_for_currency_to_delete)
async def process_currency_to_delete(message: types.Message, state: FSMContext):
    currency_name = message.text.upper()
    
    if delete_currency(currency_name):
        await message.answer(f"Валюта {currency_name} успешно удалена")
    else:
        await message.answer(f"Валюта {currency_name} не найдена")
    
    await state.clear()

# Обработчик для нажатия кнопки "Изменить курс"
@dp.callback_query(F.data == "update_currency")
async def update_currency_callback(callback: types.CallbackQuery, state: FSMContext):
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
        
        if update_currency_rate(currency_name, new_rate):
            await message.answer(f"Курс {currency_name} успешно обновлен: {new_rate} руб.")
        else:
            await message.answer(f"Валюта {currency_name} не найдена")
        
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число для курса (например, 90.5)")

# Обработчик для команды /get_currencies
@dp.message(Command("get_currencies"))
async def get_currencies_command(message: types.Message):
    logging.info(f"Пользователь {message.from_user.id} вызвал команду /get_currencies")
    currencies = get_all_currencies()
    
    if not currencies:
        await message.answer("Нет сохраненных валют.")
        return
    
    response = "Список валют и их курсов к рублю:\n\n"
    for currency, rate in currencies:
        response += f"- {currency}: {rate} руб.\n"
    
    await message.answer(response)

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
    rate = get_currency_rate(currency_name)
    
    if rate is None:
        await message.answer(f"Валюта {currency_name} не найдена. Введите другую валюту.")
        return
    
    await state.update_data(currency_name=currency_name, rate=rate)
    await message.answer(f"Введите сумму в {currency_name} для конвертации в рубли:")
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
        rate = float(data['rate'])
        
        result = amount * rate
        await message.answer(
            f"{amount} {currency_name} = {result:.2f} руб.\n"
            f"Курс: 1 {currency_name} = {rate} руб."
        )
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число для суммы")
    finally:
        await state.clear()

# Запуск бота
async def main():
    create_tables()  # Создаем таблицы при запуске бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
