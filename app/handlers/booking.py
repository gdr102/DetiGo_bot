import re
import html
import logging

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest, TelegramMigrateToChat

from contextlib import suppress

from app.states import BookingSteps
from app.keyboards.start_kb import start_kb

from app.keyboards.booking_kb import (
    get_age_kb, get_multiselect_kb, 
    get_confirm_kb, get_inline_back_kb, get_cancel_kb
)

router = Router()
ADMIN_GROUP_ID = -1003871687123

# --- ОПЦИИ ---
WISHES_OPTIONS = {
    "meet": "Встретить ребенка",
    "pickup": "Забрать из помещения",
    "dress": "Помочь переодеться",
    "other": "Другое"
}

FEATURES_OPTIONS = {
    "grunt": "Грунтовая дорога",
    "morekids": "Более 1 ребенка",
    "wait": "Ожидание",
    "extrastop": "Доп. заезд",
    "other": "Другое"
}

DAYS_OPTIONS = {
    "once": "Разовая поездка",
    "mon": "Понедельник", "tue": "Вторник", "wed": "Среда",
    "thu": "Четверг", "fri": "Пятница", "sat": "Суббота", "sun": "Воскресенье"
}

# --- УТИЛИТА ИНТЕРФЕЙСА ---
async def update_interface(state: FSMContext, text: str, reply_markup=None):
    data = await state.get_data()
    msg_id = data.get("msg_id")
    chat_id = data.get("chat_id")
    bot: Bot = data.get("bot_instance")

    if msg_id and chat_id and bot:
        with suppress(TelegramBadRequest):
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=text,
                reply_markup=reply_markup
            )
            return
        
    else:
        pass

# --- Обработчик ОТМЕНЫ ---
@router.callback_query(F.data == "cancel_booking")
async def process_cancel(callback: CallbackQuery, state: FSMContext):
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
    
    if current_state == BookingSteps.phone:
        await state.set_state(BookingSteps.name)
        await update_interface(state, "Как к Вам обращаться? (Имя родителя)", get_cancel_kb())
        
    elif current_state == BookingSteps.child_age:
        await state.set_state(BookingSteps.phone)
        await update_interface(state, "Ваш телефон (Форматы: +7..., 8..., 7...):", get_inline_back_kb())
        
    elif current_state == BookingSteps.booking_date:
        await state.set_state(BookingSteps.child_age)
        await update_interface(state, "Выберите возраст ребенка:", get_age_kb())

    elif current_state == BookingSteps.booking_time:
        await state.set_state(BookingSteps.booking_date)
        await update_interface(state, "Удобная дата поездки (дд.мм.гггг):", get_inline_back_kb())
        
    elif current_state == BookingSteps.route:
        await state.set_state(BookingSteps.booking_time)
        await update_interface(state, "Удобное время подачи (чч:мм):", get_inline_back_kb())

    elif current_state == BookingSteps.wishes:
        await state.set_state(BookingSteps.route)
        await update_interface(state, "Укажите маршрут (Откуда → Куда):", get_inline_back_kb())
        
    elif current_state == BookingSteps.wishes_comment:
        await state.set_state(BookingSteps.wishes)
        data = await state.get_data()
        selected = data.get("wishes", [])
        await update_interface(state, "Выберите особые пожелания:", get_multiselect_kb(WISHES_OPTIONS, selected, "wish"))

    elif current_state == BookingSteps.route_features:
        await state.set_state(BookingSteps.wishes)
        data = await state.get_data()
        selected = data.get("wishes", [])
        await update_interface(state, "Выберите особые пожелания:", get_multiselect_kb(WISHES_OPTIONS, selected, "wish"))

    # Логика возврата из ввода комментария к особенностям
    elif current_state == BookingSteps.features_comment:
        await state.set_state(BookingSteps.route_features)
        data = await state.get_data()
        selected = data.get("features", [])
        await update_interface(state, "Особенности маршрута:", get_multiselect_kb(FEATURES_OPTIONS, selected, "feat"))

    elif current_state == BookingSteps.schedule:
        await state.set_state(BookingSteps.route_features)
        data = await state.get_data()
        selected = data.get("features", [])
        await update_interface(state, "Особенности маршрута:", get_multiselect_kb(FEATURES_OPTIONS, selected, "feat"))
        
    elif current_state == BookingSteps.check_data:
        await state.set_state(BookingSteps.schedule)
        data = await state.get_data()
        selected = data.get("schedule", [])
        await update_interface(state, "Заказы по расписанию (дни недели):", get_multiselect_kb(DAYS_OPTIONS, selected, "day"))

    await callback.answer()

