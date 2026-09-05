import os
import re
import html
import logging
from contextlib import suppress

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.exceptions import TelegramBadRequest, TelegramMigrateToChat

from app.states import BookingSteps
from app.keyboards.start_kb import start_kb
from app.keyboards.booking_kb import (
    get_age_kb, get_multiselect_kb, 
    get_confirm_kb, get_inline_back_kb, get_cancel_kb,
    get_contact_reply_kb, get_schedule_type_kb, get_extra_wishes_kb
)

router = Router()

ADMIN_GROUP_ID = int(os.getenv('ADMIN_GROUP_ID', 0))

# --- ОПЦИИ ДЕТАЛЕЙ ПОЕЗДКИ ---
MEETING_OPTIONS = {
    "entrance": "Встретить ребенка у входа в здание и сопроводить до машины",
    "inside": "Забрать из помещения и проводить до машины",
    "dress": "Помочь переодеться",
    "sign": "Встретить с табличкой «DeтиGo»",
}

FEATURES_OPTIONS = {
    "dirt_road": "В маршруте есть грунтовые дороги",
    "more_kids": "В машине будет более 1 ребенка",
    "waiting": "Требуется ожидание",
    "extra_stop": "Нужен дополнительный заезд по пути",
    "other": "Другое",
}

SCHEDULE_OPTIONS = {
    "once": "Разовая поездка",
    "regular": "Регулярные поездки – мы обсудим график индивидуально",
}


AGE_OPTIONS = {
    "age_0-3": "0 - 3 года",
    "age_4-6": "4 - 6 лет",
    "age_7-10": "7 - 10 лет",
    "age_11-13": "11 - 13 лет",
    "age_14+": "14+ лет",
}

# --- УТИЛИТЫ ИНТЕРФЕЙСА ---
async def update_interface(bot: Bot, state: FSMContext, text: str, reply_markup=None):
    data = await state.get_data()
    msg_id = data.get("msg_id")
    chat_id = data.get("chat_id")

    if msg_id and chat_id:
        with suppress(TelegramBadRequest):
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=text,
                reply_markup=reply_markup
            )

async def remove_contact_reply_kb(bot: Bot, chat_id: int):
    with suppress(TelegramBadRequest):
        msg = await bot.send_message(chat_id, "⏳", reply_markup=ReplyKeyboardRemove())
        await msg.delete()

async def enter_phone_step(bot: Bot, state: FSMContext, chat_id: int):
    await state.set_state(BookingSteps.phone)
    data = await state.get_data()
    old_msg_id = data.get("msg_id")

    if old_msg_id:
        with suppress(TelegramBadRequest):
            await bot.delete_message(chat_id=chat_id, message_id=old_msg_id)

    text = (
        "<b>Контакт для связи.</b>\n\n"
        "<i>Введите номер в формате: +7/89991234567</i>\n\n"
        "👇 Вы также можете нажать кнопку ниже, чтобы поделиться контактом:"
    )
    new_msg = await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=get_contact_reply_kb()
    )
    await state.update_data(msg_id=new_msg.message_id)


# --- Обработчик ОТМЕНЫ ---
@router.callback_query(F.data == "cancel_booking")
async def process_cancel(callback: CallbackQuery, state: FSMContext):
    chat_id = callback.message.chat.id
    await remove_contact_reply_kb(callback.bot, chat_id)
    await state.clear()

    first_name = html.escape(callback.from_user.first_name)
    await callback.message.edit_text(
        text=f'Привет, {first_name} 👋 Я бот для записи к автоняне 🤖\n\nВыберите действие: 👇',
        reply_markup=await start_kb()
    )
    await callback.answer("Заявка отменена")

