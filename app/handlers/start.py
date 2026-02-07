import os
import html

from aiogram import Router, Bot, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from app.keyboards.start_kb import start_kb, get_sub_check_kb

router = Router()

# Настройки канала
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
CHANNEL_URL = os.getenv('CHANNEL_URL')

async def is_subscribed(bot: Bot, user_id: int, channel_id: int) -> bool:
    """Проверяет, подписан ли пользователь на канал."""
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)

        return member.status in ['creator', 'administrator', 'member']
    
    except TelegramBadRequest:
        return False

# --- ХЕНДЛЕР START ---
@router.message(CommandStart())
async def start_cmd(message: Message, bot: Bot):
    user_id = message.from_user.id
    first_name = html.escape(message.from_user.first_name)

    # 1. Проверяем подписку
    if not await is_subscribed(bot, user_id, CHANNEL_ID):
        await message.answer(
            text=(
                f"Привет, {first_name}! 👋\n\n"
                "🔒 <b>Доступ ограничен</b>\n"
                "Для использования бота необходимо быть подписанным на наш канал."
            ),
            reply_markup=get_sub_check_kb(CHANNEL_URL)
        )

        return

    # 2. Если подписан — показываем меню
    await message.answer(
        text=f'Привет, {first_name} 👋 Я бот для записи к автоняне 🤖\n\nВыберите действие: 👇',
        reply_markup=await start_kb()
    )

@router.callback_query(F.data == "check_subscription")
async def process_check_sub(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    first_name = html.escape(callback.from_user.first_name)

    if await is_subscribed(bot, user_id, CHANNEL_ID):
        await callback.message.delete()
        await callback.message.answer(
            text=f'Привет, {first_name} 👋 Я бот для записи к автоняне 🤖\n\nВыберите действие: 👇',
            reply_markup=await start_kb()
        )

    else:
        await callback.answer("❌ Вы еще не подписались на канал!", show_alert=True)