# --- ШАГИ БРОНИРОВАНИЯ ---
@router.callback_query(F.data == "start_booking")
async def start_booking_process(callback: CallbackQuery, state: FSMContext):
    await state.update_data(msg_id=callback.message.message_id, chat_id=callback.message.chat.id, bot_instance=callback.bot)
    await state.set_state(BookingSteps.name)

    await callback.message.edit_text("Как к Вам обращаться? (Имя родителя)", reply_markup=get_cancel_kb())

@router.message(BookingSteps.name)
async def process_name(message: Message, state: FSMContext):
    await message.delete()

    await state.update_data(name=message.text)
    await state.set_state(BookingSteps.phone)

    await update_interface(state, "Ваш телефон (Форматы: +7..., 8..., 7...):", get_inline_back_kb())

@router.message(BookingSteps.phone)
async def process_phone(message: Message, state: FSMContext):
    raw_phone = message.text

    try:
        await message.delete()
    except:
        pass

    clean_phone = re.sub(r'[^\d+]', '', raw_phone) 
    
    is_valid = False
    if clean_phone.startswith("+7") and len(clean_phone) == 12:
        is_valid = True

    elif clean_phone.startswith("8") and len(clean_phone) == 11:
        is_valid = True

    elif clean_phone.startswith("7") and len(clean_phone) == 11:
        is_valid = True
        
    if not is_valid:
        await update_interface(state, "⚠️ Неверный формат номера.\nПожалуйста, введите номер в формате +79990000000 или 89990000000:", get_inline_back_kb())
        
        return

    await state.update_data(phone=raw_phone)
    await state.set_state(BookingSteps.child_age)

    await update_interface(state, "Спасибо! Укажите возраст ребенка:", get_age_kb())

@router.callback_query(F.data.startswith("age_"), BookingSteps.child_age)
async def process_age(callback: CallbackQuery, state: FSMContext):
    age_map = {"age_0-3": "0-3 года", "age_4-6": "4-6 лет", "age_7+": "7+ лет"}

    selected_age = age_map.get(callback.data)

    await state.update_data(age=selected_age)
    await state.set_state(BookingSteps.booking_date)

    await update_interface(state, "Удобная дата поездки (дд.мм.гггг):", get_inline_back_kb())

    await callback.answer()

@router.message(BookingSteps.booking_date)
async def process_date(message: Message, state: FSMContext):
    await message.delete()

    await state.update_data(booking_date=message.text)
    await state.set_state(BookingSteps.booking_time)

    await update_interface(state, "Удобное время подачи (чч:мм):", get_inline_back_kb())

@router.message(BookingSteps.booking_time)
async def process_time(message: Message, state: FSMContext):
    await message.delete()

    await state.update_data(booking_time=message.text)
    await state.set_state(BookingSteps.route)

    await update_interface(state, "Маршрут (Откуда → Куда):", get_inline_back_kb())

@router.message(BookingSteps.route)
async def process_route(message: Message, state: FSMContext):
    await message.delete()

    await state.update_data(route=message.text)
    await state.update_data(wishes=[]) 
    await state.set_state(BookingSteps.wishes)

    await update_interface(state, "Особые пожелания (можно выбрать несколько):", get_multiselect_kb(WISHES_OPTIONS, [], "wish"))

