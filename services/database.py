import sqlite3


connection = sqlite3.connect(
    "database/credits.db",
    check_same_thread=False
)

cursor = connection.cursor()


# Users table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (

        user_id INTEGER PRIMARY KEY,

        credits INTEGER NOT NULL

    )
""")


# Payments table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        link_id TEXT UNIQUE NOT NULL,

        user_id INTEGER NOT NULL,

        credits INTEGER NOT NULL,

        amount REAL NOT NULL,

        status TEXT NOT NULL,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
""")


connection.commit()