# --- Обработчик НАЗАД ---
@router.callback_query(F.data == "back_step")
async def process_back_step(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    chat_id = callback.message.chat.id
    bot = callback.bot
    data = await state.get_data()

    if current_state == BookingSteps.phone:
        old_msg_id = data.get("msg_id")
        if old_msg_id:
            with suppress(TelegramBadRequest):
                await bot.delete_message(chat_id=chat_id, message_id=old_msg_id)
        await remove_contact_reply_kb(bot, chat_id)
        await state.set_state(BookingSteps.name)
        text = "<b>Как к Вам обращаться</b>?\n\n<i>(Ваше имя)</i>"
        new_msg = await bot.send_message(chat_id=chat_id, text=text, reply_markup=get_cancel_kb())
        await state.update_data(msg_id=new_msg.message_id, chat_id=chat_id)



    elif current_state == BookingSteps.booking_date:
        await enter_phone_step(bot, state, chat_id)

    elif current_state == BookingSteps.booking_time:
        await state.set_state(BookingSteps.booking_date)
        text = (
            "<b>Удобная дата поездки.</b>\n"
            "Мы подстроимся под Ваш график, даже если он меняется ⏰\n\n"
            "<i>Введите дату в формате дд.мм.гггг (01.09.2026)</i>"
        )
        await update_interface(bot, state, text, get_inline_back_kb())

    elif current_state == BookingSteps.route:
        await state.set_state(BookingSteps.booking_time)
        text = (
            "<b>Удобное время поездки.</b>\n\n"
            "<i>Введите время в формате чч:мм (10:10)</i>"
        )
        await update_interface(bot, state, text, get_inline_back_kb())

    elif current_state == BookingSteps.child_age:
        await state.set_state(BookingSteps.route)
        text = (
            "<b>Маршрут поездки</b>\n"
            "Укажите адреса: откуда и куда нужно доставить ребенка. "
            "Если маршрутов несколько – просто перечислите их\n\n"
            "<i>Пример: Школа 1 → площадь Ленина, 15</i>"
        )
        await update_interface(bot, state, text, get_inline_back_kb())

    elif current_state == BookingSteps.meeting_details:
        await state.set_state(BookingSteps.child_age)
        text = "<b>Возраст ребенка:</b>"
        await update_interface(bot, state, text, get_age_kb())

    elif current_state == BookingSteps.route_features:
        await state.set_state(BookingSteps.meeting_details)
        selected = data.get("meeting_details", [])
        text = "<b>Детали поездки</b>\nКак нам встретить Вашего ребенка? 🤝"
        await update_interface(bot, state, text, get_multiselect_kb(MEETING_OPTIONS, selected, "meet"))

    elif current_state == BookingSteps.features_comment:
        await state.set_state(BookingSteps.route_features)
        selected = data.get("features", [])
        text = "<b>Детали поездки</b>\nДополнительные условия поездки:"
        await update_interface(bot, state, text, get_multiselect_kb(FEATURES_OPTIONS, selected, "feat"))

    elif current_state == BookingSteps.schedule_type:
        if "other" in data.get("features", []):
            await state.set_state(BookingSteps.features_comment)
            await update_interface(bot, state, "Вы выбрали 'Другое'. Напишите, пожалуйста, комментарий:", get_inline_back_kb())
        else:
            await state.set_state(BookingSteps.route_features)
            selected = data.get("features", [])
            text = "<b>Детали поездки</b>\nДополнительные условия поездки:"
            await update_interface(bot, state, text, get_multiselect_kb(FEATURES_OPTIONS, selected, "feat"))

    elif current_state == BookingSteps.extra_wishes:
        await state.set_state(BookingSteps.schedule_type)
        text = "<b>Детали поездки</b>\nЭто разовая или регулярная поездка? 🚗"
        await update_interface(bot, state, text, get_schedule_type_kb())

    elif current_state == BookingSteps.check_data:
        await state.set_state(BookingSteps.extra_wishes)
        text = (
            "<b>Детали поездки</b>\n"
            "Хотите что-то добавить?\n\n"
            "Мы учтём любые пожелания: любимая музыка в дороге, аудиокнига, "
            "игрушка для ребёнка – просто напишите✍️"
        )
        await update_interface(bot, state, text, get_extra_wishes_kb())

    await callback.answer()

# --- ШАГ 1: ИМЯ ---
@router.callback_query(F.data == "start_booking")
async def start_booking_process(callback: CallbackQuery, state: FSMContext):
    await state.update_data(msg_id=callback.message.message_id, chat_id=callback.message.chat.id)
    await state.set_state(BookingSteps.name)

    text = "<b>Как к Вам обращаться</b>?\n\n<i>(Ваше имя)</i>"
    await callback.message.edit_text(text, reply_markup=get_cancel_kb())

@router.message(BookingSteps.name)
async def process_name(message: Message, state: FSMContext):
    with suppress(TelegramBadRequest):
        await message.delete()

    await state.update_data(name=message.text)
    await enter_phone_step(message.bot, state, message.chat.id)

# --- ШАГ 2: ТЕЛЕФОН ---
@router.message(BookingSteps.phone, F.text == "⬅️ Назад")
async def process_phone_back(message: Message, state: FSMContext):
    chat_id = message.chat.id
    bot = message.bot
    data = await state.get_data()
    old_msg_id = data.get("msg_id")

    with suppress(TelegramBadRequest):
        await message.delete()

    if old_msg_id:
        with suppress(TelegramBadRequest):
            await bot.delete_message(chat_id=chat_id, message_id=old_msg_id)

    await remove_contact_reply_kb(bot, chat_id)
    await state.set_state(BookingSteps.name)

    text = "<b>Как к Вам обращаться</b>?\n\n<i>(Ваше имя)</i>"
    new_msg = await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=get_cancel_kb()
    )
    await state.update_data(msg_id=new_msg.message_id, chat_id=chat_id)