@router.callback_query(F.data.startswith("wish_"), BookingSteps.wishes)
async def process_wishes_select(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_", 1)[1]
    data = await state.get_data()
    selected = data.get("wishes", [])

    if action == "done":
        if "other" in selected:
            await state.set_state(BookingSteps.wishes_comment)
            await update_interface(state, "Вы выбрали 'Другое'. Напишите, пожалуйста, комментарий:", get_inline_back_kb())
        
        else:
            await state.update_data(features=[])
            await state.set_state(BookingSteps.route_features)
            await update_interface(state, "Особенности маршрута:", get_multiselect_kb(FEATURES_OPTIONS, [], "feat"))
    
    else:
        if action in selected:
            selected.remove(action)
        
        else:
            selected.append(action)
        
        await state.update_data(wishes=selected)

        with suppress(TelegramBadRequest):
            await callback.message.edit_reply_markup(reply_markup=get_multiselect_kb(WISHES_OPTIONS, selected, "wish"))
    
    await callback.answer()

@router.message(BookingSteps.wishes_comment)
async def process_wishes_comment(message: Message, state: FSMContext):
    await message.delete()

    await state.update_data(other_comment=message.text)
    await state.update_data(features=[])
    await state.set_state(BookingSteps.route_features)

    await update_interface(state, "Особенности маршрута:", get_multiselect_kb(FEATURES_OPTIONS, [], "feat"))

@router.callback_query(F.data.startswith("feat_"), BookingSteps.route_features)
async def process_features_select(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_", 1)[1] 
    data = await state.get_data()
    selected = data.get("features", [])

    if action == "done":
        # Проверяем, выбрано ли "Другое"
        if "other" in selected:
             await state.set_state(BookingSteps.features_comment)
             await update_interface(state, "Вы выбрали 'Другое'. Напишите, пожалуйста, комментарий:", get_inline_back_kb())

        else:
            await state.update_data(schedule=[])
            await state.set_state(BookingSteps.schedule)
            await update_interface(state, "Заказы по расписанию (дни недели):", get_multiselect_kb(DAYS_OPTIONS, [], "day"))

    else:
        if action in selected:
            selected.remove(action)

        else:
            selected.append(action)
        
        await state.update_data(features=selected)

        with suppress(TelegramBadRequest):
            await callback.message.edit_reply_markup(reply_markup=get_multiselect_kb(FEATURES_OPTIONS, selected, "feat"))
            
    await callback.answer()

@router.message(BookingSteps.features_comment)
async def process_features_comment(message: Message, state: FSMContext):
    await message.delete()

    await state.update_data(features_other_comment=message.text)
    await state.update_data(schedule=[])
    await state.set_state(BookingSteps.schedule)

    await update_interface(state, "Заказы по расписанию (дни недели):", get_multiselect_kb(DAYS_OPTIONS, [], "day"))

@router.callback_query(F.data.startswith("day_"), BookingSteps.schedule)
async def process_schedule_select(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_", 1)[1]
    data = await state.get_data()
    selected = data.get("schedule", [])

    if action == "done":
        final_data = await state.get_data()
        text_result = generate_user_summary_text(final_data)
        
        await state.set_state(BookingSteps.check_data)

        await update_interface(state, text_result, get_confirm_kb())
    else:
        if action in selected:
            selected.remove(action)

        else:
            selected.append(action)
        
        await state.update_data(schedule=selected)
        
        with suppress(TelegramBadRequest):
            await callback.message.edit_reply_markup(reply_markup=get_multiselect_kb(DAYS_OPTIONS, selected, "day"))
            
    await callback.answer()

# --- ФУНКЦИИ ГЕНЕРАЦИИ ТЕКСТА (HTML) ---
def get_data_strings(data: dict):
    # Пожелания
    wishes_list = [WISHES_OPTIONS.get(w, w) for w in data.get("wishes", [])]
    wishes_str = ", ".join(wishes_list)

    if "other_comment" in data:
        wishes_str += f" (Комментарий: {html.escape(data['other_comment'])})"

    if not wishes_str: wishes_str = "Нет"

    # Особенности
    features_list = [FEATURES_OPTIONS.get(f, f) for f in data.get("features", [])]
    features_str = ", ".join(features_list)

    if "features_other_comment" in data:
        features_str += f" (Комментарий: {html.escape(data['features_other_comment'])})"

    if not features_str: features_str = "Нет"
    
    # Расписание
    schedule_list = [DAYS_OPTIONS.get(d, d) for d in data.get("schedule", [])]
    schedule_str = ", ".join(schedule_list) or "Разовая поездка"
    
    return wishes_str, features_str, schedule_str

def generate_user_summary_text(data: dict) -> str:
    wishes_str, features_str, schedule_str = get_data_strings(data)
    
    return (
        f"✅ <b>Проверьте данные заявки:</b>\n"
        f"👤 <b>Имя:</b> {html.escape(str(data.get('name')))}\n"
        f"📞 <b>Телефон:</b> {html.escape(str(data.get('phone')))}\n"
        f"👶 <b>Возраст:</b> {data.get('age')}\n"
        f"📅 <b>Дата:</b> {html.escape(str(data.get('booking_date')))} в {html.escape(str(data.get('booking_time')))}\n"
        f"🚗 <b>Маршрут:</b> {html.escape(str(data.get('route')))}\n\n"
        f"✨ <b>Пожелания:</b> {wishes_str}\n"
        f"⚠️ <b>Особенности:</b> {features_str}\n"
        f"🗓 <b>Расписание:</b> {schedule_str}\n\n"
        f"ℹ️ <b>Важно:</b>\n"
        f"• Фиксируем маршрут через 2GIS\n"
        f"• Сумма меняется при доп. ожидании, смене маршрута или доп. опциях (вода 0,33л - 60₽)\n"
        f"• Зарядка в машине бесплатно\n\n"
        f"💡 <b>Обратите внимание:</b>\n"
        f"• Оплата только за путь с ребенком.\n"
        f"• Подача авто не оплачивается.\n"
        f"• Доплата от +150₽ за отдаленные районы (>10км от центра)."
    )

def generate_admin_text(data: dict, user_data) -> str:
    wishes_str, features_str, schedule_str = get_data_strings(data)
    
    return (
        f"📩 <b>НОВАЯ ЗАЯВКА</b>\n"
        f"👤 <a href='tg://user?id={user_data.id}'>{html.escape(user_data.full_name)}</a> (@{html.escape(str(user_data.username)) if user_data.username else 'нет'})\n\n"
        f"<b>Имя:</b> {html.escape(str(data.get('name')))}\n"
        f"<b>Телефон:</b> {html.escape(str(data.get('phone')))}\n"
        f"<b>Ребенок:</b> {data.get('age')}\n"
        f"<b>Дата:</b> {html.escape(str(data.get('booking_date')))} {html.escape(str(data.get('booking_time')))}\n"
        f"<b>Маршрут:</b> {html.escape(str(data.get('route')))}\n\n"
        f"<b>Пожелания:</b> {wishes_str}\n"
        f"<b>Особенности:</b> {features_str}\n"
        f"<b>Расписание:</b> {schedule_str}"
    )

@router.callback_query(F.data == "restart_booking", BookingSteps.check_data)
async def restart_booking(callback: CallbackQuery, state: FSMContext):
    msg_id = callback.message.message_id
    chat_id = callback.message.chat.id
    bot = callback.bot
    
    await state.clear()
    await state.update_data(msg_id=msg_id, chat_id=chat_id, bot_instance=bot)
    await state.set_state(BookingSteps.name)
    
    await callback.message.edit_text("Данные сброшены.\nКак к Вам обращаться? (Имя родителя)", reply_markup=get_cancel_kb())
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
