import aiosqlite

from aiogram import Router, F, Bot
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    ChatPermissions
)
from aiogram.fsm.context import FSMContext

from config import MOD_GROUP_ID
from database import DB
from states import (
    MuteState,
    BanState,
    WarnState
)
from utils import parse_time

router = Router()


async def is_helper(user_id: int):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT user_id FROM helpers WHERE user_id=?",
            (user_id,)
        )
        return await cur.fetchone() is not None


def moderation_kb(user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔇 Мут",
                    callback_data=f"mute:{user_id}"
                ),
                InlineKeyboardButton(
                    text="⚠️ Варн",
                    callback_data=f"warn:{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⛔ Бан",
                    callback_data=f"ban:{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Завершить",
                    callback_data="finish"
                )
            ]
        ]
    )


def confirm_mute_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="cancel_mute"
                ),
                InlineKeyboardButton(
                    text="✅ Выдать",
                    callback_data="confirm_mute"
                )
            ]
        ]
    )


@router.callback_query(F.data.startswith("review:"))
async def review(call: CallbackQuery):
    if not await is_helper(call.from_user.id):
        return await call.answer(
            "Нет доступа.",
            show_alert=True
        )

    user_id = int(call.data.split(":")[1])

    text = f"""
╭─ 📂 Репорт
├ 👤 Пользователь:
│ <code>{user_id}</code>
╰ Выберите действие.
"""

    await call.message.answer(
        text,
        reply_markup=moderation_kb(user_id)
    )

    await call.answer()


@router.callback_query(F.data.startswith("deny:"))
async def deny(
    call: CallbackQuery,
    bot: Bot
):
    if not await is_helper(call.from_user.id):
        return await call.answer(
            "Нет доступа.",
            show_alert=True
        )

    topic_id = int(call.data.split(":")[1])

    try:
        await bot.delete_forum_topic(
            chat_id=MOD_GROUP_ID,
            message_thread_id=topic_id
        )
    except:
        pass

    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "DELETE FROM tickets WHERE topic_id=?",
            (topic_id,)
        )
        await db.commit()

    await call.answer(
        "❌ Репорт отклонён."
    )


@router.callback_query(F.data == "finish")
async def finish(call: CallbackQuery):
    await call.message.answer(
        "✅ Тикет завершён."
    )
    await call.answer()


@router.callback_query(F.data.startswith("mute:"))
async def mute(
    call: CallbackQuery,
    state: FSMContext
):
    user_id = int(call.data.split(":")[1])

    await state.update_data(
        user_id=user_id
    )

    await state.set_state(
        MuteState.waiting_time
    )

    await call.message.answer(
        """
╭─ 🔇 Выдача мута
├ Примеры:
│ 30 минут
│ 1 час
│ 2 дня
╰ Введите срок:
"""
    )

    await call.answer()


@router.message(MuteState.waiting_time)
async def mute_time(
    message: Message,
    state: FSMContext
):
    await state.update_data(
        mute_time=message.text
    )

    await state.set_state(
        MuteState.waiting_reason
    )

    await message.answer(
        "📝 Укажите причину мута."
    )


@router.message(MuteState.waiting_reason)
async def mute_reason(
    message: Message,
    state: FSMContext
):
    await state.update_data(
        reason=message.text
    )

    data = await state.get_data()

    text = f"""
╭─ 📋 Подтверждение
├ 👤 Пользователь:
│ <code>{data['user_id']}</code>
├ 🔇 Наказание:
│ Мут
├ ⏳ Срок:
│ {data['mute_time']}
├ 📝 Причина:
│ {data['reason']}
╰ Выдать наказание?
"""

    await message.answer(
        text,
        reply_markup=confirm_mute_kb()
    )

    await state.set_state(
        MuteState.waiting_confirm
    )


@router.callback_query(F.data == "cancel_mute")
async def cancel_mute(
    call: CallbackQuery,
    state: FSMContext
):
    await state.clear()

    await call.message.answer(
        "❌ Выдача мута отменена."
    )

    await call.answer()


