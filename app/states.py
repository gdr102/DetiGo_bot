from aiogram.fsm.state import StatesGroup, State

class BookingSteps(StatesGroup):
    name = State()              # Имя
    phone = State()             # Телефон
    child_age = State()         # Возраст
    booking_date = State()      # Дата
    booking_time = State()      # Время
    route = State()             # Маршрут
    wishes = State()            # Пожелания (мультивыбор)
    wishes_comment = State()    # Комментарий для "Другое"
    route_features = State()    # Особенности маршрута (мультивыбор)
    features_comment = State()  # Комментарий для "Другое"
    schedule = State()          # Расписание (мультивыбор)
    check_data = State()        # Проверка данных
    