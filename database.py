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

        # Banned Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS banned_users (
                user_id INTEGER PRIMARY KEY
            )
        """)

        # Broadcast Disabled Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS broadcast_disabled_users (
                user_id INTEGER PRIMARY KEY
            )
        """)

        # Welcome Message Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS welcome_message (
                id INTEGER PRIMARY KEY,
                message TEXT
            )
        """)

        conn.commit()

# Functions for Users

def add_user(user_id, username):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()

def all_users():
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username FROM users")
        return [{"user_id": row[0], "username": row[1]} for row in cursor.fetchall()]

def remove_user(user_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()

def is_banned(user_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT banned FROM users WHERE user_id = ?", (user_id,))
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

def all_banned_users():
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE banned = 1")
        return [{"user_id": row[0]} for row in cursor.fetchall()]

# Functions for Broadcast

def disable_broadcast_for_user(user_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO broadcast_disabled_users (user_id) VALUES (?)", (user_id,))
        conn.commit()

def enable_broadcast(user_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM broadcast_disabled_users WHERE user_id = ?", (user_id,))
        conn.commit()

def all_disabled_broadcast_users():
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM broadcast_disabled_users")
        return [{"user_id": row[0]} for row in cursor.fetchall()]

# Functions for Admin

def is_admin(user_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result is not None

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

# Functions for Welcome Message

def set_welcome_message(message):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM welcome_message")  # Ensure only one record
        cursor.execute("INSERT INTO welcome_message (message) VALUES (?)", (message,))
        conn.commit()

def get_welcome_message():
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT message FROM welcome_message LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else None

# Functions for User Channels

def get_user_channels(user_id):
    # You can implement a logic to get user channels if necessary
    return []

def is_broadcast_disabled(user_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM broadcast_disabled_users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result is not None

# Initialize database
initialize_database()
