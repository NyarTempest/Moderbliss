from aiogram.fsm.state import State, StatesGroup


class MuteState(StatesGroup):
    waiting_time = State()
    waiting_reason = State()
    waiting_confirm = State()


class BanState(StatesGroup):
    waiting_reason = State()
    waiting_confirm = State()


class WarnState(StatesGroup):
    waiting_reason = State()
    waiting_confirm = State()