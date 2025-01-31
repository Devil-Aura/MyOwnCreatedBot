import sqlite3

db_name = "bot_database.db"

def initialize_database():
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        
        # Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                banned INTEGER DEFAULT 0,
                broadcast_disabled INTEGER DEFAULT 0
            )
        """)

        # Admins Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY
            )
        """)

        # Other tables...

        conn.commit()


def add_admin(user_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
        conn.commit()


def all_admins():
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM admins")
        return [{"user_id": row[0]} for row in cursor.fetchall()]


def all_users():
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username FROM users")
        return [{"user_id": row[0], "username": row[1]} for row in cursor.fetchall()]


def is_banned(user_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT banned FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result and result[0] == 1


def is_broadcast_disabled(user_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT broadcast_disabled FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result and result[0] == 1


def ban_user(user_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET banned = 1 WHERE user_id = ?", (user_id,))
        conn.commit()


def unban_user(user_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET banned = 0 WHERE user_id = ?", (user_id,))
        conn.commit()


def disable_broadcast_for_user(user_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET broadcast_disabled = 1 WHERE user_id = ?", (user_id,))
        conn.commit()


def enable_broadcast(user_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET broadcast_disabled = 0 WHERE user_id = ?", (user_id,))
        conn.commit()


def set_welcome_message(message):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE settings SET welcome_message = ? WHERE id = 1", (message,))
        conn.commit()


def get_welcome_message():
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT welcome_message FROM settings WHERE id = 1")
        result = cursor.fetchone()
        return result[0] if result else "Welcome to the bot!"


def get_user_channels():
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT channel_name FROM channels")
        return "\n".join([row[0] for row in cursor.fetchall()])


initialize_database()
