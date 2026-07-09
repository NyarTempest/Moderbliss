from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


def ticket_kb(user_id, topic_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Рассмотреть",
                    callback_data=f"review:{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отказать",
                    callback_data=f"deny:{topic_id}"
                )
            ]
        ]
    )