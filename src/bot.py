import asyncio
import os
import random
import re
from asyncio import Lock

import pandas as pd
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.storage import FSMContext
from aiogram.types import InputFile
from aiogram.utils import executor
from dotenv import load_dotenv

load_dotenv(".env")
bot_api_key = os.environ.get("BOT_API_KEY", default=None)

bot = Bot(bot_api_key)
dp = Dispatcher(bot=bot, storage=MemoryStorage())


# available_commands = ['/start', '/find', '/random', '/allin']

lock = Lock()

# Class for bot states management


class RegisterMessages(StatesGroup):
    await_name = State()


keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
buttons = ["Найти модель", "Показать случайную модель"]
keyboard.add(*buttons)


@dp.message_handler(commands=["start"])
async def process_start_command(message: types.Message, state=None):
    start_message = "Добро пожаловать к NotOnlyFansBot!\nЗдесь ты можешь найти почти любую OnlyFans модель и скачать весь материал по ней/нему.\nПожалуйста, воспользуйся командами для начала"
    await bot.send_message(message.from_user.id, start_message, reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Показать случайную модель")
@dp.message_handler(commands=["random"], state=RegisterMessages.await_name)
@dp.message_handler(commands=["random"], state=None)
async def process_start_command(message: types.Message, state: FSMContext):
    message.text = random.choice(pd.read_csv(DATABASE)["Model"].to_list())
    await RegisterMessages.await_name.set()
    await reg_name(message=message, state=state)


@dp.message_handler(lambda message: message.text == "Найти модель")
@dp.message_handler(commands=["find"], state=None)
async def process_start_command(message: types.Message):
    await bot.send_message(message.from_user.id, "Введи ник модели на OnlyFans: ")
    await RegisterMessages.await_name.set()


@dp.message_handler(content_types="text", state=RegisterMessages.await_name)
async def reg_name(message: types.Message, state: FSMContext):
    async with lock:
        db = pd.read_csv(DATABASE)
        if message.text.lower() in db["Model"].to_list():
            bio = str(db[db.Model == message.text.lower()]["Bio"].values[0])
            photos = str(db[db.Model == message.text.lower()]["Photos"].values[0])
            videos = str(db[db.Model == message.text.lower()]["Videos"].values[0])
            img = str(db[db.Model == message.text.lower()]["Img_ref"].values[0])

            if img == "nan":
                img = "https://leakedzone.com/asset/images/no-avatar.jpg"
            if photos == "nan":
                photos = "Unknown yet"
            if videos == "nan":
                videos = "Unknown yet"
            if bio == "nan":
                bio = "Unknown yet"

        else:
            await bot.send_message(
                message.from_user.id,
                "Модель не найдена. Попробуй снова",
                reply_markup=keyboard,
            )
            await state.finish()
            return

        bio = bio.replace("\r", "")

        while "\n\n" in bio:
            bio = bio.replace("\n\n", "\n")

        bio = bio.strip("<br>")
        bio = bio.replace("<br>", "")
        bio = bio.strip()

        if len(bio) >= 200:
            bio = bio[:200]

        new_message = f"Модель: {message.text.lower()}\n\nКоличество фото: {photos}\nКоличество видео: {videos}\n\nТекст профиля:\n{bio}"
        await bot.send_photo(
            message.from_user.id, photo=img, caption=new_message, reply_markup=keyboard
        )

        await state.finish()


@dp.message_handler(commands=["allin"])
async def process_start_command(message: types.Message, state=None):
    start_message = "В разработке..."
    await bot.send_message(message.from_user.id, start_message, reply_markup=keyboard)


@dp.message_handler()
async def process_other_messages(message: types.Message, state=None):
    start_message = "Пожалуйста, воспользуйся командами для работы с ботом"
    await bot.send_message(message.from_user.id, start_message, reply_markup=keyboard)


if __name__ == "__main__":
    executor.start_polling(dispatcher=dp, skip_updates=True)
