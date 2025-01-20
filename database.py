import sqlite3

# Database Initialization
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

        # Banned Users Log Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS banned_users (
                user_id INTEGER PRIMARY KEY,
                ban_reason TEXT
            )
        """)

        # Welcome Message Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS welcome_messages (
                id INTEGER PRIMARY KEY,
                message TEXT
            )
        """)

        # User Channels Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_channels (
                user_id INTEGER,
                chat_id INTEGER,
                chat_name TEXT,
                PRIMARY KEY (user_id, chat_id)
            )
        """)

        conn.commit()

# Add a User
def add_user(user_id, username=None):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO users (user_id, username)
            VALUES (?, ?)
        """, (user_id, username))
        conn.commit()

# Remove a User
def remove_user(user_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()

# Log User Data
def log_user_data(user_id, username, log_channel):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO users (user_id, username)
            VALUES (?, ?)
        """, (user_id, username))
        conn.commit()

# Get All Users
def all_users():
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        return [{"user_id": row[0]} for row in cursor.fetchall()]

# Check if a User is Banned
def is_banned(user_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT banned FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] == 1 if result else False

# Ban a User
def ban_user(user_id, reason="No reason provided"):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO banned_users (user_id, ban_reason)
            VALUES (?, ?)
        """, (user_id, reason))
        cursor.execute("""
            UPDATE users SET banned = 1 WHERE user_id = ?
        """, (user_id,))
        conn.commit()

# Unban a User
def unban_user(user_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM banned_users WHERE user_id = ?
        """, (user_id,))
        cursor.execute("""
            UPDATE users SET banned = 0 WHERE user_id = ?
        """, (user_id,))
        conn.commit()

# Get All Banned Users
def all_banned_users():
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, ban_reason FROM banned_users")
        return [{"user_id": row[0], "ban_reason": row[1]} for row in cursor.fetchall()]

# Disable Broadcast for a User
def disable_broadcast_for_user(user_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET broadcast_disabled = 1 WHERE user_id = ?
        """, (user_id,))
        conn.commit()

# Enable Broadcast for a User
def enable_broadcast(user_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET broadcast_disabled = 0 WHERE user_id = ?
        """, (user_id,))
        conn.commit()

# Get All Users with Broadcast Disabled
def all_disabled_broadcast_users():
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id FROM users WHERE broadcast_disabled = 1
        """)
        return [{"user_id": row[0]} for row in cursor.fetchall()]

# Set a Welcome Message
def set_welcome_message(message):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM welcome_messages")
        cursor.execute("""
            INSERT INTO welcome_messages (message)
            VALUES (?)
        """, (message,))
        conn.commit()

# Get the Welcome Message
def get_welcome_message():
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT message FROM welcome_messages LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else None

# Get User Channels
def get_user_channels(user_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT chat_id, chat_name FROM user_channels WHERE user_id = ?
        """, (user_id,))
        return [{"chat_id": row[0], "chat_name": row[1]} for row in cursor.fetchall()]

# Initialize Database on First Run
initialize_database()
