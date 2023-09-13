from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from core.config import config


class Support:
    # Start bot's essentials
    bot = Bot(config.SUP_BOT_API_KEY)
    dp = Dispatcher(bot=bot, storage=MemoryStorage())

    @staticmethod
    @dp.message_handler(commands=["start"])
    async def process_start_command(message: types.Message):
        start_message = "Добро пожаловать к NotOnlySupport!\nЗдесь ты можешь оставить отзыв или жалобу на NotOnlyFansBot. Наша поддержка обязательно ответит на твой вопрос, обращайся!"
        await Support.bot.send_message(message.from_user.id, start_message)

    @staticmethod
    @dp.message_handler()
    async def process_user_messages(message: types.Message):
        if str(message.chat.id) != config.SUP_CHAT_ID:
            await Support.bot.send_message(
                config.SUP_CHAT_ID, str(message.from_user.id) + ": " + message.text
            )
        elif str(message.chat.id) == config.SUP_CHAT_ID:
            reply_id = message.reply_to_message.text.split(":")[0]
            await Support.bot.send_message(reply_id, message.text)
