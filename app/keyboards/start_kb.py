from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- Клавиатура основного меню ---
async def start_kb():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🚗 Забронировать поездку', callback_data='start_booking')],
        [InlineKeyboardButton(text='📞 Связаться с поддержкой', url='https://t.me/AvtoNanny_VL?direct')]
    ])
    
    return kb

# --- Клавиатура проверки подписки ---
def get_sub_check_kb(channel_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text="📢 Подписаться на канал", url=channel_url)
    builder.button(text="✅ Я подписался", callback_data="check_subscription")
    builder.adjust(1)

    return builder.as_markup()
