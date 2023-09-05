import os
from dotenv import load_dotenv
import asyncio
from aiogram import Dispatcher, Bot, types
from aiogram.utils import executor
from aiogram.types import InputFile

load_dotenv(".env")
bot_api_key = os.environ.get("BOT_API_KEY", default=None)

bot = Bot(bot_api_key)
dp = Dispatcher(bot)

commands = ['/start', '/find', '/continue', '/allin']

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    start_message = "Ты гей! START" 
    await bot.send_message(message.from_user.id, start_message)

@dp.message_handler(commands=['continue'])
async def process_start_command(message: types.Message):
    start_message = "Ты гей! CONTINUE"
    await bot.send_message(message.from_user.id, start_message)


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    start_message = "Ты гей! ALLIN"
    await bot.send_message(message.from_user.id, start_message)


@dp.message_handler()
async def process_other_messages(message: types.Message):
    start_message = "Ты гей! OTHER MESSAGE"
    await bot.send_message(message.from_user.id, start_message)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates = True)
