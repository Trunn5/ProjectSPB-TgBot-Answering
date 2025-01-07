import asyncio
import logging
import os
import sqlite3
import csv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, BaseFilter, Command
from aiogram.types import Message
from aiogram.types import FSInputFile
from dotenv import load_dotenv

# Настройки бота и администратора
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS').split(',')))

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Хранилище для отслеживания исходных сообщений пользователей
message_ids = {}

# Создание или подключение к SQLite базе данных
db_path = "users.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT
)
""")
conn.commit()

# Кастомный фильтр для проверки на администратора
class IsAdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMIN_IDS


@dp.message(CommandStart())
async def start(message: Message):
    # Сохранение данных пользователя в базу данных
    user_id = message.from_user.id
    cursor.execute("""
    INSERT OR IGNORE INTO users (id, username, first_name, last_name)
    VALUES (?, ?, ?, ?)
    """, (user_id, message.from_user.username, message.from_user.first_name, message.from_user.last_name))
    conn.commit()

    await message.answer("Привет! Отправьте мне сообщение, и я передам его администратору.")
    logger.info(f"Пользователь {user_id} начал диалог.")


@dp.message(Command(commands=["users"]), IsAdminFilter())
async def get_users(message: Message):
    # Получение всех пользователей из базы данных
    cursor.execute("SELECT id, username, first_name, last_name FROM users")
    users = cursor.fetchall()

    if not users:
        await message.answer("Список пользователей пуст.")
        return

    # Форматируем данные для ответа
    user_list = "\n".join([f"{user[0]} | @{user[1]} | {user[2]} {user[3]}" for user in users])
    response = f"ID | Username | First Name Last Name\n{'-'*40}\n{user_list}"

    # Создаем CSV файл
    csv_file_path = "users.csv"
    with open(csv_file_path, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["ID", "Username", "First Name", "Last Name"])  # Заголовки
        writer.writerows(users)  # Данные

    # Отправляем CSV файл админу
    csv_file = FSInputFile(csv_file_path)
    await message.answer_document(csv_file)

    # Отправляем список пользователей в текстовом формате
    await message.answer(f"Список пользователей:\n\n{response}")
    logger.info("Администратор запросил список пользователей и CSV файл отправлен.")


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
    user_id = message.from_user.id
    cursor.execute("""
    INSERT OR IGNORE INTO users (id, username, first_name, last_name)
    VALUES (?, ?, ?, ?)
    """, (user_id, message.from_user.username, message.from_user.first_name, message.from_user.last_name))
    conn.commit()
    # Форматируем сообщение для отправки администратору
    text = f"id: {message.from_user.id}\n\n{message.text}"
    try:
        # Отправляем сообщение админу и сохраняем ID сообщения для отслеживания ответа
        for admin in ADMIN_IDS:
            forwarded_message = await bot.send_message(chat_id=admin, text=text)
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
