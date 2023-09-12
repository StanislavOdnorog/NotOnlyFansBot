import asyncio
import sys
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
from db.queries import Queries
from db_manager import DBManager
from materials_manager import MaterialsManager
from support import Support


# CLass for variables in the date that start with _ will be indelible
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


# Class for FSMState for bot
class RegisterMessages(StatesGroup):
    await_name = State()


# Function to register keyboard
def register_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        "Найти модель",
        "Случайная модель",
        "Текущая модель",
        "Получить видео",
        "Получить фото",
    ]
    keyboard.add(*buttons)
    return keyboard


class NotOnlyFansBot:
    # Start bot's essentials
    bot = Bot(config.BOT_API_KEY)
    dp = Dispatcher(bot=bot, storage=GMemoryStorage())
    keyboard = register_keyboard()
    lock = Lock()
    DBManager.initialize_database()

    @staticmethod
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

    @staticmethod
    @dp.message_handler(commands=["start"])
    async def process_start_command(message: types.Message):
        start_message = "Добро пожаловать к NotOnlyFans!\nЗдесь ты можешь найти слитые материалы на моделей с OnlyFans\nПожалуйста, воспользуйся командами для начала"
        await NotOnlyFansBot.bot.send_message(
            message.from_user.id, start_message, reply_markup=NotOnlyFansBot.keyboard
        )

    @staticmethod
    @dp.message_handler(lambda message: message.text == "Текущая модель")
    async def process_current_model_command(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            try:
                current_model = data["_current_model"]
            except KeyError:
                await NotOnlyFansBot.bot.send_message(
                    message.from_user.id,
                    "Модель не выбрана",
                    reply_markup=NotOnlyFansBot.keyboard,
                )
                return
        message.text = current_model[0]
        await NotOnlyFansBot.reg_name(message=message, state=state)

    @staticmethod
    @dp.message_handler(lambda message: message.text == "Случайная модель")
    async def process_random_command(message: types.Message, state: FSMContext):
        model = Queries.get_random_model()
        async with state.proxy() as data:
            data["_current_model"] = model
            try:
                current_number = data["_current_number"]
            except:
                data["_current_number"] = 0
        new_message = f"💖    Модель: {model[0]}    💖\n\n📷   Количество фото: {model[1]}    📷\n📽   Количество видео: {model[2]}    📽\n\n💌   Текст профиля    💌\n\n{NotOnlyFansBot.clean_bio(model[3])}"
        await NotOnlyFansBot.bot.send_photo(
            message.from_user.id,
            photo=model[4],
            caption=new_message,
            reply_markup=NotOnlyFansBot.keyboard,
        )
        await state.finish()

    @staticmethod
    @dp.message_handler(lambda message: message.text == "Найти модель")
    async def process_find_command(message: types.Message):
        await NotOnlyFansBot.bot.send_message(
            message.from_user.id, "Введи ник модели на OnlyFans: "
        )
        await RegisterMessages.await_name.set()

    @staticmethod
    @dp.message_handler(lambda message: message.text == "Получить фото")
    async def process_get_photo_command(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            try:
                current_model = data["_current_model"]
                current_number = data["_current_number"]
                current_number %= 100000
            except KeyError:
                await NotOnlyFansBot.bot.send_message(
                    message.from_user.id,
                    "Модель не выбрана",
                    reply_markup=NotOnlyFansBot.keyboard,
                )
                return
            media_group = types.MediaGroup()
            materials = []
            for _ in range(5):
                materials.append(
                    await MaterialsManager().get_material_url(
                        current_model[0], current_model[1], "photos", current_number
                    )
                )
                data["_current_number"] = current_number + 1
                current_number += 1
            try:
                materials = set(materials)
            except TypeError as Err:
                logger.error(Err)

            for material in materials:
                media_group.attach_photo(material)
            await NotOnlyFansBot.bot.send_media_group(
                message.from_user.id,
                media=media_group,
            )

    @staticmethod
    @dp.message_handler(lambda message: message.text == "Получить видео")
    async def process_get_video_command(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            try:
                current_model = data["_current_model"]
                current_number = data["_current_number"]
                current_number %= 100000
            except KeyError:
                await NotOnlyFansBot.bot.send_message(
                    message.from_user.id,
                    "Модель не выбрана",
                    reply_markup=NotOnlyFansBot.keyboard,
                )
                return
            video_img, video_url = await MaterialsManager().get_material_url(
                current_model[0], current_model[2], "videos", current_number
            )
            data["_current_number"] = current_number + 1
            ikb = InlineKeyboardMarkup().add(
                InlineKeyboardButton(
                    text="Переход к видео",
                    web_app=WebAppInfo(
                        url=video_url if video_url else config.NO_MATERIAL_URL
                    ),
                )
            )
            await NotOnlyFansBot.bot.send_photo(
                message.from_user.id, photo=video_img, reply_markup=ikb
            )

    @staticmethod
    @dp.message_handler(content_types="text", state=RegisterMessages.await_name)
    async def reg_name(message: types.Message, state: FSMContext):
        async with NotOnlyFansBot.lock:
            model = Queries.get_model(message.text.lower())
            if model:
                async with state.proxy() as data:
                    data["_current_model"] = model
                    try:
                        current_number = data["_current_number"]
                    except:
                        data["_current_number"] = 0
                new_message = f"💖    Модель: {model[0]}    💖\n\n📷   Количество фото: {model[1]}    📷\n📽   Количество видео: {model[2]}    📽\n\n💌   Текст профиля    💌\n\n{NotOnlyFansBot.clean_bio(model[3])}"
                await NotOnlyFansBot.bot.send_photo(
                    message.from_user.id,
                    photo=model[4],
                    caption=new_message,
                    reply_markup=NotOnlyFansBot.keyboard,
                )
            else:
                await NotOnlyFansBot.bot.send_message(
                    message.from_user.id,
                    "Модель не найдена. Попробуй снова",
                    reply_markup=NotOnlyFansBot.keyboard,
                )

            await state.finish()

    @staticmethod
    @dp.message_handler()
    async def process_other_messages(message: types.Message):
        start_message = "Пожалуйста, воспользуйся кнопками для работы с ботом"
        await NotOnlyFansBot.bot.send_message(
            message.from_user.id, start_message, reply_markup=NotOnlyFansBot.keyboard
        )


if __name__ == "__main__":
    if "-u" in sys.argv or "--update" in sys.argv:
        db = DBManager()
        loop = asyncio.get_event_loop()
        tasks = [loop.create_task(db.update_models())]
        tasks.append(loop.create_task(db.update_materials()) for _ in range(60))
        loop.run_until_complete(asyncio.wait(tasks))
        loop.close()
    elif "-s" in sys.argv or "--support" in sys.argv:
        executor.start_polling(dispatcher=Support.dp, skip_updates=True)
    else:
        executor.start_polling(dispatcher=NotOnlyFansBot.dp, skip_updates=True)
