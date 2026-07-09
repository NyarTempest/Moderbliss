from aiogram import Router
from aiogram.types import Message
import aiosqlite

from database import DB

router = Router()


@router.message()
async def commands(message: Message):
    if not message.text:
        return

    if message.text.startswith("/warns"):
        if not message.reply_to_message:
            return

        user_id = (
            message.reply_to_message
            .from_user.id
        )

        async with aiosqlite.connect(DB) as db:
            cur = await db.execute(
                """
                SELECT count
                FROM warns
                WHERE user_id=?
                """,
                (user_id,)
            )

            row = await cur.fetchone()

        count = row[0] if row else 0

        await message.answer(
            f"⚠️ Варнов: {count}"
        )