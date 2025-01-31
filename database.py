import sqlite3

db_name = "bot_database.db"

def initialize_database():
    """Initializes the database and creates necessary tables."""
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

        conn.commit()


def add_user(user_id, username):
    """Adds a new user to the database."""
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()


def remove_user(user_id):
    """Removes a user from the database."""
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()


def all_users():
    """Returns a list of all users."""
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        return [row[0] for row in cursor.fetchall()]


def ban_user(user_id):
    """Bans a user."""
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET banned = 1 WHERE user_id = ?", (user_id,))
        conn.commit()


def unban_user(user_id):
    """Unbans a user."""
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET banned = 0 WHERE user_id = ?", (user_id,))
        conn.commit()


def is_banned(user_id):
    """Checks if a user is banned."""
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT banned FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] == 1 if result else False


def all_banned_users():
    """Returns a list of all banned users."""
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE banned = 1")
        return [row[0] for row in cursor.fetchall()]


def disable_broadcast_for_user(user_id):
    """Disables broadcast messages for a specific user."""
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET broadcast_disabled = 1 WHERE user_id = ?", (user_id,))
        conn.commit()


def enable_broadcast(user_id):
    """Enables broadcast messages for a specific user."""
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET broadcast_disabled = 0 WHERE user_id = ?", (user_id,))
        conn.commit()


def is_broadcast_disabled(user_id):
    """Checks if broadcast is disabled for a user."""
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT broadcast_disabled FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] == 1 if result else False


def add_admin(user_id):
    """Adds an admin."""
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
        conn.commit()


def all_admins():
    """Returns a list of all admins."""
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM admins")
        return [row[0] for row in cursor.fetchall()]


def is_admin(user_id):
    """Checks if a user is an admin."""
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
        return bool(cursor.fetchone())


# ✅ Initialize Database
initialize_database()
