import typing
from asyncio import Lock

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.storage import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types.web_app_info import WebAppInfo
from aiogram.utils import executor
from core.config import config
from core.logger import logger
from db.database import Database
from db.queries import Queries
from materials_manager import MaterialsManager

# теперь все переменные в дате которые начинаются с _ будут нестираемыми


class GMemoryStorage(MemoryStorage):
    async def reset_state(
        self,
        *,
        chat: typing.Union[str, int, None] = None,
        user: typing.Union[str, int, None] = None,
        with_data: typing.Optional[bool] = True,
    ):
        await self.set_state(chat=chat, user=user, state=None)
        if with_data:
            new_data = {}
            old_data = await self.get_data(chat=chat, user=user)
            for key, value in old_data.items():
                if key.startswith("_"):
                    new_data[key] = value

            await self.set_data(chat=chat, user=user, data=new_data)
        self._cleanup(chat, user)


bot = Bot(config.BOT_API_KEY)
dp = Dispatcher(bot=bot, storage=GMemoryStorage())


lock = Lock()


class RegisterMessages(StatesGroup):
    await_name = State()


# Заебашить нормальный класс

keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
buttons = [
    "Найти модель",
    "Показать случайную модель",
    "Получить фото",
    "Получить видео",
]
keyboard.add(*buttons)


# ПЕРЕНЕСТИ НАХУЙ
def initialize_database():
    Database.initialize(
        database=config.DATABASE,
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
    )


initialize_database()


def clean_bio(bio):
    bio = (
        "\n".join(bio.replace("\r", "\n").split("\n")[:8])
        if len(bio.split("\n")) >= 8
        else bio
    )

    while "\n\n" in bio:
        bio = bio.replace("\n\n", "\n")

    bio = bio.replace("\n ", "\n")

    bio = bio[:300] if len(bio) >= 300 else bio

    return bio


@dp.message_handler(commands=["start"])
async def process_start_command(message: types.Message):
    start_message = "Добро пожаловать к NotOnlyFansBot!\nЗдесь ты можешь найти почти любую OnlyFans модель и скачать весь материал по ней/нему.\nПожалуйста, воспользуйся командами для начала"
    await bot.send_message(message.from_user.id, start_message, reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Показать случайную модель")
async def process_random_command(message: types.Message, state: FSMContext):
    model = Queries.get_random_model()
    async with state.proxy() as data:
        data["_current_model"] = model
    new_message = f"💖    Модель: {model[0]}    💖\n\n📷   Количество фото: {model[1]}    📷\n📽   Количество видео: {model[2]}    📽\n\n💌   Текст профиля    💌\n\n{clean_bio(model[3])}"
    await bot.send_photo(
        message.from_user.id, photo=model[4], caption=new_message, reply_markup=keyboard
    )

    await state.finish()


@dp.message_handler(lambda message: message.text == "Найти модель")
async def process_find_command(message: types.Message):
    await bot.send_message(message.from_user.id, "Введи ник модели на OnlyFans: ")
    await RegisterMessages.await_name.set()


@dp.message_handler(lambda message: message.text == "Получить фото")
async def process_get_photo_command(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            current_model = data["_current_model"]
        except KeyError:
            await bot.send_message(
                message.from_user.id,
                "Модель не выбрана",
                reply_markup=keyboard,
            )
            return

    media_group = types.MediaGroup()
    materials = []
    for _ in range(5):
        materials.append(
            await MaterialsManager().get_material_url(
                current_model[0], current_model[1], "photos"
            )
        )

    materials = set(materials)
    for material in materials:
        media_group.attach_photo(material)

    await bot.send_media_group(
        message.from_user.id,
        media=media_group,
    )


@dp.message_handler(lambda message: message.text == "Получить видео")
async def process_get_video_command(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            current_model = data["_current_model"]
        except KeyError:
            await bot.send_message(
                message.from_user.id,
                "Модель не выбрана",
                reply_markup=keyboard,
            )
            return

    video_img, video_url = await MaterialsManager().get_material_url(
        current_model[0], current_model[2], "videos"
    )

    ikb = InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            text="Переход к видео",
            web_app=WebAppInfo(url=video_url if video_url else config.NO_MATERIAL_URL),
        )
    )
    await bot.send_photo(message.from_user.id, photo=video_img, reply_markup=ikb)


@dp.message_handler(content_types="text", state=RegisterMessages.await_name)
async def reg_name(message: types.Message, state: FSMContext):
    async with lock:
        model = Queries.get_model(message.text)
        if model:
            async with state.proxy() as data:
                data["_current_model"] = model
            new_message = f"💖    Модель: {model[0]}    💖\n\n📷   Количество фото: {model[1]}    📷\n📽   Количество видео: {model[2]}    📽\n\n💌   Текст профиля    💌\n\n{clean_bio(model[3])}"
            await bot.send_photo(
                message.from_user.id,
                photo=model[4],
                caption=new_message,
                reply_markup=keyboard,
            )
        else:
            await bot.send_message(
                message.from_user.id,
                "Модель не найдена. Попробуй снова",
                reply_markup=keyboard,
            )

        await state.finish()


@dp.message_handler()
async def process_other_messages(message: types.Message):
    start_message = "Пожалуйста, воспользуйся кнопками для работы с ботом"
    await bot.send_message(message.from_user.id, start_message, reply_markup=keyboard)


if __name__ == "__main__":
    executor.start_polling(dispatcher=dp, skip_updates=True)
