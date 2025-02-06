import sqlite3

DB_NAME = "bot_database.db"

# Create Tables
def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    """)

    # Groups/Channels Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            chat_id INTEGER PRIMARY KEY
        )
    """)

    # Disabled Broadcast Users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disabled_broadcast (
            user_id INTEGER PRIMARY KEY
        )
    """)

    # Banned Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY
        )
    """)

    # Welcome Messages Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS welcome_messages (
            chat_id INTEGER PRIMARY KEY,
            message TEXT
        )
    """)

    conn.commit()
    conn.close()

#━━━━━━━━━━━━━━━━━━━━━━━ User Management ━━━━━━━━━━━━━━━━━━━━━━━

def add_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def remove_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

#━━━━━━━━━━━━━━━━━━━━━━━ Group/Channel Management ━━━━━━━━━━━━━━━━━━━━━━━

def add_group(chat_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO groups (chat_id) VALUES (?)", (chat_id,))
    conn.commit()
    conn.close()

def all_groups():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM groups")
    count = cursor.fetchone()[0]
    conn.close()
    return count

#━━━━━━━━━━━━━━━━━━━━━━━ Broadcast Control ━━━━━━━━━━━━━━━━━━━━━━━

def disable_broadcast(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO disabled_broadcast (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def enable_broadcast(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM disabled_broadcast WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def is_broadcast_disabled(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM disabled_broadcast WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_disabled_broadcast_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM disabled_broadcast")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

#━━━━━━━━━━━━━━━━━━━━━━━ Ban Management ━━━━━━━━━━━━━━━━━━━━━━━

def ban_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def is_user_banned(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM banned_users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_banned_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM banned_users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

#━━━━━━━━━━━━━━━━━━━━━━━ Welcome Message Management ━━━━━━━━━━━━━━━━━━━━━━━

def set_welcome_message(chat_id, message):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO welcome_messages (chat_id, message) VALUES (?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET message = ?
    """, (chat_id, message, message))
    conn.commit()
    conn.close()

def get_welcome_message(chat_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT message FROM welcome_messages WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

#━━━━━━━━━━━━━━━━━━━━━━━ User-Channel Tracking ━━━━━━━━━━━━━━━━━━━━━━━

def get_user_channels():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    
    channels = {}
    for user in users:
        user_id = user[0]
        username = f"User-{user_id}"
        chat_title = f"Chat-{user_id}"
        chat_url = f"https://t.me/chat{user_id}"
        channels[user_id] = {"username": username, "chat_title": chat_title, "chat_url": chat_url}
    
    return channels

#━━━━━━━━━━━━━━━━━━━━━━━ Initialize Database ━━━━━━━━━━━━━━━━━━━━━━━

create_tables()
