import aiosqlite

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from config import MOD_GROUP_ID
from database import DB

router = Router()


def report_kb(user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👮 Рассмотреть",
                    callback_data=f"review:{user_id}"
                )
            ]
        ]
    )


@router.message(
    Command("report") |
    F.text.lower().startswith("репорт")
)
async def report(
    message: Message,
    bot: Bot
):
    if not message.reply_to_message:
        return await message.answer(
            "❌ Ответьте на сообщение нарушителя."
        )

    reported = message.reply_to_message.from_user

    reason = (
        message.text
        .replace("/report", "")
        .replace("репорт", "")
        .strip()
    )

    if not reason:
        reason = "Причина не указана"

    try:
        topic = await bot.create_forum_topic(
            chat_id=MOD_GROUP_ID,
            name=f"Репорт | {reported.id}"
        )
    except Exception as e:
        return await message.answer(
            f"❌ Ошибка создания тикета:\n{e}"
        )

    topic_id = topic.message_thread_id

    async with aiosqlite.connect(DB) as db:
        await db.execute(
            """
            INSERT INTO tickets
            (
                user_id,
                chat_id,
                topic_id
            )
            VALUES (?, ?, ?)
            """,
            (
                reported.id,
                message.chat.id,
                topic_id
            )
        )
        await db.commit()

    text = f"""
╭━━ 📂 НОВЫЙ РЕПОРТ ━━╮
┣ 👤 Пользователь:
┃ {reported.full_name}
┣ 🆔 ID:
┃ <code>{reported.id}</code>
┣ 📝 Причина:
┃ {reason}
┣ 💬 Чат:
┃ <code>{message.chat.id}</code>
╰━━━━━━━━━━━━━━╯
"""

    await bot.send_message(
        chat_id=MOD_GROUP_ID,
        message_thread_id=topic_id,
        text=text,
        reply_markup=report_kb(
            reported.id
        )
    )

    await message.answer(
        "✅ Репорт отправлен модерации."
    )
