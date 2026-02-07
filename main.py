import os
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand, BotCommandScopeDefault

from dotenv import load_dotenv
load_dotenv()

from app.handlers import start, booking

TOKEN = os.getenv('TOKEN')

async def main():
    bot = Bot(
        token=TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    commands = [
        BotCommand(command='/start', description='Запустить бота')
    ]

    await bot.set_my_commands(commands=commands, scope=BotCommandScopeDefault())

    dp.include_routers(start.router, booking.router)

    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
