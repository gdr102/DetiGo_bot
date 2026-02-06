from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
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

# --- Возраст ---
def get_age_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="0-3 года", callback_data="age_0-3")
    kb.button(text="4-6 лет", callback_data="age_4-6")
    kb.button(text="7+ лет", callback_data="age_7+")
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
    
    row_btns = []
    row_btns.append(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_step"))
    row_btns.append(InlineKeyboardButton(text="Готово ➡️", callback_data=f"{callback_prefix}_done"))
    kb.row(*row_btns)
    
    return kb.as_markup()

