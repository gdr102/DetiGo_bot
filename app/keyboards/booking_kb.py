from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- Клавиатура подтверждения ---
def get_confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Все верно", callback_data="confirm_booking")
    builder.button(text="🔄 Заполнить заново", callback_data="restart_booking")
    builder.button(text="⬅️ Назад", callback_data="back_step")
    builder.adjust(1)
    return builder.as_markup()

# --- Кнопка "Отмена" ---
def get_cancel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_booking")
    return builder.as_markup()

# --- Обычная кнопка "Назад" ---
def get_inline_back_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="back_step")
    return builder.as_markup()

# --- Кнопка "Поделиться номером" (Reply) ---
def get_contact_reply_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Поделиться номером", request_contact=True)],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


# --- Возраст ---
def get_age_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="0 - 3 года", callback_data="age_0-3")
    kb.button(text="4 - 6 лет", callback_data="age_4-6")
    kb.button(text="7 - 10 лет", callback_data="age_7-10")
    kb.button(text="11 - 13 лет", callback_data="age_11-13")
    kb.button(text="14+ лет", callback_data="age_14+")
    kb.button(text="⬅️ Назад", callback_data="back_step")
    kb.adjust(1)
    return kb.as_markup()

# --- Мульти-выбор ---
def get_multiselect_kb(options: dict, selected: list, callback_prefix: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for key, text in options.items():
        is_selected = key in selected
        btn_text = f"✅ {text}" if is_selected else text
        kb.button(text=btn_text, callback_data=f"{callback_prefix}_{key}")

    kb.adjust(1)
    
    row_btns = [
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_step"),
        InlineKeyboardButton(text="Готово ➡️", callback_data=f"{callback_prefix}_done")
    ]
    kb.row(*row_btns)
    
    return kb.as_markup()

# --- Выбор регулярности поездки ---
def get_schedule_type_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Разовая поездка", callback_data="sched_once")
    kb.button(
        text="Регулярные поездки – мы обсудим график индивидуально",
        callback_data="sched_regular"
    )
    kb.button(text="⬅️ Назад", callback_data="back_step")
    kb.adjust(1)
    return kb.as_markup()


# --- Шаг дополнительных пожеланий (Пропустить / Назад) ---
def get_extra_wishes_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Пропустить ➡️", callback_data="skip_extra_wishes")
    kb.button(text="⬅️ Назад", callback_data="back_step")
    kb.adjust(1)
    return kb.as_markup()


