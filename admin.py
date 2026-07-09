from aiogram import Router, F
from aiogram.types import Message
import aiosqlite

from database import DB

router = Router()


@router.message(F.text.startswith("/newhelp"))
async def new_helper(message: Message):
    if not message.reply_to_message:
        return await message.answer(
            "Ответьте на сообщение пользователя."
        )

    user_id = (
        message.reply_to_message
        .from_user.id
    )

    async with aiosqlite.connect(DB) as db:
        await db.execute(
            """
            INSERT OR IGNORE
            INTO helpers
            VALUES (?)
            """,
            (user_id,)
        )
        await db.commit()

    await message.answer(
        "✅ Хелпер назначен."
    )


@router.message(F.text.startswith("/delhelp"))
async def del_helper(message: Message):
    if not message.reply_to_message:
        return await message.answer(
            "Ответьте на сообщение пользователя."
        )

    user_id = (
        message.reply_to_message
        .from_user.id
    )

    async with aiosqlite.connect(DB) as db:
        await db.execute(
            """
            DELETE FROM helpers
            WHERE user_id=?
            """,
            (user_id,)
        )
        await db.commit()

    await message.answer(
        "❌ Хелпер снят."
    )