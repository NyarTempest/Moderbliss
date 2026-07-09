from aiogram import Router, F
from aiogram.types import Message
from aiogram import Bot
import aiosqlite

from config import MOD_GROUP_ID
from keyboards import ticket_kb
from database import DB

router = Router()


@router.message(F.text.lower().startswith("репорт"))
async def report(message: Message, bot: Bot):
    if not message.reply_to_message:
        return await message.answer(
            "❌ Используйте репорт ответом на сообщение."
        )

    offender = message.reply_to_message.from_user
    reporter = message.from_user

    reason = message.text[6:].strip()

    if not reason:
        reason = "Без причины"

    try:
        topic = await bot.create_forum_topic(
            chat_id=MOD_GROUP_ID,
            name=reason[:128]
        )
    except:
        return await message.answer(
            "❌ Не удалось создать тему."
        )

    topic_id = topic.message_thread_id

    if message.chat.username:
        link = (
            f"https://t.me/"
            f"{message.chat.username}/"
            f"{message.reply_to_message.message_id}"
        )
    else:
        link = "Ссылка недоступна"

    text = f"""
╭─ 🚨 Новый репорт
├ 👤 Репортёр:
│  {reporter.mention_html()}
├ 🎯 Нарушитель:
│  {offender.mention_html()}
├ 🆔 ID:
│  <code>{offender.id}</code>
├ 📌 Причина:
│  {reason}
├ 🔗 Ссылка:
│  {link}
╰ Ожидает проверки.
"""

    await bot.send_message(
        chat_id=MOD_GROUP_ID,
        message_thread_id=topic_id,
        text=text,
        reply_markup=ticket_kb(
            offender.id,
            topic_id
        )
    )

    async with aiosqlite.connect(DB) as db:
        await db.execute(
            """
            INSERT INTO tickets
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                topic_id,
                offender.id,
                reporter.id,
                reason,
                message.chat.id,
                message.reply_to_message.message_id
            )
        )

        await db.commit()

    await message.reply(
        "✅ Репорт отправлен модераторам."
    )