import asyncio
import datetime
import sys
import threading
import typing
import uuid
from asyncio import Lock

import grequests
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.storage import FSMContext
from aiogram.types import (ChatActions, InlineKeyboardButton,
                           InlineKeyboardMarkup, InputMediaPhoto)
from aiogram.types.web_app_info import WebAppInfo
from aiogram.utils import executor
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import BadRequest

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
    m_manager = MaterialsManager()
    args = CallbackData("dun_w", "paymentid", "message", "userid", "msgurlid")

    @staticmethod
    def clean_bio(bio):
        if not bio:
            return ""
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
        Queries.add_user(str(message.from_user.id))
        start_message = f"Добро пожаловать к NotOnlyFans!\nЗдесь ты можешь найти слитые материалы на моделей c OnlyFans"
        await NotOnlyFansBot.bot.send_message(
            message.from_user.id, start_message, reply_markup=NotOnlyFansBot.keyboard
        )

    @staticmethod
    @dp.message_handler(commands=["sub_end"])
    async def process_subend_command(message: types.Message):
        sub_end_date = Queries.get_endsub_date(str(message.from_user.id))
        new_message = f"Дата истечения подписки: {sub_end_date}"
        await NotOnlyFansBot.bot.send_message(
            message.from_user.id, new_message, reply_markup=NotOnlyFansBot.keyboard
        )

    @staticmethod
    @dp.message_handler(commands=["subscribe"])
    async def process_subscribe_command(message: types.Message):
        response = grequests.map(
            [
                grequests.post(
                    url=config.PAYMENT_URL,
                    params={
                        "shop_id": config.SHOP_ID,
                        "order_id": uuid.uuid4(),
                        "amount": config.SUBSCRIPTION_COST,
                        "token": config.SHOP_TOKEN,
                    },
                )
            ]
        )[0].json()

        msg_url = await NotOnlyFansBot.bot.send_message(
            chat_id=message.from_user.id, text=f"Ссылка на оплату: {response['url']}"
        )

        msg = await NotOnlyFansBot.bot.send_message(
            chat_id=message.from_user.id,
            text=f"ID операции: {response['id']}\nСтоимость подписки: {config.SUBSCRIPTION_COST} рублей",
        )

        ikb = InlineKeyboardMarkup().add(
            InlineKeyboardButton(
                text="Проверить оплату",
                callback_data=NotOnlyFansBot.args.new(
                    paymentid=response["id"],
                    message=msg.message_id,
                    userid=message.from_user.id,
                    msgurlid=msg_url.message_id,
                ),
            )
        )

        await msg.edit_reply_markup(reply_markup=ikb)

    @dp.callback_query_handler(args.filter())
    async def check_payment(call: types.CallbackQuery, callback_data: dict):
        msg = callback_data.get("message")
        pay_id = callback_data.get("paymentid")
        user_id = callback_data.get("userid")
        msg_url_id = callback_data.get("msgurlid")

        response = grequests.map(
            [
                grequests.get(
                    url=config.CHECK_PAYMENT_URL,
                    params={
                        "shop_id": config.SHOP_ID,
                        "id": pay_id,
                        "token": config.SHOP_TOKEN,
                    },
                )
            ]
        )[0].json()

        ikb = InlineKeyboardMarkup().add(
            InlineKeyboardButton(
                text="Проверить оплату",
                callback_data=NotOnlyFansBot.args.new(
                    paymentid=pay_id, message=msg, userid=user_id, msgurlid=msg_url_id
                ),
            )
        )

        if response["status"] == "PAID":
            await NotOnlyFansBot.register_successful_payment(user_id)
            await NotOnlyFansBot.bot.edit_message_text(
                chat_id=user_id,
                message_id=msg,
                text=f"ID операции: {pay_id}\nСтатус: Успешно проведен",
            )
            await NotOnlyFansBot.bot.delete_message(
                chat_id=user_id, message_id=msg_url_id
            )
        elif response["status"] == "CANCEL":
            await NotOnlyFansBot.bot.edit_message_text(
                chat_id=user_id,
                message_id=msg,
                text=f"ID операции: {pay_id}\nСтатус: Отменен",
            )
            await NotOnlyFansBot.bot.delete_message(
                chat_id=user_id, message_id=msg_url_id
            )
        elif response["status"] == "WAIT":
            await NotOnlyFansBot.bot.edit_message_text(
                chat_id=user_id,
                message_id=msg,
                text=f"ID операции: {pay_id}\nСтатус: Ожидает оплаты\nВремя проверки: {(datetime.datetime.now() + datetime.timedelta(hours=3)).time()}\nСтоимость подписки: {config.SUBSCRIPTION_COST} рублей\nПроверка оплаты может достигать 5-7 минут",
                reply_markup=ikb,
            )

    @staticmethod
    async def register_successful_payment(user_id):
        Queries.prolong_subsription(str(user_id))

    @staticmethod
    @dp.message_handler(lambda message: message.text == "Текущая модель")
    async def process_current_model_command(message: types.Message, state: FSMContext):
        if not Queries.is_subsribed(str(message.from_user.id)):
            await NotOnlyFansBot.bot.send_message(
                message.from_user.id,
                "Подписка истекла, воспользуйтесь командой /subscribe для продления подписки",
                reply_markup=NotOnlyFansBot.keyboard,
            )
            return
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
        if not Queries.is_subsribed(str(message.from_user.id)):
            await NotOnlyFansBot.bot.send_message(
                message.from_user.id,
                "Подписка истекла, воспользуйтесь командой /subscribe для продления подписки",
                reply_markup=NotOnlyFansBot.keyboard,
            )
            return
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
        if not Queries.is_subsribed(str(message.from_user.id)):
            await NotOnlyFansBot.bot.send_message(
                message.from_user.id,
                "Подписка истекла, воспользуйтесь командой /subscribe для продления подписки",
                reply_markup=NotOnlyFansBot.keyboard,
            )
            return
        await NotOnlyFansBot.bot.send_message(
            message.from_user.id, "Введи ник модели на OnlyFans: "
        )
        await RegisterMessages.await_name.set()

    @staticmethod
    @dp.message_handler(lambda message: message.text == "Получить фото")
    async def process_get_photo_command(message: types.Message, state: FSMContext):
        if not Queries.is_subsribed(str(message.from_user.id)):
            await NotOnlyFansBot.bot.send_message(
                message.from_user.id,
                "Подписка истекла, воспользуйтесь командой /subscribe для продления подписки",
                reply_markup=NotOnlyFansBot.keyboard,
            )
            return

        async with state.proxy() as data:
            try:
                current_model = data["_current_model"]
                current_number = data["_current_number"]
                data["_current_number"] = current_number + 5
            except KeyError:
                await NotOnlyFansBot.bot.send_message(
                    message.from_user.id,
                    "Модель не выбрана",
                    reply_markup=NotOnlyFansBot.keyboard,
                )
                return

        msg = await NotOnlyFansBot.bot.send_message(
            chat_id=message.from_user.id, text="Получаем фото с сервера..."
        )
        media_group = []
        materials = [
            await NotOnlyFansBot.m_manager.get_material_url(
                current_model[0], current_model[1], "photos", current_number - i
            )
            for i in range(5)
        ]

        materials = set(materials)
        for material in materials:
            media_group.append(InputMediaPhoto(material))
            await types.ChatActions.upload_photo()

        await msg.edit_text(text="Загружаем фото в телеграм...")
        try:
            await NotOnlyFansBot.bot.send_media_group(
                chat_id=message.from_user.id, media=media_group
            )
            await msg.delete()
        except BadRequest as Err:
            logger.error(Err)
            await msg.edit_text(text="Не удалось загрузить фото 🥲")

    @staticmethod
    @dp.message_handler(lambda message: message.text == "Получить видео")
    async def process_get_video_command(message: types.Message, state: FSMContext):
        if not Queries.is_subsribed(str(message.from_user.id)):
            await NotOnlyFansBot.bot.send_message(
                message.from_user.id,
                "Подписка истекла, воспользуйтесь командой /subscribe для продления подписки",
                reply_markup=NotOnlyFansBot.keyboard,
            )
            return
        async with state.proxy() as data:
            try:
                current_model = data["_current_model"]
                current_number = data["_current_number"]
                current_number %= 100000
                data["_current_number"] = current_number
            except KeyError:
                await NotOnlyFansBot.bot.send_message(
                    message.from_user.id,
                    "Модель не выбрана",
                    reply_markup=NotOnlyFansBot.keyboard,
                )
                return
            video_img, video_url = await NotOnlyFansBot.m_manager.get_material_url(
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
        if not Queries.is_subsribed(str(message.from_user.id)):
            await NotOnlyFansBot.bot.send_message(
                message.from_user.id,
                "Подписка истекла, воспользуйтесь командой /subscribe для продления подписки",
                reply_markup=NotOnlyFansBot.keyboard,
            )
            return
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
                models_alike_response = Queries.get_alike_models(message.text.lower())
                no_model_message = "Модель не найдена 😓\n"

                if models_alike_response:
                    no_model_message += "\nПохожие модели:\n - " + "\n - ".join(
                        model[0] for model in models_alike_response
                    )

                await NotOnlyFansBot.bot.send_message(
                    message.from_user.id,
                    no_model_message,
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
        # loop.create_task(db.update_models())
        [loop.create_task(db.update_materials(attempt)) for attempt in range(61)]
        loop.run_forever()
        loop.close()
    elif "-s" in sys.argv or "--support" in sys.argv:
        executor.start_polling(dispatcher=Support.dp, skip_updates=True)
    else:
        executor.start_polling(dispatcher=NotOnlyFansBot.dp, skip_updates=True)
