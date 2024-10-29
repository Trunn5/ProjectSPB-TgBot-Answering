import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, BaseFilter
from aiogram.types import Message
from dotenv import load_dotenv

# Настройки бота и администратора
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Хранилище для отслеживания исходных сообщений пользователей
message_ids = {}


# Кастомный фильтр для проверки на администратора
class IsAdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id == ADMIN_ID


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Привет! Отправьте мне сообщение, и я передам его администратору.")
    logger.info(f"Пользователь {message.from_user.id} начал диалог.")


@dp.message(F.reply_to_message, IsAdminFilter())
async def reply_to_user(message: Message):
    # Проверяем, что сообщение является ответом на сообщение от бота и что оно от администратора
    user_id = message_ids.get(message.reply_to_message.message_id)
    if user_id:
        try:
            # Отправляем ответ пользователю
            await bot.send_message(chat_id=user_id, text=message.text)
            logger.info(f"Ответ администратора переслан пользователю {user_id}.")
        except Exception as e:
            logger.error(f"Ошибка при отправке ответа пользователю {user_id}: {e}")
    else:
        await message.reply("Не удалось найти пользователя для ответа.")
        logger.warning("Не удалось найти пользователя для ответа администратора.")


@dp.message(F.text)
async def forward_to_admin(message: Message):
    # Форматируем сообщение для отправки администратору
    text = f"id: {message.from_user.id}\n\n{message.text}"
    try:
        # Отправляем сообщение админу и сохраняем ID сообщения для отслеживания ответа
        forwarded_message = await bot.send_message(chat_id=ADMIN_ID, text=text)
        # Сохраняем ID сообщения пользователя и ID пересланного админу
        message_ids[forwarded_message.message_id] = message.from_user.id
        logger.info(f"Сообщение от пользователя {message.from_user.id} переслано админу.")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения админу: {e}")


async def main():
    logger.info("Бот запущен.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
