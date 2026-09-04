from aiogram.fsm.state import StatesGroup, State

class BookingSteps(StatesGroup):
    name = State()              # 1. Имя
    phone = State()             # 2. Телефон
    booking_date = State()      # 3. Дата поездки
    booking_time = State()      # 4. Время поездки
    route = State()             # 5. Маршрут
    child_age = State()         # 6. Возраст ребенка
    meeting_details = State()   # 7. Как встретить ребенка (мультивыбор)
    route_features = State()    # 8. Дополнительные условия (мультивыбор)
    features_comment = State()  # 8a. Комментарий для "Другое"
    schedule_type = State()     # 9. Разовая или регулярная поездка
    extra_wishes = State()      # 10. Дополнительные пожелания
    check_data = State()        # 11. Проверка данных

    