@router.message(BookingSteps.phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    phone_number = message.contact.phone_number
    if not phone_number.startswith("+"):
        phone_number = f"+{phone_number}"

    chat_id = message.chat.id
    bot = message.bot
    data = await state.get_data()
    old_msg_id = data.get("msg_id")

    with suppress(TelegramBadRequest):
        await message.delete()

    if old_msg_id:
        with suppress(TelegramBadRequest):
            await bot.delete_message(chat_id=chat_id, message_id=old_msg_id)

    await remove_contact_reply_kb(bot, chat_id)
    await state.update_data(phone=phone_number)
    await state.set_state(BookingSteps.booking_date)

    text = (
        "<b>Удобная дата поездки.</b>\n"
        "Мы подстроимся под Ваш график, даже если он меняется ⏰\n\n"
        "<i>Введите дату в формате дд.мм.гггг (01.09.2026)</i>"
    )
    new_msg = await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=get_inline_back_kb()
    )
    await state.update_data(msg_id=new_msg.message_id, chat_id=chat_id)

@router.message(BookingSteps.phone)
async def process_phone_text(message: Message, state: FSMContext):
    raw_phone = message.text or ""
    chat_id = message.chat.id
    bot = message.bot
    data = await state.get_data()
    old_msg_id = data.get("msg_id")

    with suppress(TelegramBadRequest):
        await message.delete()

    clean_phone = re.sub(r'[^\d+]', '', raw_phone) 
    is_valid = False
    if clean_phone.startswith("+7") and len(clean_phone) == 12:
        is_valid = True
    elif clean_phone.startswith("8") and len(clean_phone) == 11:
        is_valid = True
    elif clean_phone.startswith("7") and len(clean_phone) == 11:
        raw_phone = "+" + clean_phone
        is_valid = True
        
    if not is_valid:
        error_text = (
            "⚠️ Неверный формат номера.\n\n"
            "<b>Контакт для связи.</b>\n\n"
            "<i>Введите номер в формате: +7/89991234567</i>\n\n"
            "👇 Вы также можете нажать кнопку ниже, чтобы поделиться контактом:"
        )
        if old_msg_id:
            with suppress(TelegramBadRequest):
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=old_msg_id,
                    text=error_text
                )
        return

    if old_msg_id:
        with suppress(TelegramBadRequest):
            await bot.delete_message(chat_id=chat_id, message_id=old_msg_id)

    await remove_contact_reply_kb(bot, chat_id)
    await state.update_data(phone=raw_phone)
    await state.set_state(BookingSteps.booking_date)

    text = (
        "<b>Удобная дата поездки.</b>\n"
        "Мы подстроимся под Ваш график, даже если он меняется ⏰\n\n"
        "<i>Введите дату в формате дд.мм.гггг (01.09.2026)</i>"
    )
    new_msg = await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=get_inline_back_kb()
    )
    await state.update_data(msg_id=new_msg.message_id, chat_id=chat_id)



