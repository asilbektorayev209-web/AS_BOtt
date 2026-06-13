from aiogram.fsm.state import State, StatesGroup


class BroadcastStates(StatesGroup):
    choosing_target = State()
    waiting_new_target = State()
    waiting_user_id = State()
    waiting_content = State()
    waiting_buttons = State()
    confirm = State()


class PostStates(StatesGroup):
    choosing_media = State()
    waiting_media = State()
    waiting_text = State()
    choosing_buttons = State()
    waiting_buttons = State()
    choosing_target = State()
    waiting_new_target = State()
    confirm = State()


class AdminManageStates(StatesGroup):
    waiting_add_id = State()
    waiting_remove_id = State()
