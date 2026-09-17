from aiogram.fsm.state import State, StatesGroup


class AddProvider(StatesGroup):
    choosing_kind = State()          # chat / image / video
    choosing_preset = State()        # یکی از پرووایدرهای معروف یا کاستوم
    entering_custom_url = State()
    entering_api_key = State()
    entering_custom_model = State()  # برای replicate که لیست مدل نداره
    choosing_model = State()


class Settings(StatesGroup):
    entering_daily_limit = State()
    entering_monthly_limit = State()
    entering_temperature = State()
    entering_code_timeout = State()


class ChatMode(StatesGroup):
    chatting = State()
