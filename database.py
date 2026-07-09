import aiosqlite

DB = "bot.db"


async def init_db():
    async with aiosqlite.connect(DB) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS warns(
            user_id INTEGER PRIMARY KEY,
            count INTEGER DEFAULT 0
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS punishments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            moderator_id INTEGER,
            action TEXT,
            reason TEXT,
            duration TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS tickets(
            topic_id INTEGER PRIMARY KEY,
            user_id INTEGER,
            reporter_id INTEGER,
            reason TEXT,
            chat_id INTEGER,
            message_id INTEGER
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS helpers(
            user_id INTEGER PRIMARY KEY
        )
        """)

        await db.commit()