# --- ШАГ 3: ДАТА ---
@router.message(BookingSteps.booking_date)
async def process_date(message: Message, state: FSMContext):
    with suppress(TelegramBadRequest):
        await message.delete()

    await state.update_data(booking_date=message.text)
    await state.set_state(BookingSteps.booking_time)

    text = (
        "<b>Удобное время поездки.</b>\n\n"
        "<i>Введите время в формате чч:мм (10:10)</i>"
    )
    await update_interface(message.bot, state, text, get_inline_back_kb())

# --- ШАГ 4: ВРЕМЯ ---
@router.message(BookingSteps.booking_time)
async def process_time(message: Message, state: FSMContext):
    with suppress(TelegramBadRequest):
        await message.delete()

    await state.update_data(booking_time=message.text)
    await state.set_state(BookingSteps.route)

    text = (
        "<b>Маршрут поездки</b>\n"
        "Укажите адреса: откуда и куда нужно доставить ребенка. "
        "Если маршрутов несколько – просто перечислите их\n\n"
        "<i>Пример: Школа 1 → площадь Ленина, 15</i>"
    )
    await update_interface(message.bot, state, text, get_inline_back_kb())

# --- ШАГ 5: МАРШРУТ ---
@router.message(BookingSteps.route)
async def process_route(message: Message, state: FSMContext):
    with suppress(TelegramBadRequest):
        await message.delete()

    await state.update_data(route=message.text)
    await state.set_state(BookingSteps.child_age)

    text = "<b>Возраст ребенка:</b>"
    await update_interface(message.bot, state, text, get_age_kb())

# --- ШАГ 6: ВОЗРАСТ РЕБЕНКА ---
@router.callback_query(F.data.startswith("age_"), BookingSteps.child_age)
async def process_age(callback: CallbackQuery, state: FSMContext):
    selected_age = AGE_OPTIONS.get(callback.data, callback.data)
    await state.update_data(age=selected_age)
    await state.update_data(meeting_details=[])
    await state.set_state(BookingSteps.meeting_details)

    text = "<b>Детали поездки</b>\nКак нам встретить Вашего ребенка? 🤝"
    await update_interface(callback.bot, state, text, get_multiselect_kb(MEETING_OPTIONS, [], "meet"))
    await callback.answer()

