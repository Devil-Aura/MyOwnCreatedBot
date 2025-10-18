import sqlite3
from pymongo import MongoClient
from os import getenv
from datetime import datetime, timedelta

# Load MongoDB URI from environment variables
MONGO_URI = getenv("MONGO_URI", "mongodb+srv://ajedvwess_db_user:pU3egnmZuEuHvWsd@cluster0.bflbyzu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# Connect to MongoDB
client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True)
db = client["Cluster0"]

# Collections
users_collection = db["users"]
channels_collection = db["channels"]
temporary_broadcasts_collection = db["temporary_broadcasts"]
user_messages_collection = db["user_messages"]

# Define DB Name for SQLite
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

    # Add to MongoDB
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id, "joined_at": datetime.now()}},
        upsert=True
    )

def remove_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def all_users():
    # Get count from MongoDB
    return users_collection.count_documents({})

#━━━━━━━━━━━━━━━━━━━━━━━ Group/Channel Management ━━━━━━━━━━━━━━━━━━━━━━━

def add_group(chat_id, user_id, chat_title, chat_url, chat_type, username=None, user_url=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO groups (chat_id) VALUES (?)", (chat_id,))
    conn.commit()
    conn.close()

    # Add to MongoDB
    channels_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {
            "user_id": user_id,
            "username": username or f"User-{user_id}",
            "user_url": user_url or f"https://t.me/{username}",
            "chat_id": chat_id,
            "chat_title": chat_title,
            "chat_url": chat_url,
            "type": chat_type,
            "added_at": datetime.now()
        }},
        upsert=True
    )

def all_groups():
    # Get count from MongoDB
    return channels_collection.count_documents({})

#━━━━━━━━━━━━━━━━━━━━━━━ Temporary Broadcast Management ━━━━━━━━━━━━━━━━━━━━━━━

def add_temporary_broadcast(message_id, delete_time):
    temporary_broadcasts_collection.insert_one({
        "message_id": message_id,
        "delete_time": delete_time,
        "created_at": datetime.now()
    })

def get_expired_broadcasts():
    now = datetime.now()
    return list(temporary_broadcasts_collection.find({"delete_time": {"$lte": now}}))

def remove_temporary_broadcast(message_id):
    temporary_broadcasts_collection.delete_one({"message_id": message_id})

#━━━━━━━━━━━━━━━━━━━━━━━ User Message Management ━━━━━━━━━━━━━━━━━━━━━━━

def store_user_message(user_id, message_id, log_message_id):
    user_messages_collection.insert_one({
        "user_id": user_id,
        "user_message_id": message_id,
        "log_message_id": log_message_id,
        "timestamp": datetime.now()
    })

def get_user_message_info(log_message_id):
    return user_messages_collection.find_one({"log_message_id": log_message_id})

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
    user_channels = channels_collection.find({})
    channels = {}

    for channel in user_channels:
        user_id = channel["user_id"]
        chat_title = channel["chat_title"]
        chat_url = channel["chat_url"]
        chat_type = channel.get("type", "unknown")
        username = channel.get("username", f"User-{user_id}")
        user_url = channel.get("user_url", f"https://t.me/{username}")

        if user_id not in channels:
            channels[user_id] = {
                "username": username,
                "user_url": user_url,
                "user_id": user_id,
                "username_tag": f"@{username}" if username else f"User-{user_id}",
                "channels": [],
                "groups": []
            }

        if chat_type == "channel":
            channels[user_id]["channels"].append({
                "chat_title": chat_title,
                "chat_url": chat_url
            })
        elif chat_type == "group":
            channels[user_id]["groups"].append({
                "chat_title": chat_title,
                "chat_url": chat_url
            })

    return channels

#━━━━━━━━━━━━━━━━━━━━━━━ Initialize Database ━━━━━━━━━━━━━━━━━━━━━━━

create_tables()
