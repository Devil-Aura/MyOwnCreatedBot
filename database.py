import sqlite3
from config import cfg


# Connect to the SQLite database
def connect_db():
    return sqlite3.connect(cfg.DATABASE_NAME)


# Add a new user to the database
def add_user(user_id, username):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", 
            (user_id, username)
        )
        conn.commit()


# Log user data
def log_user_data(user_id, username, log_channel):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_logs (user_id, username, log_channel) VALUES (?, ?, ?)", 
            (user_id, username, log_channel)
        )
        conn.commit()


# Check if user is banned
def is_banned(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM banned_users WHERE user_id = ?", (user_id,))
        return cursor.fetchone() is not None


# Get all users
def all_users():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        return cursor.fetchall()


# Disable broadcast for a user
def disable_broadcast_for_user(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO disabled_broadcast_users (user_id) VALUES (?)", (user_id,))
        conn.commit()


# Enable broadcast for a user
def enable_broadcast(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM disabled_broadcast_users WHERE user_id = ?", (user_id,))
        conn.commit()


# Check if broadcast is disabled for a user
def is_broadcast_disabled(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM disabled_broadcast_users WHERE user_id = ?", (user_id,))
        return cursor.fetchone() is not None


# Set welcome message
def set_welcome_message(message):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("REPLACE INTO settings (key, value) VALUES ('welcome_message', ?)", (message,))
        conn.commit()


# Get welcome message
def get_welcome_message():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'welcome_message'")
        result = cursor.fetchone()
        return result[0] if result else "Welcome to the bot!"


# Get user channels
def get_user_channels(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_channels WHERE user_id = ?", (user_id,))
        return cursor.fetchall()


# Ban a user
def ban_user(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO banned_users (user_id) VALUES (?)", (user_id,))
        conn.commit()


# Unban a user
def unban_user(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
        conn.commit()


# Get all banned users
def all_banned_users():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM banned_users")
        return cursor.fetchall()


# Get all disabled broadcast users
def all_disabled_broadcast_users():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM disabled_broadcast_users")
        return cursor.fetchall()