# --- ШАГ 7: ДЕТАЛИ - КАК ВСТРЕТИТЬ РЕБЕНКА ---
@router.callback_query(F.data.startswith("meet_"), BookingSteps.meeting_details)
async def process_meeting_select(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_", 1)[1]
    data = await state.get_data()
    selected = data.get("meeting_details", [])

    if action == "done":
        await state.update_data(features=[])
        await state.set_state(BookingSteps.route_features)
        text = "<b>Детали поездки</b>\nДополнительные условия поездки:"
        await update_interface(callback.bot, state, text, get_multiselect_kb(FEATURES_OPTIONS, [], "feat"))
    else:
        if action in selected:
            selected.remove(action)
        else:
            selected.append(action)

        await state.update_data(meeting_details=selected)
        with suppress(TelegramBadRequest):
            await callback.message.edit_reply_markup(
                reply_markup=get_multiselect_kb(MEETING_OPTIONS, selected, "meet")
            )
    await callback.answer()

# --- ШАГ 8: ДЕТАЛИ - ДОПОЛНИТЕЛЬНЫЕ УСЛОВИЯ ---
@router.callback_query(F.data.startswith("feat_"), BookingSteps.route_features)
async def process_features_select(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_", 1)[1]
    data = await state.get_data()
    selected = data.get("features", [])

    if action == "done":
        if "other" in selected:
            await state.set_state(BookingSteps.features_comment)
            await update_interface(
                callback.bot,
                state,
                "Вы выбрали 'Другое'. Напишите, пожалуйста, комментарий:",
                get_inline_back_kb()
            )
        else:
            await state.set_state(BookingSteps.schedule_type)
            text = "<b>Детали поездки</b>\nЭто разовая или регулярная поездка? 🚗"
            await update_interface(callback.bot, state, text, get_schedule_type_kb())
    else:
        if action in selected:
            selected.remove(action)
        else:
            selected.append(action)

        await state.update_data(features=selected)
        with suppress(TelegramBadRequest):
            await callback.message.edit_reply_markup(
                reply_markup=get_multiselect_kb(FEATURES_OPTIONS, selected, "feat")
            )
    await callback.answer()

@router.message(BookingSteps.features_comment)
async def process_features_comment(message: Message, state: FSMContext):
    with suppress(TelegramBadRequest):
        await message.delete()

    await state.update_data(features_other_comment=message.text)
    await state.set_state(BookingSteps.schedule_type)

    text = "<b>Детали поездки</b>\nЭто разовая или регулярная поездка? 🚗"
    await update_interface(message.bot, state, text, get_schedule_type_kb())

# --- ШАГ 9: ДЕТАЛИ - РАЗОВАЯ ИЛИ РЕГУЛЯРНАЯ ---
@router.callback_query(F.data.startswith("sched_"), BookingSteps.schedule_type)
async def process_schedule_type(callback: CallbackQuery, state: FSMContext):
    sched_key = callback.data.split("_", 1)[1]
    schedule_text = SCHEDULE_OPTIONS.get(sched_key, "Разовая поездка")
    await state.update_data(schedule_type=schedule_text)
    await state.set_state(BookingSteps.extra_wishes)

    text = (
        "<b>Детали поездки</b>\n"
        "Хотите что-то добавить?\n\n"
        "Мы учтём любые пожелания: любимая музыка в дороге, аудиокнига, "
        "игрушка для ребёнка – просто напишите✍️"
    )
    await update_interface(callback.bot, state, text, get_extra_wishes_kb())
    await callback.answer()

# --- ШАГ 10: ДЕТАЛИ - ДОПОЛНИТЕЛЬНЫЕ ПОЖЕЛАНИЯ ---
async def show_confirmation_screen(bot: Bot, state: FSMContext):
    await state.set_state(BookingSteps.check_data)
    final_data = await state.get_data()
    text_result = generate_user_summary_text(final_data)
    await update_interface(bot, state, text_result, get_confirm_kb())

@router.callback_query(F.data == "skip_extra_wishes", BookingSteps.extra_wishes)
async def process_skip_extra_wishes(callback: CallbackQuery, state: FSMContext):
    await state.update_data(extra_wishes="Нет")
    await show_confirmation_screen(callback.bot, state)
    await callback.answer()

@router.message(BookingSteps.extra_wishes)
async def process_extra_wishes_text(message: Message, state: FSMContext):
    with suppress(TelegramBadRequest):
        await message.delete()

    await state.update_data(extra_wishes=message.text)
    await show_confirmation_screen(message.bot, state)

# --- ШАГ 11: ФОРМИРОВАНИЕ ТЕКСТА СВОДКИ И ОТПРАВКА ---
def get_data_strings(data: dict):
    # Как встретить
    meeting_list = [MEETING_OPTIONS.get(m, m) for m in data.get("meeting_details", [])]
    meeting_str = ", ".join(meeting_list) or "Стандартно"

    # Дополнительные условия
    features_list = [FEATURES_OPTIONS.get(f, f) for f in data.get("features", [])]
    features_str = ", ".join(features_list)
    if "features_other_comment" in data:
        features_str += f" (Комментарий: {html.escape(data['features_other_comment'])})"
    if not features_str:
        features_str = "Нет"

    # Тип поездки
    schedule_str = data.get("schedule_type", "Разовая поездка")

    # Дополнительные пожелания
    extra_wishes_str = html.escape(str(data.get("extra_wishes", "Нет")))

    return meeting_str, features_str, schedule_str, extra_wishes_str

def generate_user_summary_text(data: dict) -> str:
    meeting_str, features_str, schedule_str, extra_wishes_str = get_data_strings(data)
    
    return (
        f"✅ <b>Проверьте данные заявки:</b>\n"
        f"👤 <b>Имя:</b> {html.escape(str(data.get('name')))}\n"
        f"📞 <b>Телефон:</b> {html.escape(str(data.get('phone')))}\n"
        f"📅 <b>Дата:</b> {html.escape(str(data.get('booking_date')))} в {html.escape(str(data.get('booking_time')))}\n"
        f"🚗 <b>Маршрут:</b> {html.escape(str(data.get('route')))}\n"
        f"👶 <b>Возраст ребенка:</b> {html.escape(str(data.get('age')))}\n\n"
        f"🤝 <b>Встреча:</b> {meeting_str}\n"
        f"⚠️ <b>Условия:</b> {features_str}\n"
        f"🗓 <b>Поездка:</b> {schedule_str}\n"
        f"✍️ <b>Дополнительно:</b> {extra_wishes_str}\n\n"
        f"<blockquote expandable>"
        f"✨ Что мы предусмотрели для Вашего комфорта:\n\n"
        f"• Зарядка для телефона — всегда в машине\n"
        f"• Детская вода — по вашему желанию\n"
        f"• Маршрут фиксируем по 2GIS/Google Maps для точности\n"
        f"• Стоимость поездки фиксирована и меняется только если Вы просите подождать или меняете маршрут\n\n"
        f"💳 Как мы считаем стоимость:\n\n"
        f"• Вы платите только за путь с ребёнком в машине\n"
        f"• Дорога няни до Вас и обратно — не оплачивается\n"
        f"• Цена фиксирована, без скрытых надбавок\n"
        f"• Для поездок за город (свыше 10 км) — предусмотрена доплата, о которой мы предупредим заранее\n\n"
        f"Всё прозрачно, Вы всегда знаете, за что платите\n\n"
        f"Остались вопросы? Мы всегда на связи 🤝"
        f"</blockquote>"
    )

def generate_admin_text(data: dict, user_data) -> str:
    meeting_str, features_str, schedule_str, extra_wishes_str = get_data_strings(data)
    
    return (
        f"📩 <b>НОВАЯ ЗАЯВКА</b>\n"
        f"👤 <a href='tg://user?id={user_data.id}'>{html.escape(user_data.full_name)}</a> (@{html.escape(str(user_data.username)) if user_data.username else 'нет'})\n\n"
        f"<b>Имя:</b> {html.escape(str(data.get('name')))}\n"
        f"<b>Телефон:</b> {html.escape(str(data.get('phone')))}\n"
        f"<b>Дата и время:</b> {html.escape(str(data.get('booking_date')))} в {html.escape(str(data.get('booking_time')))}\n"
        f"<b>Маршрут:</b> {html.escape(str(data.get('route')))}\n"
        f"<b>Возраст ребенка:</b> {html.escape(str(data.get('age')))}\n\n"
        f"<b>Встреча:</b> {meeting_str}\n"
        f"<b>Условия:</b> {features_str}\n"
        f"<b>Поездка:</b> {schedule_str}\n"
        f"<b>Дополнительно:</b> {extra_wishes_str}"
    )

@router.callback_query(F.data == "restart_booking", BookingSteps.check_data)
async def restart_booking(callback: CallbackQuery, state: FSMContext):
    msg_id = callback.message.message_id
    chat_id = callback.message.chat.id
    
    await state.clear()
    await state.update_data(msg_id=msg_id, chat_id=chat_id)
    await state.set_state(BookingSteps.name)
    
    text = "Данные сброшены.\n\n<b>Как к Вам обращаться</b>?\n\n<i>(Ваше имя)</i>"
    await callback.message.edit_text(text, reply_markup=get_cancel_kb())
    await callback.answer()

@router.callback_query(F.data == "confirm_booking", BookingSteps.check_data)
async def confirm_booking(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    admin_text = generate_admin_text(data, callback.from_user)
    
    try:
        await callback.bot.send_message(chat_id=ADMIN_GROUP_ID, text=admin_text)

    except TelegramMigrateToChat as e:
        new_id = e.migrate_to_chat_id
        logging.warning(f"Group migrated to {new_id}. Resending...")

        try:
            await callback.bot.send_message(chat_id=new_id, text=admin_text)
        except Exception as e2:
            logging.error(f"Failed to send to new group ID: {e2}")
            await callback.answer("Ошибка отправки заявки администратору.", show_alert=True)
            return
             
    except Exception as e:
        logging.error(f"Admin send error: {e}")
        await callback.answer("Произошла ошибка при отправке заявки.", show_alert=True)
        return

    await callback.message.edit_text(
        "✅ <b>Заявка успешно отправлена!</b>\n\nСкоро с вами свяжется оператор для подтверждения.",
        reply_markup=None
    )
    await state.clear()
    await callback.answer()

