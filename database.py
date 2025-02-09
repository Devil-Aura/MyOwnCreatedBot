import sqlite3
from pymongo import MongoClient
from os import getenv

# Load MongoDB URI from environment variables
MONGO_URI = getenv("MONGO_URI", "mongodb+srv://iamrealdevil098:M7UXF0EL3M352q0H@cluster0.257nd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["Cluster0"]  # Database name (change if needed)

# Collections
users_collection = db["users"]  # Collection for storing user data
channels_collection = db["channels"]  # Collection for storing channel/group data

# Define DB Name for SQLite
DB_NAME = "bot_database.db"  # Make sure DB_NAME is defined

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

    # Add to MongoDB
    users_collection.insert_one({"user_id": user_id})

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

def add_group(chat_id, user_id, chat_title, chat_url, chat_type):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO groups (chat_id) VALUES (?)", (chat_id,))
    conn.commit()
    conn.close()

    # Add to MongoDB
    channels_collection.insert_one({
        "user_id": user_id,
        "chat_id": chat_id,
        "chat_title": chat_title,
        "chat_url": chat_url,
        "type": chat_type  # Ensure this field is always added
    })

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
    cursor.execute("SELECT user_id FROM users")
    users_list = cursor.fetchall()
    conn.close()

    channels = {}
    for user in users_list:
        user_id = user[0]
        # Fetch user details from MongoDB
        user_data = users_collection.find_one({"user_id": user_id})
        if user_data:
            username = user_data.get("username", f"User-{user_id}")
            # Fetch channels/groups where the bot is added
            user_channels = channels_collection.find({"user_id": user_id})
            channels[user_id] = {"username": username, "channels": [], "groups": []}
            for channel in user_channels:
                if "type" in channel:  # Check if the 'type' key exists
                    if channel["type"] == "channel":
                        channels[user_id]["channels"].append({
                            "chat_title": channel["chat_title"],
                            "chat_url": channel["chat_url"],
                            "type": "channel"
                        })
                    elif channel["type"] == "group":
                        channels[user_id]["groups"].append({
                            "chat_title": channel["chat_title"],
                            "chat_url": channel["chat_url"],
                            "type": "group"
                        })
    
    return channels

#━━━━━━━━━━━━━━━━━━━━━━━ Initialize Database ━━━━━━━━━━━━━━━━━━━━━━━

create_tables()