@router.callback_query(F.data == "confirm_mute")
async def confirm_mute(
    call: CallbackQuery,
    state: FSMContext,
    bot: Bot
):
    data = await state.get_data()

    user_id = data["user_id"]
    duration = data["mute_time"]
    reason = data["reason"]

    until = parse_time(duration)

    if not until:
        await call.message.answer(
            "❌ Неверный формат времени."
        )
        return

    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            """
            SELECT chat_id
            FROM tickets
            ORDER BY topic_id DESC
            LIMIT 1
            """
        )

        row = await cur.fetchone()

    if not row:
        await call.message.answer(
            "❌ Тикет не найден."
        )
        return

    chat_id = row[0]

        try:
        await bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=False
            ),
            until_date=until
        )
    except Exception as e:
        await call.message.answer(
            f"❌ Ошибка:\n{e}"
        )
        return

    async with aiosqlite.connect(DB) as db:
        await db.execute(
            """
            INSERT INTO punishments
            (
                user_id,
                moderator_id,
                action,
                reason,
                duration
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                call.from_user.id,
                "mute",
                reason,
                duration
            )
        )
        await db.commit()

    await call.message.answer(
        f"""
╭━━━ 🔇 МУТ ВЫДАН ━━━╮
┣ 👤 Пользователь:
┃ <code>{user_id}</code>
┣ ⏳ Срок:
┃ {duration}
┣ 📝 Причина:
┃ {reason}
╰━━━━━━━━━━━━━━━╯
"""
    )

    try:
        await bot.delete_forum_topic(
            chat_id=MOD_GROUP_ID,
            message_thread_id=call.message.message_thread_id
        )
    except:
        pass

    await state.clear()
    await call.answer()


@router.callback_query(F.data.startswith("warn:"))
async def warn(
    call: CallbackQuery,
    bot: Bot
):
    user_id = int(
        call.data.split(":")[1]
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

        if row:
            count = row[0] + 1

            await db.execute(
                """
                UPDATE warns
                SET count=?
                WHERE user_id=?
                """,
                (
                    count,
                    user_id
                )
            )
        else:
            count = 1

            await db.execute(
                """
                INSERT INTO warns
                VALUES (?, ?)
                """,
                (
                    user_id,
                    count
                )
            )

        await db.execute(
            """
            INSERT INTO punishments
            (
                user_id,
                moderator_id,
                action,
                reason,
                duration
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                call.from_user.id,
                "warn",
                "Варн",
                "-"
            )
        )

        await db.commit()

    text = f"""
╭━━ ⚠️ ВАРН ВЫДАН ━━╮
┣ 👤 Пользователь:
┃ <code>{user_id}</code>
┣ 📊 Всего варнов:
┃ {count}
╰━━━━━━━━━━━━━━╯
"""

    if count >= 3:
        text += "\n⚠️ Достигнуто 3 варна."

    if count >= 5:
        text += "\n⛔ Достигнуто 5 варнов."

    await call.message.answer(text)

    try:
        await bot.delete_forum_topic(
            chat_id=MOD_GROUP_ID,
            message_thread_id=call.message.message_thread_id
        )
    except:
        pass

    await call.answer()


@router.callback_query(F.data.startswith("ban:"))
async def ban(
    call: CallbackQuery,
    bot: Bot
):
    user_id = int(
        call.data.split(":")[1]
    )

    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            """
            SELECT chat_id
            FROM tickets
            ORDER BY topic_id DESC
            LIMIT 1
            """
        )

        row = await cur.fetchone()

    if not row:
        return await call.answer(
            "❌ Тикет не найден.",
            show_alert=True
        )

    chat_id = row[0]

    try:
        await bot.ban_chat_member(
            chat_id=chat_id,
            user_id=user_id
        )
    except Exception as e:
        return await call.message.answer(
            f"❌ Ошибка:\n{e}"
        )

    async with aiosqlite.connect(DB) as db:
        await db.execute(
            """
            INSERT INTO punishments
            (
                user_id,
                moderator_id,
                action,
                reason,
                duration
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                call.from_user.id,
                "ban",
                "Бан",
                "Навсегда"
            )
        )

        await db.commit()

    await call.message.answer(
        f"""
╭━━ ⛔ БАН ВЫДАН ━━╮
┣ 👤 Пользователь:
┃ <code>{user_id}</code>
┣ 👮 Модератор:
┃ <code>{call.from_user.id}</code>
╰━━━━━━━━━━━━━━╯
"""
    )

    try:
        await bot.delete_forum_topic(
            chat_id=MOD_GROUP_ID,
            message_thread_id=call.message.message_thread_id
        )
    except:
        pass

    await call.answer()


@router.message(F.text.startswith("/history"))
async def history(
    message: Message
):
    if not message.reply_to_message:
        return await message.answer(
            "Ответьте на сообщение пользователя."
        )

    user_id = message.reply_to_message.from_user.id

    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            """
            SELECT action, reason, duration
            FROM punishments
            WHERE user_id=?
            """,
            (user_id,)
        )

        rows = await cur.fetchall()

    if not rows:
        return await message.answer(
            "История наказаний пуста."
        )

    text = f"""
╭━━ 📋 ИСТОРИЯ ━━╮
┣ 👤 ID:
┃ <code>{user_id}</code>
"""

    for action, reason, duration in rows:
        text += (
            f"\n┣ {action.upper()}"
            f"\n┃ Причина: {reason}"
            f"\n┃ Срок: {duration}"
        )

    text += "\n╰━━━━━━━━━━━━━━╯"

    await message.answer(text)
