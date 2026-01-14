import asyncio
import os
import logging
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Инициализация бота
bot = Bot(token=os.getenv('API_TOKEN'))
dp = Dispatcher()

# Обработчик команды /start 
@dp.message(Command("start"))
async def start_command(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Получить данные", callback_data="get_data")]
    ])
    await message.answer("Нажмите кнопку для получения данных:", reply_markup=keyboard)

# Обработчик нажатия инлайн кнопки
@dp.callback_query(F.data == "get_data")
async def process_callback(callback: types.CallbackQuery):
    try:
        response = requests.get('http://localhost:5000/data')
        if response.status_code == 200:
            data = response.json()
            await callback.message.answer(f"Данные с сервера: {data['message']}")
        else:
            await callback.message.answer("Ошибка при получении данных")
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await callback.message.answer("Сервер недоступен")
    await callback.answer()

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())